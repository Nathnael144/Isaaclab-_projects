#!/usr/bin/env python3
"""Train Stage-2 TurtleBot3 PPO in Isaac Lab (LiDAR).

Run this script with Isaac Lab's wrapper:
    isaaclab.sh -p train2.py --headless

To record a 1-minute Isaac Lab training video (LiDAR visualization, no camera):
    isaaclab.sh -p play_ppo_record_lidar.py --headless --checkpoint logs/train2/model_999.pt --duration_sec 60

Recordings are saved under turtlebot3_isaaclab/recordings/ (not cosmos_pipeline).
"""

from __future__ import annotations

import argparse
import os
import sys

import torch


# Ensure `turtlebot3_isaaclab` package imports when launched from IsaacLab repo.
_PKG_PARENT = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)


from turtlebot3_isaaclab.goal_visual import sample_goals_and_update_marker


def _sanitize_tensor(x: torch.Tensor) -> torch.Tensor:
    """Clamp NaN/Inf values that can destabilize PPO."""
    return torch.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)


def _sanitize_obs(obs):
    if hasattr(obs, "apply"):
        return obs.apply(_sanitize_tensor)
    if isinstance(obs, torch.Tensor):
        return _sanitize_tensor(obs)
    return obs


class SafeVecEnv:
    """Thin wrapper that sanitizes observations/rewards from Isaac Lab env."""

    def __init__(self, base_env):
        self.base_env = base_env

    def __getattr__(self, name):
        return getattr(self.base_env, name)

    def get_observations(self):
        return _sanitize_obs(self.base_env.get_observations())

    def step(self, actions):
        obs, rewards, dones, extras = self.base_env.step(actions)
        return _sanitize_obs(obs), _sanitize_tensor(rewards), dones, extras


def main() -> None:
    parser = argparse.ArgumentParser(description="Train2 - Stage 2 static PPO training")
    parser.add_argument("--num_envs", type=int, default=512)
    parser.add_argument("--max_iters", type=int, default=1000)
    parser.add_argument("--log_dir", type=str, default="logs/train2")
     # Optional checkpoint to resume training from (policy + optimizer state).
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to an existing RSL-RL checkpoint (e.g. model_final.pt) to resume from.",
    )

    from isaaclab.app import AppLauncher

    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    _app_launcher = AppLauncher(args)

    # Delay Isaac-Lab/Omniverse touching imports until after AppLauncher.
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.managers import SceneEntityCfg
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
    from rsl_rl.runners import OnPolicyRunner
    from turtlebot3_isaaclab.stages.stage2_static_env_cfg import Stage2EnvCfg

    env_cfg = Stage2EnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    # Stage-2 config currently stores this as a dict; convert to SceneEntityCfg
    # to match reset_root_state_uniform() expectations in Isaac Lab.
    env_cfg.events.reset_robot.params["asset_cfg"] = SceneEntityCfg("robot")
    if hasattr(args, "device") and args.device is not None:
        env_cfg.sim.device = args.device

    # Stage-2 Events now handle goal resampling and marker updates on every reset,
    # so we just create the environment here. The first reset is triggered by the
    # RslRlVecEnvWrapper inside the runner.
    env = ManagerBasedRLEnv(cfg=env_cfg)

    runner_cfg = {
        "num_steps_per_env": 24,
        "max_iterations": args.max_iters,
        "save_interval": 100,
        "log_interval": 10,
        "obs_groups": {
            "policy": ["policy"],
            "critic": ["policy"],
        },
        "policy": {
            "class_name": "ActorCritic",
            "init_noise_std": 0.5,
            "actor_hidden_dims": [128, 128],
            "critic_hidden_dims": [128, 128],
            "activation": "elu",
        },
        "algorithm": {
            "class_name": "PPO",
            "value_loss_coef": 1.0,
            "use_clipped_value_loss": True,
            "clip_param": 0.2,
            # Higher entropy to better mirror DQN's strong exploration (epsilon-greedy).
            "entropy_coef": 0.01,
            "num_learning_epochs": 5,
            "num_mini_batches": 4,
            "learning_rate": 3e-4,
            "schedule": "adaptive",
            "desired_kl": 0.01,
            "gamma": 0.99,
            "lam": 0.95,
            "max_grad_norm": 1.0,
        },
    }

    rsl_env = SafeVecEnv(RslRlVecEnvWrapper(env))
    runner = OnPolicyRunner(rsl_env, runner_cfg, log_dir=args.log_dir, device=env.device)

    # Optionally resume from an existing checkpoint (e.g. model_final.pt).
    if args.checkpoint is not None:
        ckpt_path = args.checkpoint
        if not os.path.isabs(ckpt_path):
            ckpt_path = os.path.join(args.log_dir, os.path.basename(ckpt_path))
        print(f"[train2] Loading checkpoint from {ckpt_path}")
        runner.load(ckpt_path)

    print(
        f"[train2] Starting PPO: device={env.device} num_envs={args.num_envs} "
        f"max_iters={args.max_iters} log_dir={args.log_dir}"
    )
    runner.learn(num_learning_iterations=args.max_iters)
    # Save final model so the trained policy is always available
    final_ckpt = os.path.join(args.log_dir, "model_final.pt")
    runner.save(final_ckpt)
    print(f"[train2] Final model saved to {final_ckpt}")
    env.close()


if __name__ == "__main__":
    main()
