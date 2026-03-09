#!/usr/bin/env python3
# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 3 — Train TurtleBot3 navigation with dynamic obstacles.

Extends Stage 2 with moving obstacles and updated reward shaping.

Usage
-----
    # Random-policy verification
    python run_stage3.py --headless --mode verify

    # Train with RSL-RL PPO
    python run_stage3.py --headless --mode train --num_envs 512 --max_iterations 2000

    # Evaluate a checkpoint
    python run_stage3.py --mode eval --checkpoint /path/to/model.pt
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

# ---------------------------------------------------------------------------
# Isaac Sim app
# ---------------------------------------------------------------------------
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Stage 3 — Dynamic environment navigation")
parser.add_argument("--num_envs", type=int, default=512)
parser.add_argument("--mode", choices=["verify", "train", "eval"], default="verify")
parser.add_argument("--checkpoint", type=str, default=None)
parser.add_argument("--max_iterations", type=int, default=2000)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
from turtlebot3_isaaclab.stages.stage3_dynamic_env_cfg import Stage3EnvCfg  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402


def _sample_goals(env: ManagerBasedRLEnv) -> None:
    """Randomly sample a goal position for each environment inside the arena."""
    goal = env.scene.env_origins[:, :2].clone()
    goal[:, 0] += torch.empty(env.num_envs, device=env.device).uniform_(-3.0, 3.0)
    goal[:, 1] += torch.empty(env.num_envs, device=env.device).uniform_(-3.0, 3.0)
    env.goal_pos = goal


# =========================================================================
# Verification mode
# =========================================================================


def run_verify(env: ManagerBasedRLEnv) -> None:
    _sample_goals(env)
    action_dim = env.action_space.shape[-1]

    for step in range(500):
        actions = torch.randn(env.num_envs, action_dim, device=env.device) * 0.3
        obs, rew, term, trunc, info = env.step(actions)

        if (term | trunc).any():
            _sample_goals(env)

        if step % 50 == 0:
            robot = env.scene["robot"]
            pos = robot.data.root_pos_w[0].cpu().numpy()

            # Show dynamic obstacle positions
            dyn_pos = []
            for name in ["dyn_cube_1", "dyn_cube_2", "dyn_sphere_1", "dyn_sphere_2"]:
                obj = env.scene[name]
                dp = obj.data.root_pos_w[0, :2].cpu().numpy()
                dyn_pos.append(f"({dp[0]:+.1f},{dp[1]:+.1f})")

            print(
                f"  step {step:4d} | robot=({pos[0]:+.2f},{pos[1]:+.2f}) "
                f"| dyn_obs={','.join(dyn_pos)} "
                f"| reward={rew[0].item():+.3f}"
            )

    print("\n[Stage 3 — verify] Done. Dynamic obstacles are moving.\n")


# =========================================================================
# Training mode — RSL-RL PPO
# =========================================================================


def run_train(env: ManagerBasedRLEnv, max_iters: int) -> None:
    try:
        from rsl_rl.runners import OnPolicyRunner
        from rsl_rl.modules import ActorCritic
        from rsl_rl.algorithms import PPO
    except ImportError:
        print("[Stage 3 — train] rsl_rl not installed. Falling back to verify mode.")
        run_verify(env)
        return

    _sample_goals(env)

    obs_dim = env.observation_space["policy"].shape[-1]
    act_dim = env.action_space.shape[-1]

    policy_cfg = {
        "class_name": "ActorCritic",
        "init_noise_std": 0.5,
        "actor_hidden_dims": [256, 256, 128],
        "critic_hidden_dims": [256, 256, 128],
        "activation": "elu",
    }
    algorithm_cfg = {
        "class_name": "PPO",
        "value_loss_coef": 1.0,
        "use_clipped_value_loss": True,
        "clip_param": 0.2,
        "entropy_coef": 0.005,
        "num_learning_epochs": 5,
        "num_mini_batches": 4,
        "learning_rate": 3e-4,
        "schedule": "adaptive",
        "desired_kl": 0.01,
        "gamma": 0.99,
        "lam": 0.95,
        "max_grad_norm": 1.0,
    }
    runner_cfg = {
        "num_steps_per_env": 24,
        "max_iterations": max_iters,
        "save_interval": 200,
        "log_interval": 10,
        "policy": policy_cfg,
        "algorithm": algorithm_cfg,
    }

    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402
    rsl_env = RslRlVecEnvWrapper(env)

    runner = OnPolicyRunner(rsl_env, runner_cfg, log_dir="logs/stage3", device=env.device)

    _orig_reset = env.reset

    def _reset_with_goals(*a, **kw):
        result = _orig_reset(*a, **kw)
        _sample_goals(env)
        return result

    env.reset = _reset_with_goals

    print(f"\n[Stage 3 — train] Starting PPO for {max_iters} iterations …\n")
    runner.learn(num_learning_iterations=max_iters)
    print("\n[Stage 3 — train] Training complete.\n")


# =========================================================================
# Eval mode
# =========================================================================


def run_eval(env: ManagerBasedRLEnv, ckpt: str) -> None:
    try:
        from rsl_rl.modules import ActorCritic
    except ImportError:
        print("[Stage 3 — eval] rsl_rl not installed.")
        return

    _sample_goals(env)

    obs_dim = env.observation_space["policy"].shape[-1]
    act_dim = env.action_space.shape[-1]

    policy = ActorCritic(obs_dim, obs_dim, act_dim, **{
        "init_noise_std": 0.5,
        "actor_hidden_dims": [256, 256, 128],
        "critic_hidden_dims": [256, 256, 128],
        "activation": "elu",
    }).to(env.device)
    state = torch.load(ckpt, map_location=env.device)
    policy.load_state_dict(state["model_state_dict"])
    policy.eval()

    obs, _ = env.reset()
    _sample_goals(env)

    for step in range(1000):
        with torch.no_grad():
            actions = policy.act_inference(obs["policy"])
        obs, rew, term, trunc, info = env.step(actions)
        if (term | trunc).any():
            _sample_goals(env)

        if step % 100 == 0:
            pos = env.scene["robot"].data.root_pos_w[0].cpu().numpy()
            print(f"  step {step:4d} | pos=({pos[0]:+.2f},{pos[1]:+.2f}) | reward={rew[0].item():+.3f}")

    print("\n[Stage 3 — eval] Done.\n")


# =========================================================================
# Main
# =========================================================================


def main() -> None:
    env_cfg = Stage3EnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    env = ManagerBasedRLEnv(cfg=env_cfg)

    print(f"\n[Stage 3] {args.mode} | {env.num_envs} envs | obs={env.observation_space} | act={env.action_space}\n")

    if args.mode == "verify":
        run_verify(env)
    elif args.mode == "train":
        run_train(env, args.max_iterations)
    elif args.mode == "eval":
        if args.checkpoint is None:
            print("ERROR: --checkpoint required for eval mode.")
        else:
            run_eval(env, args.checkpoint)

    env.close()


if __name__ == "__main__":
    main()
