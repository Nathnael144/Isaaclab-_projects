# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Custom reward terms for TurtleBot3 navigation tasks."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


# ---------------------------------------------------------------------------
# Goal-reaching rewards
# ---------------------------------------------------------------------------


def goal_distance_reward(
    env: ManagerBasedRLEnv,
    std: float = 1.0,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Reward for approaching the goal.  ``1 - tanh(dist / std)``.

    Returns 1 when at the goal and decays smoothly.  Shape: (N,).
    """
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    robot_xy = asset.data.root_pos_w[:, :2]
    dist = torch.norm(goal_w[:, :2] - robot_xy, dim=-1)
    return 1.0 - torch.tanh(dist / std)


def distance_progress_reward(
    env: ManagerBasedRLEnv,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Reward proportional to decrease in goal distance since the last step.

    Positive when the robot moves closer (+), negative when moving further away (-).
    Directly mirrors the DQN reward: ``5 * (prev_distance - current_distance)``.
    The weight in the config should be set to 5.0 to match the DQN scaling.
    Shape: (N,).
    """
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    current_dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)

    if not hasattr(env, "_prev_goal_dist"):
        env._prev_goal_dist = current_dist.clone()

    progress = env._prev_goal_dist - current_dist  # + when closer, - when further
    env._prev_goal_dist = current_dist.clone()
    return progress


def time_step_penalty(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Constant -1 penalty every step to encourage efficiency.

    Mirrors the DQN '-1 per step' time penalty.  Set weight=-1.0 in the config.
    Shape: (N,).
    """
    return torch.ones(env.num_envs, device=env.device)


def goal_reached_bonus(
    env: ManagerBasedRLEnv,
    threshold: float = 0.25,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Sparse bonus (+1) when the robot is within *threshold* metres of the goal."""
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)
    return (dist < threshold).float()


# ---------------------------------------------------------------------------
# Collision penalties
# ---------------------------------------------------------------------------


def collision_penalty(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("contact_sensor"),
    threshold: float = 0.5,
) -> torch.Tensor:
    """Returns 1.0 for every environment where the net contact force exceeds *threshold*.

    Attach a :class:`ContactSensorCfg` to the robot's base body to use this.
    """
    sensor = env.scene[sensor_cfg.name]
    # sensor.data.net_forces_w is (N, num_bodies, 3)
    net_force = torch.norm(sensor.data.net_forces_w[:, :, :], dim=-1)  # (N, B)
    max_force = net_force.max(dim=-1).values  # (N,)
    return (max_force > threshold).float()


# ---------------------------------------------------------------------------
# Heading reward (DQN-inspired)
# ---------------------------------------------------------------------------


def heading_reward(
    env: ManagerBasedRLEnv,
    goal_pos_key: str = "goal_pos",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Reward for facing the goal: cos(heading_error) in [-1, 1].  Shape: (N,).

    Mirrors the DQN approach of rewarding alignment with the goal direction.
    Returns +1 when facing the goal and -1 when facing away.
    """
    asset = env.scene[asset_cfg.name]
    goal_w = _resolve_goal(env, goal_pos_key)
    robot_xy = asset.data.root_pos_w[:, :2]
    diff = goal_w[:, :2] - robot_xy  # (N, 2)

    angle_to_goal = torch.atan2(diff[:, 1], diff[:, 0])  # (N,)

    quat = asset.data.root_quat_w
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)

    heading_err = angle_to_goal - yaw
    return torch.cos(heading_err)  # (N,)


# ---------------------------------------------------------------------------
# Smoothness / energy penalties
# ---------------------------------------------------------------------------


def action_rate_penalty(env: ManagerBasedRLEnv) -> torch.Tensor:
    """L2 penalty on the change in actions between consecutive steps."""
    if not hasattr(env, "_prev_actions"):
        env._prev_actions = torch.zeros_like(env.action_manager.action)
    rate = torch.sum((env.action_manager.action - env._prev_actions) ** 2, dim=-1)
    env._prev_actions = env.action_manager.action.clone()
    return rate


def angular_velocity_penalty(
    env: ManagerBasedRLEnv,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """L2 penalty on yaw rate — encourages smooth turning."""
    asset = env.scene[asset_cfg.name]
    return asset.data.root_ang_vel_b[:, 2] ** 2


# ---------------------------------------------------------------------------
# Stage 3: Dynamic-obstacle-aware rewards
# ---------------------------------------------------------------------------


def time_to_collision_reward(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("lidar"),
    safe_ttc: float = 2.0,
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
) -> torch.Tensor:
    """Reward for maintaining a safe time-to-collision (TTC).

    TTC ≈ min_range / forward_speed.  Returns ``tanh(TTC / safe_ttc)`` so the
    agent is rewarded for keeping a comfortable gap ahead.
    """
    asset = env.scene[asset_cfg.name]
    fwd_speed = asset.data.root_lin_vel_b[:, 0].clamp(min=0.01)  # avoid div/0

    sensor = env.scene[sensor_cfg.name]
    hits = sensor.data.ray_hits_w
    origin = sensor.data.pos_w.unsqueeze(1)
    distances = torch.norm(hits - origin, dim=-1)  # (N, num_rays)
    min_range = distances.min(dim=-1).values  # (N,)

    ttc = min_range / fwd_speed
    return torch.tanh(ttc / safe_ttc)


def dynamic_obstacle_clearance(
    env: ManagerBasedRLEnv,
    sensor_cfg: SceneEntityCfg = SceneEntityCfg("lidar"),
    min_clearance: float = 0.3,
) -> torch.Tensor:
    """Penalty when the closest lidar range drops below *min_clearance* metres."""
    sensor = env.scene[sensor_cfg.name]
    hits = sensor.data.ray_hits_w
    origin = sensor.data.pos_w.unsqueeze(1)
    distances = torch.norm(hits - origin, dim=-1)
    min_dist = distances.min(dim=-1).values
    return (min_dist < min_clearance).float()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_goal(env: ManagerBasedRLEnv, key: str) -> torch.Tensor:
    """Return goal position (N, 2+) from env attribute or command manager."""
    if hasattr(env, key) and isinstance(getattr(env, key), torch.Tensor):
        return getattr(env, key)
    if hasattr(env, "command_manager") and key in env.command_manager.active_terms:
        cmd = env.command_manager.get_command(key)
        return cmd[:, :2]
    # Fallback: static goal 2 m ahead of origin
    return env.scene.env_origins[:, :2] + torch.tensor([[2.0, 0.0]], device=env.device)
