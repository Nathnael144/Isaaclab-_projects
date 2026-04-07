# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shaped rewards for RL training on pick-place style mimic tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_right_eef_distance_exp(
    env: ManagerBasedRLEnv,
    eef_link_name: str,
    std: float = 0.12,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """Shaped reward in (0, 1]: closer right eef to object root -> higher."""
    obj: RigidObject = env.scene[object_cfg.name]
    object_pos = obj.data.root_pos_w - env.scene.env_origins
    body_pos_w = env.scene["robot"].data.body_pos_w
    idx = env.scene["robot"].data.body_names.index(eef_link_name)
    eef_pos = body_pos_w[:, idx] - env.scene.env_origins
    err = torch.sum(torch.square(object_pos - eef_pos), dim=1)
    return torch.exp(-err / (std**2))


def pick_place_success_reward(
    env: ManagerBasedRLEnv,
    task_link_name: str,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
    right_wrist_max_x: float = 0.26,
    min_x: float = 0.40,
    max_x: float = 0.85,
    min_y: float = 0.35,
    max_y: float = 0.60,
    max_height: float = 1.10,
    min_vel: float = 0.20,
) -> torch.Tensor:
    """Sparse success signal (0 or 1) using the same predicate as pick-place termination."""
    from .terminations import task_done_pick_place

    return task_done_pick_place(
        env,
        task_link_name,
        object_cfg,
        right_wrist_max_x,
        min_x,
        max_x,
        min_y,
        max_y,
        max_height,
        min_vel,
    ).float()


def object_in_target_xy_exp(
    env: ManagerBasedRLEnv,
    target_xy: tuple[float, float],
    std: float = 0.20,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """Dense reward for moving the object toward a target XY point (world frame, env-relative)."""
    obj: RigidObject = env.scene[object_cfg.name]
    pos = obj.data.root_pos_w - env.scene.env_origins
    dx = pos[:, 0] - target_xy[0]
    dy = pos[:, 1] - target_xy[1]
    err = dx * dx + dy * dy
    return torch.exp(-err / (std**2))


def object_speed_exp(
    env: ManagerBasedRLEnv,
    std: float = 0.25,
    object_cfg: SceneEntityCfg = SceneEntityCfg("object"),
) -> torch.Tensor:
    """Dense reward for making the object move slowly (uses root linear velocity magnitude)."""
    obj: RigidObject = env.scene[object_cfg.name]
    v = obj.data.root_vel_w[:, :3]
    speed2 = torch.sum(torch.square(v), dim=1)
    return torch.exp(-speed2 / (std**2))


def wrist_retract_exp(
    env: ManagerBasedRLEnv,
    link_name: str,
    target_max_x: float = 0.26,
    std: float = 0.10,
) -> torch.Tensor:
    """Dense reward for retracting the wrist back toward the body (x below target_max_x)."""
    body_pos_w = env.scene["robot"].data.body_pos_w
    idx = env.scene["robot"].data.body_names.index(link_name)
    wrist_x = body_pos_w[:, idx, 0] - env.scene.env_origins[:, 0]
    # reward ~1 when wrist_x << target_max_x, decays as it exceeds target_max_x
    err = torch.clamp(wrist_x - target_max_x, min=0.0)
    return torch.exp(-(err * err) / (std**2))


def nut_pour_shaping_reward(
    env: ManagerBasedRLEnv,
    std_nut_bowl: float = 0.04,
    std_bowl_scale: float = 0.06,
    std_beaker_bin: float = 0.08,
    sorting_scale_cfg: SceneEntityCfg = SceneEntityCfg("sorting_scale"),
    sorting_bowl_cfg: SceneEntityCfg = SceneEntityCfg("sorting_bowl"),
    sorting_beaker_cfg: SceneEntityCfg = SceneEntityCfg("sorting_beaker"),
    factory_nut_cfg: SceneEntityCfg = SceneEntityCfg("factory_nut"),
    sorting_bin_cfg: SceneEntityCfg = SceneEntityCfg("black_sorting_bin"),
) -> torch.Tensor:
    """Soft progress toward nut-pour success (sum of exponential distance kernels)."""
    sorting_scale: RigidObject = env.scene[sorting_scale_cfg.name]
    sorting_bowl: RigidObject = env.scene[sorting_bowl_cfg.name]
    factory_nut: RigidObject = env.scene[factory_nut_cfg.name]
    sorting_beaker: RigidObject = env.scene[sorting_beaker_cfg.name]
    sorting_bin: RigidObject = env.scene[sorting_bin_cfg.name]

    origins = env.scene.env_origins
    scale_pos = sorting_scale.data.root_pos_w - origins
    bowl_pos = sorting_bowl.data.root_pos_w - origins
    nut_pos = factory_nut.data.root_pos_w - origins
    beaker_pos = sorting_beaker.data.root_pos_w - origins
    bin_pos = sorting_bin.data.root_pos_w - origins

    nut_bowl_xy = torch.sum(torch.square(nut_pos[:, :2] - bowl_pos[:, :2]), dim=1)
    r_nut = torch.exp(-nut_bowl_xy / (std_nut_bowl**2))

    bowl_scale_xy = torch.sum(torch.square(bowl_pos[:, :2] - scale_pos[:, :2]), dim=1)
    bowl_scale_z = torch.square(bowl_pos[:, 2] - scale_pos[:, 2])
    r_bowl = torch.exp(-(bowl_scale_xy + bowl_scale_z) / (std_bowl_scale**2))

    beaker_bin_xy = torch.sum(torch.square(beaker_pos[:, :2] - bin_pos[:, :2]), dim=1)
    beaker_bin_z = torch.square(beaker_pos[:, 2] - bin_pos[:, 2])
    r_beaker = torch.exp(-(beaker_bin_xy + beaker_bin_z) / (std_beaker_bin**2))

    return (r_nut + r_bowl + r_beaker) / 3.0


def nut_pour_success_reward(
    env: ManagerBasedRLEnv,
    sorting_scale_cfg: SceneEntityCfg = SceneEntityCfg("sorting_scale"),
    sorting_bowl_cfg: SceneEntityCfg = SceneEntityCfg("sorting_bowl"),
    sorting_beaker_cfg: SceneEntityCfg = SceneEntityCfg("sorting_beaker"),
    factory_nut_cfg: SceneEntityCfg = SceneEntityCfg("factory_nut"),
    sorting_bin_cfg: SceneEntityCfg = SceneEntityCfg("black_sorting_bin"),
    max_bowl_to_scale_x: float = 0.055,
    max_bowl_to_scale_y: float = 0.055,
    max_bowl_to_scale_z: float = 0.025,
    max_nut_to_bowl_x: float = 0.050,
    max_nut_to_bowl_y: float = 0.050,
    max_nut_to_bowl_z: float = 0.019,
    max_beaker_to_bin_x: float = 0.08,
    max_beaker_to_bin_y: float = 0.12,
    max_beaker_to_bin_z: float = 0.07,
) -> torch.Tensor:
    from .terminations import task_done_nut_pour

    return task_done_nut_pour(
        env,
        sorting_scale_cfg,
        sorting_bowl_cfg,
        sorting_beaker_cfg,
        factory_nut_cfg,
        sorting_bin_cfg,
        max_bowl_to_scale_x,
        max_bowl_to_scale_y,
        max_bowl_to_scale_z,
        max_nut_to_bowl_x,
        max_nut_to_bowl_y,
        max_nut_to_bowl_z,
        max_beaker_to_bin_x,
        max_beaker_to_bin_y,
        max_beaker_to_bin_z,
    ).float()


def exhaust_pipe_shaping_reward(
    env: ManagerBasedRLEnv,
    std: float = 0.12,
    blue_exhaust_pipe_cfg: SceneEntityCfg = SceneEntityCfg("blue_exhaust_pipe"),
    blue_sorting_bin_cfg: SceneEntityCfg = SceneEntityCfg("blue_sorting_bin"),
) -> torch.Tensor:
    """Soft progress: pipe close to bin (exponential kernel on xyz error)."""
    pipe: RigidObject = env.scene[blue_exhaust_pipe_cfg.name]
    bin_obj: RigidObject = env.scene[blue_sorting_bin_cfg.name]
    origins = env.scene.env_origins
    p = pipe.data.root_pos_w - origins
    b = bin_obj.data.root_pos_w - origins
    err = torch.sum(torch.square(p - b), dim=1)
    return torch.exp(-err / (std**2))


def exhaust_pipe_success_reward(
    env: ManagerBasedRLEnv,
    blue_exhaust_pipe_cfg: SceneEntityCfg = SceneEntityCfg("blue_exhaust_pipe"),
    blue_sorting_bin_cfg: SceneEntityCfg = SceneEntityCfg("blue_sorting_bin"),
    max_blue_exhaust_to_bin_x: float = 0.085,
    max_blue_exhaust_to_bin_y: float = 0.200,
    min_blue_exhaust_to_bin_y: float = -0.090,
    max_blue_exhaust_to_bin_z: float = 0.070,
) -> torch.Tensor:
    from .terminations import task_done_exhaust_pipe

    return task_done_exhaust_pipe(
        env,
        blue_exhaust_pipe_cfg,
        blue_sorting_bin_cfg,
        max_blue_exhaust_to_bin_x,
        max_blue_exhaust_to_bin_y,
        min_blue_exhaust_to_bin_y,
        max_blue_exhaust_to_bin_z,
    ).float()
