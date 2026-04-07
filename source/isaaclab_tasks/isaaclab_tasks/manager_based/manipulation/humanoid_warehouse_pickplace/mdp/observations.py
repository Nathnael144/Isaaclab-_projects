# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Observation helpers for fixed-base humanoid warehouse pick-and-place task."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def eef_pos_w(env: "ManagerBasedRLEnv", asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """End-effector position in world frame. Shape: (N, 3)."""
    robot: Articulation = env.scene[asset_cfg.name]
    return robot.data.body_pos_w[:, asset_cfg.body_ids[0]]


def eef_quat_w(env: "ManagerBasedRLEnv", asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """End-effector orientation (quaternion wxyz) in world frame. Shape: (N, 4)."""
    robot: Articulation = env.scene[asset_cfg.name]
    return robot.data.body_quat_w[:, asset_cfg.body_ids[0]]


def eef_to_object_vec(
    env: "ManagerBasedRLEnv",
    eef_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Vector from end-effector to object root. Shape: (N, 3)."""
    robot: Articulation = env.scene[eef_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]
    eef_pos = robot.data.body_pos_w[:, eef_cfg.body_ids[0]]
    obj_pos = obj.data.root_pos_w
    return obj_pos - eef_pos


def object_to_goal_vec(
    env: "ManagerBasedRLEnv",
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Vector from object to goal. Shape: (N, 3)."""
    obj_pos = env.scene[object_cfg.name].data.root_pos_w
    goal_pos = env.scene[goal_cfg.name].data.root_pos_w
    return goal_pos - obj_pos


def contact_force_obs(
    env: "ManagerBasedRLEnv",
    sensor_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Contact force magnitude on the hand sensor. Shape: (N, 1).

    Provides the policy with information about whether it is currently
    gripping the object, inspired by the hands.py demo where contact
    force is the key signal for successful grasping.
    """
    sensor = env.scene[sensor_cfg.name]
    f = torch.norm(sensor.data.net_forces_w, dim=-1)
    if f.ndim > 1:
        f = f.squeeze(-1)
    # Normalize to reasonable range and return as (N, 1) observation
    return (f / 50.0).unsqueeze(-1)
