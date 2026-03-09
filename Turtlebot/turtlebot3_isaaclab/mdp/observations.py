# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Custom observation terms for TurtleBot3 navigation tasks."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg
from isaaclab.utils.math import wrap_to_pi

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


# ---------------------------------------------------------------------------
# Robot-state observations
# ---------------------------------------------------------------------------


def base_yaw(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Returns the robot's yaw angle wrapped to [-pi, pi].  Shape: (N, 1)."""
    asset = env.scene[asset_cfg.name]
    quat = asset.data.root_quat_w  # (N, 4)  — (w, x, y, z)
    # Extract yaw from quaternion
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)
    return yaw.unsqueeze(-1)  # (N, 1)


def base_position_xy(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Returns the robot's (x, y) position in the world frame.  Shape: (N, 2)."""
    asset = env.scene[asset_cfg.name]
    return asset.data.root_pos_w[:, :2]  # (N, 2)


def base_linear_velocity_xy(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Returns the robot's linear velocity in body frame (x, y only).  Shape: (N, 2)."""
    asset = env.scene[asset_cfg.name]
    return asset.data.root_lin_vel_b[:, :2]  # (N, 2)


def base_angular_velocity_z(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")) -> torch.Tensor:
    """Returns the robot's angular velocity about Z in body frame.  Shape: (N, 1)."""
    asset = env.scene[asset_cfg.name]
    return asset.data.root_ang_vel_b[:, 2:3]  # (N, 1)


# ---------------------------------------------------------------------------
# Goal-relative observations
# ---------------------------------------------------------------------------


def goal_position_in_robot_frame(
    env: ManagerBasedRLEnv,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Returns the goal (x, y) expressed in the robot's body frame.  Shape: (N, 2).

    Expects ``env.scene.env_origins`` + a ``goal_pos`` attribute on env or scene.
    Falls back to the command manager if ``goal_pos_key`` is registered there.
    """
    asset = env.scene[asset_cfg.name]
    # Try getting goal from env attribute or command manager
    if hasattr(env, goal_pos_key) and isinstance(getattr(env, goal_pos_key), torch.Tensor):
        goal_w = getattr(env, goal_pos_key)  # (N, 2) or (N, 3)
    elif hasattr(env, "command_manager") and goal_pos_key in env.command_manager.active_terms:
        cmd = env.command_manager.get_command(goal_pos_key)
        goal_w = cmd[:, :2]
    else:
        # Default: origin-relative goal at (2, 0)
        goal_w = env.scene.env_origins[:, :2] + torch.tensor([[2.0, 0.0]], device=env.device)

    robot_xy = asset.data.root_pos_w[:, :2]
    diff = goal_w[:, :2] - robot_xy  # (N, 2) world frame delta

    # Rotate into robot frame
    quat = asset.data.root_quat_w
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)  # (N,)

    cos_yaw = torch.cos(-yaw)
    sin_yaw = torch.sin(-yaw)
    goal_body_x = diff[:, 0] * cos_yaw - diff[:, 1] * sin_yaw
    goal_body_y = diff[:, 0] * sin_yaw + diff[:, 1] * cos_yaw
    return torch.stack([goal_body_x, goal_body_y], dim=-1)  # (N, 2)


def lidar_scan(env: ManagerBasedRLEnv, sensor_cfg: SceneEntityCfg = SceneEntityCfg("lidar")) -> torch.Tensor:
    """Returns 1-D lidar range readings from a RayCaster sensor.  Shape: (N, num_rays).

    The output is the Euclidean distance per ray, clipped to [0, max_distance].
    """
    sensor = env.scene[sensor_cfg.name]
    # ray_hits_w is (N, num_rays, 3) — the world hit positions
    # For invalid (miss) hits, distance == max_distance
    hits = sensor.data.ray_hits_w  # (N, num_rays, 3)
    origin = sensor.data.pos_w.unsqueeze(1)  # (N, 1, 3)
    distances = torch.norm(hits - origin, dim=-1)  # (N, num_rays)
    return distances


# ---------------------------------------------------------------------------
# DQN-inspired compact state observations
# ---------------------------------------------------------------------------


def heading_to_goal(
    env: ManagerBasedRLEnv,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Signed angle from the robot's heading to the goal direction, in [-pi, pi].  Shape: (N, 1).

    Matches the DQN 'heading' state feature: positive when goal is to the left.
    """
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    robot_xy = asset.data.root_pos_w[:, :2]
    diff = goal_w[:, :2] - robot_xy  # (N, 2) world frame

    angle_to_goal = torch.atan2(diff[:, 1], diff[:, 0])  # (N,)

    # Robot yaw from quaternion
    quat = asset.data.root_quat_w
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)

    heading_err = wrap_to_pi(angle_to_goal - yaw)
    return heading_err.unsqueeze(-1)  # (N, 1)


def distance_to_goal(
    env: ManagerBasedRLEnv,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Euclidean distance to the goal.  Shape: (N, 1).

    Matches the DQN 'current_distance' state feature.
    """
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)
    return dist.unsqueeze(-1)  # (N, 1)


def obstacle_min_range(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("lidar"),
    max_distance: float = 3.5,
) -> torch.Tensor:
    """Minimum LiDAR range — distance to the closest obstacle.  Shape: (N, 1).

    Matches the DQN 'obstacle_min_range' state feature.
    """
    sensor = env.scene[sensor_cfg.name]
    hits = sensor.data.ray_hits_w  # (N, R, 3)
    origin = sensor.data.pos_w.unsqueeze(1)  # (N, 1, 3)
    distances = torch.norm(hits - origin, dim=-1)  # (N, R)
    min_dist = distances.min(dim=-1).values.clamp(max=max_distance)
    return min_dist.unsqueeze(-1)  # (N, 1)


def obstacle_angle(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("lidar"),
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Bearing toward the closest obstacle in the robot frame, in [-pi, pi].  Shape: (N, 1).

    Matches the DQN 'obstacle_angle' state feature.
    """
    sensor = env.scene[sensor_cfg.name]
    asset = env.scene[asset_cfg.name]

    hits = sensor.data.ray_hits_w  # (N, R, 3)
    origin = sensor.data.pos_w     # (N, 3)

    distances = torch.norm(hits - origin.unsqueeze(1), dim=-1)  # (N, R)
    min_idx = distances.argmin(dim=-1)  # (N,)

    # World-frame (x, y) of the closest hit
    n = hits.shape[0]
    closest_hit_xy = hits[torch.arange(n, device=hits.device), min_idx, :2]  # (N, 2)
    diff_world = closest_hit_xy - origin[:, :2]  # (N, 2)
    angle_world = torch.atan2(diff_world[:, 1], diff_world[:, 0])  # (N,)

    # Robot yaw
    quat = asset.data.root_quat_w
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)

    angle_body = wrap_to_pi(angle_world - yaw)
    return angle_body.unsqueeze(-1)  # (N, 1)


# ---------------------------------------------------------------------------
# Internal helper (mirrors the reward helper without the fallback import)
# ---------------------------------------------------------------------------


def _resolve_goal(env: ManagerBasedRLEnv, key: str) -> torch.Tensor:
    """Return goal position (N, 2+) from env attribute or command manager."""
    if hasattr(env, key) and isinstance(getattr(env, key), torch.Tensor):
        return getattr(env, key)
    if hasattr(env, "command_manager") and key in env.command_manager.active_terms:
        return env.command_manager.get_command(key)[:, :2]
    return env.scene.env_origins[:, :2] + torch.tensor([[2.0, 0.0]], device=env.device)
