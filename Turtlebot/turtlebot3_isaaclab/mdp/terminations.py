# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Custom termination terms for TurtleBot3 navigation tasks."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def goal_reached(
    env: ManagerBasedRLEnv,
    threshold: float = 0.25,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Terminate when the robot is within *threshold* metres of the goal."""
    asset = env.scene[asset_cfg.name]
    if hasattr(env, goal_pos_key) and isinstance(getattr(env, goal_pos_key), torch.Tensor):
        goal_w = getattr(env, goal_pos_key)
    elif hasattr(env, "command_manager") and goal_pos_key in env.command_manager.active_terms:
        goal_w = env.command_manager.get_command(goal_pos_key)[:, :2]
    else:
        goal_w = env.scene.env_origins[:, :2] + torch.tensor([[2.0, 0.0]], device=env.device)

    dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)
    return dist < threshold


def robot_flipped(
    env: ManagerBasedRLEnv,
    limit_angle: float = 0.8,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Terminate if the robot tilts beyond *limit_angle* rad from upright."""
    asset = env.scene[asset_cfg.name]
    # projected gravity in body frame — if z-component is small the robot is flipped
    quat = asset.data.root_quat_w  # (N, 4)
    # Compute the z-component of the world gravity expressed in body frame
    # For a flat robot, projected_gz ≈ -1 when upright
    gx = 2.0 * (quat[:, 1] * quat[:, 3] - quat[:, 0] * quat[:, 2])
    gy = 2.0 * (quat[:, 2] * quat[:, 3] + quat[:, 0] * quat[:, 1])
    gz = 1.0 - 2.0 * (quat[:, 1] ** 2 + quat[:, 2] ** 2)
    # Tilt angle from vertical
    tilt = torch.acos(gz.clamp(-1.0, 1.0))
    return tilt > limit_angle


def collision_with_obstacle(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("contact_sensor"),
    threshold: float = 0.5,
) -> torch.Tensor:
    """Terminate (and reset) when the robot hits an obstacle.

    Mirrors the DQN behaviour: collision gives -200 and the episode ends
    immediately so the robot restarts at a new position.
    """
    sensor = env.scene[sensor_cfg.name]
    net_force = torch.norm(sensor.data.net_forces_w[:, :, :], dim=-1)  # (N, B)
    max_force = net_force.max(dim=-1).values  # (N,)
    return max_force > threshold


def out_of_bounds(
    env: ManagerBasedRLEnv,
    x_bounds: tuple[float, float] = (-10.0, 10.0),
    y_bounds: tuple[float, float] = (-10.0, 10.0),
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Terminate if the robot leaves the arena (relative to env origin)."""
    asset = env.scene[asset_cfg.name]
    pos = asset.data.root_pos_w[:, :2] - env.scene.env_origins[:, :2]
    oob_x = (pos[:, 0] < x_bounds[0]) | (pos[:, 0] > x_bounds[1])
    oob_y = (pos[:, 1] < y_bounds[0]) | (pos[:, 1] > y_bounds[1])
    return oob_x | oob_y
