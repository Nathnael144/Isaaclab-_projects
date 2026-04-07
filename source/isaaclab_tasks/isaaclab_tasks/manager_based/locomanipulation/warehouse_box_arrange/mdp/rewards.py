# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import EventTermCfg, ManagerTermBase


def object_to_goal_distance_l2(env, object_cfg: SceneEntityCfg, goal_cfg: SceneEntityCfg) -> torch.Tensor:
    """Euclidean distance between box root and goal marker root in world frame."""
    obj_pos = env.scene[object_cfg.name].data.root_pos_w
    goal_pos = env.scene[goal_cfg.name].data.root_pos_w
    return torch.norm(obj_pos - goal_pos, dim=-1)


def object_to_goal_distance_tanh(
    env,
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    std: float,
) -> torch.Tensor:
    """Shaped distance reward in (0, 1]."""
    dist = object_to_goal_distance_l2(env, object_cfg, goal_cfg)
    return 1.0 - torch.tanh(dist / std)


def hand_to_object_distance_tanh(
    env,
    robot_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    hand_body_name: str,
    std: float,
) -> torch.Tensor:
    """Shaped reach reward based on hand-body to object distance."""
    robot = env.scene[robot_cfg.name]
    obj = env.scene[object_cfg.name]
    body_idx, _ = robot.find_bodies(hand_body_name)
    if isinstance(body_idx, (list, tuple)):
        body_idx = body_idx[0]
    hand_pos = robot.data.body_pos_w[:, body_idx]
    obj_pos = obj.data.root_pos_w
    dist = torch.norm(hand_pos - obj_pos, dim=-1)
    return 1.0 - torch.tanh(dist / std)


def object_height_above_min(
    env,
    object_cfg: SceneEntityCfg,
    min_height: float,
) -> torch.Tensor:
    """Reward 1.0 if object root is above a height threshold else 0."""
    obj = env.scene[object_cfg.name]
    return (obj.data.root_pos_w[:, 2] > min_height).to(dtype=torch.float32)


def object_speed_l2(env, object_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalty on object root linear speed squared."""
    obj = env.scene[object_cfg.name]
    v = obj.data.root_lin_vel_w
    return torch.sum(v * v, dim=-1)


def object_angular_speed_l2(env, object_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalty on object root angular speed squared."""
    obj = env.scene[object_cfg.name]
    w = obj.data.root_ang_vel_w
    return torch.sum(w * w, dim=-1)


def object_near_goal_and_slow(env, object_cfg: SceneEntityCfg, goal_cfg: SceneEntityCfg, dist_thresh: float, speed_thresh: float):
    """Dense place reward: 1 if near goal and slow."""
    obj = env.scene[object_cfg.name]
    goal = env.scene[goal_cfg.name]
    dist = torch.norm(obj.data.root_pos_w - goal.data.root_pos_w, dim=-1)
    speed = torch.norm(obj.data.root_lin_vel_w, dim=-1)
    return ((dist < dist_thresh) & (speed < speed_thresh)).to(dtype=torch.float32)


def contact_force_tanh(env, sensor_cfg: SceneEntityCfg, std: float) -> torch.Tensor:
    """Shaped reward for palm↔box contact force magnitude."""
    sensor = env.scene[sensor_cfg.name]
    # net_forces_w: (num_envs, 3)
    f = torch.norm(sensor.data.net_forces_w, dim=-1)
    # If sensor has history dimension, squeeze it out (expect history_length=1 here).
    if f.ndim > 1:
        f = f.squeeze(-1)
    return 1.0 - torch.tanh(f / std)


class DropPenaltyAfterContact(ManagerTermBase):
    """Penalty when the box drops after any finger/palm contact has happened in the episode."""

    def __init__(self, cfg: EventTermCfg, env):
        super().__init__(cfg, env)
        self.box_cfg: SceneEntityCfg = cfg.params["box_cfg"]
        self.sensor_cfgs: list[SceneEntityCfg] = cfg.params["sensor_cfgs"]
        self.contact_force_threshold: float = float(cfg.params.get("contact_force_threshold", 2.0))
        self.drop_height_threshold: float = float(cfg.params.get("drop_height_threshold", 0.08))
        self._ever_contact = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)

    def reset(self, env_ids: torch.Tensor | None = None):
        if env_ids is None:
            self._ever_contact[:] = False
        else:
            self._ever_contact[env_ids] = False

    def __call__(
        self,
        env,
        box_cfg: SceneEntityCfg,
        sensor_cfgs: list[SceneEntityCfg],
        contact_force_threshold: float = 2.0,
        drop_height_threshold: float = 0.08,
    ) -> torch.Tensor:
        # update thresholds (allow cfg override)
        self.contact_force_threshold = float(contact_force_threshold)
        self.drop_height_threshold = float(drop_height_threshold)

        # detect contact this step (any sensor)
        in_contact = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        for scfg in sensor_cfgs:
            sensor = env.scene[scfg.name]
            f = torch.norm(sensor.data.net_forces_w, dim=-1)
            if f.ndim > 1:
                f = f.squeeze(-1)
            in_contact = in_contact | (f > self.contact_force_threshold)

        self._ever_contact = self._ever_contact | in_contact

        # drop check
        box = env.scene[box_cfg.name]
        dropped = box.data.root_pos_w[:, 2] < self.drop_height_threshold
        penalty = (self._ever_contact & dropped).to(dtype=torch.float32)
        # return positive mask; will be weighted negatively in RewardTermCfg
        return penalty

