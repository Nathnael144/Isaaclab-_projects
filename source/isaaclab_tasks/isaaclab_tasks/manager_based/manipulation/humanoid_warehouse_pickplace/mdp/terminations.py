# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Termination conditions for fixed-base humanoid warehouse pick-and-place task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def object_placed_on_goal(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    xy_threshold: float = 0.12,
    z_range: tuple = (0.70, 0.90),
    speed_threshold: float = 0.15,
) -> torch.Tensor:
    """Success: object is at goal position, correct height, and nearly stationary."""
    obj = env.scene[object_cfg.name]
    goal = env.scene[goal_cfg.name]
    obj_pos = obj.data.root_pos_w
    goal_pos = goal.data.root_pos_w
    xy_dist = torch.norm(obj_pos[:, :2] - goal_pos[:, :2], dim=-1)
    z_ok = (obj_pos[:, 2] > z_range[0]) & (obj_pos[:, 2] < z_range[1])
    speed = torch.norm(obj.data.root_lin_vel_w, dim=-1)
    return (xy_dist < xy_threshold) & z_ok & (speed < speed_threshold)


def object_dropped(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    min_height: float = -0.1,
) -> torch.Tensor:
    """Object fell below the floor."""
    obj = env.scene[object_cfg.name]
    return obj.data.root_pos_w[:, 2] < min_height
