# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Goal visualization: green circle in the environment, updated when goal is resampled."""

from __future__ import annotations

import torch

# Lazy imports for Isaac Lab / Omniverse (after AppLauncher)
_goal_marker = None


def _get_goal_marker():
    global _goal_marker
    if _goal_marker is None:
        import isaaclab.sim as sim_utils
        from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
        cfg = VisualizationMarkersCfg(
            prim_path="/Visuals/GoalMarkers",
            markers={
                "goal": sim_utils.CylinderCfg(
                    radius=0.25,
                    height=0.05,
                    visual_material=sim_utils.PreviewSurfaceCfg(
                        diffuse_color=(0.0, 1.0, 0.0),
                        emissive_color=(0.0, 0.4, 0.0),
                        opacity=0.9,
                    ),
                ),
            },
        )
        _goal_marker = VisualizationMarkers(cfg)
    return _goal_marker


def sample_goals_and_update_marker(env) -> None:
    """Sample random 2-D goals for each env, set env.goal_pos, and draw the goal circle(s).

    The goal is sampled relative to the robot's current starting position so that
    every time the robot is reset to its initial pose, it also receives a new
    goal position.
    """
    robot = env.scene["robot"]
    # Base positions for each env at reset.
    base_xy = robot.data.root_pos_w[:, :2].clone()
    # Sample goal offsets in a box around the start pose.
    dx = torch.empty(env.num_envs, device=env.device).uniform_(-2.0, 2.0)
    dy = torch.empty(env.num_envs, device=env.device).uniform_(-2.0, 2.0)
    goal = base_xy
    goal[:, 0] += dx
    goal[:, 1] += dy
    env.goal_pos = goal
    update_goal_marker(env)


def sample_goals_and_update_marker_for_envs(env, env_ids) -> None:
    """Sample new goals *only* for the specified env_ids and update the marker.

    This is used by the Stage-2 Events config on every episode reset so that
    successful / failed environments receive a fresh goal position.
    """
    # Ensure goal_pos exists
    if not hasattr(env, "goal_pos") or env.goal_pos is None:
        env.goal_pos = torch.zeros((env.num_envs, 2), device=env.device)

    robot = env.scene["robot"]
    base_xy = robot.data.root_pos_w[env_ids, :2].clone()

    dx = torch.empty(len(env_ids), device=env.device).uniform_(-2.0, 2.0)
    dy = torch.empty(len(env_ids), device=env.device).uniform_(-2.0, 2.0)
    base_xy[:, 0] += dx
    base_xy[:, 1] += dy

    env.goal_pos[env_ids] = base_xy
    update_goal_marker(env)


def update_goal_marker(env) -> None:
    """Update the green goal circle(s) from env.goal_pos. Call after changing goal_pos."""
    if not hasattr(env, "goal_pos") or env.goal_pos is None:
        return
    goal = env.goal_pos  # (N, 2)
    if goal.dim() == 1:
        goal = goal.unsqueeze(0)
    z = torch.full((goal.shape[0], 1), 0.03, device=goal.device, dtype=goal.dtype)
    translations = torch.cat([goal[:, :2], z], dim=-1)
    _get_goal_marker().visualize(translations=translations)
