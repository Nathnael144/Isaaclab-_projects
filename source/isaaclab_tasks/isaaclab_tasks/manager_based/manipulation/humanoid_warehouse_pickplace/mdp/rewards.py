# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Reward functions for fixed-base humanoid warehouse pick-and-place task.

Grasping logic inspired by the hands.py demo which uses soft_joint_pos_limits
to toggle hand open/close states and rewards based on contact forces.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg, EventTermCfg, ManagerTermBase

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


# ------------------------------------------------------------------
# Reach rewards
# ------------------------------------------------------------------


def hand_to_object_distance_tanh(
    env: "ManagerBasedRLEnv",
    robot_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    hand_body_name: str,
    std: float,
) -> torch.Tensor:
    """Shaped reach reward: hand → object distance with tanh kernel."""
    robot: Articulation = env.scene[robot_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]
    body_idx, _ = robot.find_bodies(hand_body_name)
    if isinstance(body_idx, (list, tuple)):
        body_idx = body_idx[0]
    hand_pos = robot.data.body_pos_w[:, body_idx]
    obj_pos = obj.data.root_pos_w
    dist = torch.norm(hand_pos - obj_pos, dim=-1)
    return 1.0 - torch.tanh(dist / std)


def hand_above_object(
    env: "ManagerBasedRLEnv",
    robot_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    hand_body_name: str,
    height_offset: float = 0.15,
    std: float = 0.1,
) -> torch.Tensor:
    """Reward for positioning hand above the object (pre-grasp)."""
    robot: Articulation = env.scene[robot_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]
    body_idx, _ = robot.find_bodies(hand_body_name)
    if isinstance(body_idx, (list, tuple)):
        body_idx = body_idx[0]
    hand_pos = robot.data.body_pos_w[:, body_idx]
    obj_pos = obj.data.root_pos_w
    xy_dist = torch.norm(hand_pos[:, :2] - obj_pos[:, :2], dim=-1)
    z_err = torch.abs(hand_pos[:, 2] - (obj_pos[:, 2] + height_offset))
    total_err = xy_dist + z_err
    return 1.0 - torch.tanh(total_err / std)


# ------------------------------------------------------------------
# Grasp rewards (inspired by hands.py contact + limits toggling)
# ------------------------------------------------------------------


def contact_force_reward(
    env: "ManagerBasedRLEnv",
    sensor_cfg: SceneEntityCfg,
    min_force: float = 1.0,
    max_force: float = 50.0,
) -> torch.Tensor:
    """Reward for maintaining contact force in the ideal grasping range.

    Returns 1.0 when force is in [min_force, max_force], scaled otherwise.
    This is inspired by the hands.py approach of toggling between open/close
    states – here we reward the force that results from closing fingers on the box.
    """
    sensor = env.scene[sensor_cfg.name]
    f = torch.norm(sensor.data.net_forces_w, dim=-1)
    if f.ndim > 1:
        f = f.squeeze(-1)
    # Normalize: 0 when no contact, ramps to 1 at min_force, stays ~1 in range, drops above max
    in_range = ((f >= min_force) & (f <= max_force)).to(dtype=torch.float32)
    below = (f < min_force).to(dtype=torch.float32) * (f / max(min_force, 1e-6))
    above = (f > max_force).to(dtype=torch.float32) * torch.clamp(1.0 - (f - max_force) / max_force, 0.0, 1.0)
    return in_range + below + above


def finger_close_near_object(
    env: "ManagerBasedRLEnv",
    robot_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    hand_body_name: str,
    finger_joint_names: list[str],
    proximity_threshold: float = 0.15,
) -> torch.Tensor:
    """Reward finger closure when the hand is near the object.

    From hands.py: grasping is achieved by commanding fingers to their
    soft_joint_pos_limits upper bound. Here we reward how close finger joints
    are to their upper limits when the hand is near the box.
    """
    robot: Articulation = env.scene[robot_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]

    # Hand proximity check
    body_idx, _ = robot.find_bodies(hand_body_name)
    if isinstance(body_idx, (list, tuple)):
        body_idx = body_idx[0]
    hand_pos = robot.data.body_pos_w[:, body_idx]
    obj_pos = obj.data.root_pos_w
    dist = torch.norm(hand_pos - obj_pos, dim=-1)
    near_mask = (dist < proximity_threshold).to(dtype=torch.float32)

    # Find finger joint indices
    all_joint_names = robot.data.joint_names
    finger_ids = []
    for pattern in finger_joint_names:
        for j, name in enumerate(all_joint_names):
            if re.match(pattern, name):
                finger_ids.append(j)

    if len(finger_ids) == 0:
        return torch.zeros(env.num_envs, device=env.device)

    finger_ids_t = torch.tensor(finger_ids, device=env.device, dtype=torch.long)

    # How close fingers are to their upper limit (closed position)
    joint_pos = robot.data.joint_pos[:, finger_ids_t]
    upper_limits = robot.data.soft_joint_pos_limits[0, finger_ids_t, 1]
    lower_limits = robot.data.soft_joint_pos_limits[0, finger_ids_t, 0]
    joint_range = upper_limits - lower_limits
    joint_range = torch.clamp(joint_range, min=1e-6)

    # Normalized closure: 0 = open (lower limit), 1 = closed (upper limit)
    closure = (joint_pos - lower_limits) / joint_range
    closure = torch.clamp(closure, 0.0, 1.0)
    mean_closure = closure.mean(dim=-1)

    return near_mask * mean_closure


def contact_force_tanh(
    env: "ManagerBasedRLEnv",
    sensor_cfg: SceneEntityCfg,
    std: float,
) -> torch.Tensor:
    """Shaped reward for contact force magnitude with tanh kernel."""
    sensor = env.scene[sensor_cfg.name]
    f = torch.norm(sensor.data.net_forces_w, dim=-1)
    if f.ndim > 1:
        f = f.squeeze(-1)
    return 1.0 - torch.tanh(f / std)


# ------------------------------------------------------------------
# Lift rewards
# ------------------------------------------------------------------


def object_lifted_reward(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    min_height: float,
) -> torch.Tensor:
    """Binary reward: 1.0 if object is above min_height, else 0.0."""
    obj: RigidObject = env.scene[object_cfg.name]
    return (obj.data.root_pos_w[:, 2] > min_height).to(dtype=torch.float32)


# ------------------------------------------------------------------
# Place rewards
# ------------------------------------------------------------------


def object_to_goal_distance_tanh(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    std: float,
) -> torch.Tensor:
    """Shaped distance reward: object → goal in (0, 1]."""
    obj_pos = env.scene[object_cfg.name].data.root_pos_w
    goal_pos = env.scene[goal_cfg.name].data.root_pos_w
    dist = torch.norm(obj_pos - goal_pos, dim=-1)
    return 1.0 - torch.tanh(dist / std)


def object_near_goal_and_slow(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    dist_thresh: float,
    speed_thresh: float,
) -> torch.Tensor:
    """Dense place reward: 1 if near goal and slow (stable placement)."""
    obj = env.scene[object_cfg.name]
    goal = env.scene[goal_cfg.name]
    dist = torch.norm(obj.data.root_pos_w - goal.data.root_pos_w, dim=-1)
    speed = torch.norm(obj.data.root_lin_vel_w, dim=-1)
    return ((dist < dist_thresh) & (speed < speed_thresh)).to(dtype=torch.float32)


def object_on_target_table(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    xy_thresh: float = 0.30,
    z_range: tuple = (0.70, 0.90),
) -> torch.Tensor:
    """Reward for object being on the target table area."""
    obj_pos = env.scene[object_cfg.name].data.root_pos_w
    goal_pos = env.scene[goal_cfg.name].data.root_pos_w
    xy_dist = torch.norm(obj_pos[:, :2] - goal_pos[:, :2], dim=-1)
    z_ok = (obj_pos[:, 2] > z_range[0]) & (obj_pos[:, 2] < z_range[1])
    xy_ok = xy_dist < xy_thresh
    return (xy_ok & z_ok).to(dtype=torch.float32)


# ------------------------------------------------------------------
# Regularization
# ------------------------------------------------------------------


def object_speed_l2(env: "ManagerBasedRLEnv", object_cfg: SceneEntityCfg) -> torch.Tensor:
    """Penalty on object root linear speed squared."""
    obj = env.scene[object_cfg.name]
    v = obj.data.root_lin_vel_w
    return torch.sum(v * v, dim=-1)


# ------------------------------------------------------------------
# Stateful penalties
# ------------------------------------------------------------------


class DropPenaltyAfterContact(ManagerTermBase):
    """Penalty when object drops after any contact has occurred in the episode."""

    def __init__(self, cfg: EventTermCfg, env):
        super().__init__(cfg, env)
        self.box_cfg: SceneEntityCfg = cfg.params["object_cfg"]
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
        object_cfg: SceneEntityCfg,
        sensor_cfgs: list[SceneEntityCfg],
        contact_force_threshold: float = 2.0,
        drop_height_threshold: float = 0.08,
    ) -> torch.Tensor:
        in_contact = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        for scfg in sensor_cfgs:
            sensor = env.scene[scfg.name]
            f = torch.norm(sensor.data.net_forces_w, dim=-1)
            if f.ndim > 1:
                f = f.squeeze(-1)
            in_contact = in_contact | (f > float(contact_force_threshold))
        self._ever_contact = self._ever_contact | in_contact
        obj = env.scene[object_cfg.name]
        dropped = obj.data.root_pos_w[:, 2] < float(drop_height_threshold)
        return (self._ever_contact & dropped).to(dtype=torch.float32)
