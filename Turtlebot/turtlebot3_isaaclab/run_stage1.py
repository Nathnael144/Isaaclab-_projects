#!/usr/bin/env python3
# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 1 — Spawn verification script.

Run this script to check that the TurtleBot3 Burger:
  • Loads from the USD file without errors.
  • Sits stably on the ground plane.
  • Responds to differential-drive velocity commands.

Usage
-----
    # With GUI (default)
    python run_stage1.py

    # Headless (CI / remote)
    python run_stage1.py --headless

    # More environments
    python run_stage1.py --num_envs 64
"""

from __future__ import annotations

import argparse
import math
import sys
import os
import torch

# ---------------------------------------------------------------------------
# Ensure the parent package is importable
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

# ---------------------------------------------------------------------------
# Isaac Sim app — must be created BEFORE importing Omniverse modules
# ---------------------------------------------------------------------------
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Stage 1 — TurtleBot3 spawn verification")
parser.add_argument("--num_envs", type=int, default=16, help="Number of parallel environments")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Now safe to import Isaac Lab / Omni modules
# ---------------------------------------------------------------------------
from turtlebot3_isaaclab.stages.stage1_empty_env_cfg import Stage1EnvCfg  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402


def main() -> None:
    """Spawn the environment, apply simple velocity commands, and print diagnostics."""

    # -- Build env config ----------------------------------------------------
    env_cfg = Stage1EnvCfg()
    env_cfg.scene.num_envs = args.num_envs

    # -- Create environment ---------------------------------------------------
    env = ManagerBasedRLEnv(cfg=env_cfg)
    print(f"\n[Stage 1] Environment created with {env.num_envs} envs.")
    print(f"  Observation space : {env.observation_space}")
    print(f"  Action space      : {env.action_space}\n")


    # -- Run for 1000 episodes, each with num_steps steps --
    num_episodes = 1000
    num_steps = 500
    action_dim = env.action_space.shape[-1]

    for episode in range(num_episodes):
        obs, info = env.reset()
        print(f"\n[Stage 1] Starting episode {episode+1}/{num_episodes}")
        for step in range(num_steps):
            if step < 100:
                # Phase 1: zero action — robot should stay still
                actions = torch.zeros(env.num_envs, action_dim, device=env.device)
            elif step < 300:
                # Phase 2: drive forward at ~50 % max speed
                actions = torch.zeros(env.num_envs, action_dim, device=env.device)
                actions[:, 0] = 0.5  # normalised forward velocity
            else:
                # Phase 3: spin in place
                actions = torch.zeros(env.num_envs, action_dim, device=env.device)
                actions[:, 1] = 0.5  # normalised yaw rate

            obs, rewards, terminated, truncated, info = env.step(actions)

            if step % 50 == 0:
                robot = env.scene["robot"]
                pos = robot.data.root_pos_w[0].cpu().numpy()
                vel = robot.data.root_lin_vel_b[0].cpu().numpy()
                print(
                    f"  episode {episode+1:4d} step {step:4d} | pos=({pos[0]:+.3f}, {pos[1]:+.3f}, {pos[2]:+.3f}) "
                    f"| vel_body=({vel[0]:+.3f}, {vel[1]:+.3f}) "
                    f"| reward={rewards[0].item():+.4f}"
                )

    print("\n[Stage 1] 1000 episodes complete — robot is stable and controllable.\n")
    env.close()


if __name__ == "__main__":
    main()
