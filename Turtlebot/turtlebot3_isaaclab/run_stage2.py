#!/usr/bin/env python3
# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 2 — Train TurtleBot3 navigation in a static obstacle environment.

Usage
-----
    # Train with RSL-RL PPO (GUI)
    python run_stage2.py --mode train --num_envs 512

    # Train + record 3-min video
    python run_stage2.py --mode train --num_envs 512 --video --video_length 5400

    # Evaluate a trained checkpoint
    python run_stage2.py --mode eval --checkpoint /path/to/model.pt
"""

from __future__ import annotations

import argparse
import os
import sys
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

# ---------------------------------------------------------------------------
# Isaac Sim app — must be created before any omni/isaaclab imports
# ---------------------------------------------------------------------------
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Stage 2 — Static environment navigation")
parser.add_argument("--num_envs", type=int, default=512)
parser.add_argument("--mode", choices=["verify", "train", "eval"], default="verify")
parser.add_argument("--checkpoint", type=str, default=None)
parser.add_argument("--max_iterations", type=int, default=1000)
# Video recording
parser.add_argument("--video", action="store_true", default=False,
                    help="Record a video (saved to logs/stage2/videos/).")
parser.add_argument("--video_length", type=int, default=5400,
                    help="Steps to record. Default 5400 = 3 min at 30 steps/s.")
parser.add_argument("--video_interval", type=int, default=0,
                    help="Trigger new clip every N steps (0 = record once from step 0).")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Post-launch imports
# ---------------------------------------------------------------------------
from turtlebot3_isaaclab.stages.stage2_static_env_cfg import Stage2EnvCfg  # noqa: E402
from isaaclab.envs import ManagerBasedRLEnv  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg  # noqa: E402
from turtlebot3_isaaclab.goal_visual import update_goal_marker  # noqa: E402

_ROBOT_MARKER_CFG = VisualizationMarkersCfg(
    prim_path="/Visuals/RobotMarker",
    markers={
        "robot": sim_utils.SphereCfg(
            radius=0.10,
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(0.0, 0.75, 1.0),
                emissive_color=(0.0, 0.2, 0.3),
                opacity=0.9,
            ),
        ),
    },
)
_robot_marker: VisualizationMarkers | None = None


# ---------------------------------------------------------------------------
# Helper: peel off gymnasium wrappers to reach the raw ManagerBasedRLEnv
# ---------------------------------------------------------------------------

def _get_base(env) -> ManagerBasedRLEnv:
    """Return the underlying ManagerBasedRLEnv, unwrapping any gym wrappers."""
    return getattr(env, "unwrapped", env)


# ---------------------------------------------------------------------------
# Goal sampling + green marker update
# ---------------------------------------------------------------------------

def _sample_goals(env) -> None:
    """Sample a random goal for every env and move the green goal markers."""
    base = _get_base(env)

    if base.num_envs == 0:
        return

    goal = base.scene.env_origins[:, :2].clone()
    goal[:, 0] += torch.empty(base.num_envs, device=base.device).uniform_(-2.0, 2.0)
    goal[:, 1] += torch.empty(base.num_envs, device=base.device).uniform_(-2.0, 2.0)
    base.goal_pos = goal  # (N, 2)

    # Delegate to goal_visual so only one marker prim is ever created
    update_goal_marker(base)


def _update_robot_marker(env) -> None:
    """Update a bright marker at robot position for easy viewport tracking."""
    global _robot_marker
    base = _get_base(env)
    if _robot_marker is None:
        _robot_marker = VisualizationMarkers(_ROBOT_MARKER_CFG)
    robot_pos = base.scene["robot"].data.root_pos_w[:, :3].clone()
    if robot_pos.shape[0] == 0:
        return  # No envs — nothing to visualize
    robot_pos[:, 2] += 0.15
    _robot_marker.visualize(translations=robot_pos)


# =========================================================================
# Verification mode
# =========================================================================

def run_verify(env) -> None:
    base = _get_base(env)
    _sample_goals(env)
    _update_robot_marker(env)
    action_dim = env.action_space.shape[-1]

    for step in range(300):
        actions = torch.zeros(base.num_envs, action_dim, device=base.device)
        if 100 <= step < 200:
            actions[:, 0] = 0.5
        elif step >= 200:
            actions[:, 0] = 0.5

        obs, rew, term, trunc, info = env.step(actions)
        _update_robot_marker(env)
        if (term | trunc).any():
            _sample_goals(env)

        if step % 50 == 0:
            robot = base.scene["robot"]
            pos = robot.data.root_pos_w[0].cpu().numpy()
            vel = robot.data.root_lin_vel_b[0].cpu().numpy()
            print(
                f"  step {step:4d} | pos=({pos[0]:+.3f}, {pos[1]:+.3f}, {pos[2]:+.3f}) "
                f"| vel_body=({vel[0]:+.3f}, {vel[1]:+.3f}) "
                f"| reward={rew[0].item():+.4f}"
            )

    print("\n[Stage 2 — verify] Done.\n")


# =========================================================================
# Training mode — RSL-RL PPO
# =========================================================================

def run_train(env, max_iters: int, resume_ckpt: str | None = None) -> None:
    try:
        from rsl_rl.runners import OnPolicyRunner
    except ImportError:
        print("[Stage 2 — train] rsl_rl not installed. Falling back to verify mode.")
        run_verify(env)
        return

    base = _get_base(env)
    _sample_goals(env)

    # Install goal-resampling hook on the BASE env's reset so it fires even
    # when called internally by RslRlVecEnvWrapper during its own reset().
    _orig_reset = base.reset

    def _reset_with_goals(*a, **kw):
        result = _orig_reset(*a, **kw)
        _sample_goals(env)
        return result

    base.reset = _reset_with_goals

    # -- RSL-RL config -------------------------------------------------------
    policy_cfg = {
        "class_name": "ActorCritic",
        "init_noise_std": 1.0,
        "actor_hidden_dims": [128, 128],
        "critic_hidden_dims": [128, 128],
        "activation": "elu",
    }
    algorithm_cfg = {
        "class_name": "PPO",
        "value_loss_coef": 1.0,
        "use_clipped_value_loss": True,
        "clip_param": 0.2,
        "entropy_coef": 0.01,
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
        "num_steps_per_env": 64,
        "max_iterations": max_iters,
        "save_interval": 100,
        "log_interval": 10,
        "obs_groups": {"policy": ["policy"], "critic": ["policy"]},
        "policy": policy_cfg,
        "algorithm": algorithm_cfg,
    }

    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper  # noqa: E402

    # NaN/Inf sanitisation wrapper — prevents exploding PPO std values
    class _SafeWrapper:
        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def get_observations(self):
            obs = self._inner.get_observations()
            return obs.apply(lambda t: torch.nan_to_num(t, nan=0.0, posinf=0.0, neginf=0.0))

        def step(self, actions):
            obs, rew, dones, extras = self._inner.step(actions)
            obs = obs.apply(lambda t: torch.nan_to_num(t, nan=0.0, posinf=0.0, neginf=0.0))
            rew = torch.nan_to_num(rew, nan=0.0, posinf=0.0, neginf=0.0)
            return obs, rew, dones, extras

    rsl_env = _SafeWrapper(RslRlVecEnvWrapper(env))

    runner = OnPolicyRunner(rsl_env, runner_cfg, log_dir="logs/stage2", device=base.device)

    if resume_ckpt is not None:
        if not os.path.isfile(resume_ckpt):
            print(f"[Stage 2 — train] Resume checkpoint not found: {resume_ckpt}")
            return
        runner.load(resume_ckpt)
        print(f"[Stage 2 — train] Resumed from checkpoint: {resume_ckpt}")

    print(f"\n[Stage 2 — train] Starting PPO for {max_iters} iterations …\n")
    runner.learn(num_learning_iterations=max_iters)
    print("\n[Stage 2 — train] Training complete.\n")


# =========================================================================
# Eval mode
# =========================================================================

def run_eval(env, ckpt: str) -> None:
    try:
        from rsl_rl.modules import ActorCritic
    except ImportError:
        print("[Stage 2 — eval] rsl_rl not installed.")
        return

    base = _get_base(env)
    _sample_goals(env)
    _update_robot_marker(env)

    # Get one observation to infer the ActorCritic input structure.
    obs, _ = env.reset()
    # ActorCritic in the current rsl_rl expects:
    #   - obs: a TensorDict of observation groups
    #   - obs_groups: mapping group name -> list of term names
    # Our Stage-2 env uses a single group "policy" for both actor & critic.
    obs_groups = {"policy": ["policy"], "critic": ["policy"]}
    act_dim = env.action_space.shape[-1]

    # Hidden-layer sizes must match those used during training so that the
    # checkpoint weights load correctly. The current checkpoint corresponds to
    # a 2-layer MLP with 128 units per layer for both actor and critic.
    policy = ActorCritic(
        obs,
        obs_groups,
        act_dim,
        init_noise_std=0.5,
        actor_hidden_dims=[128, 128],
        critic_hidden_dims=[128, 128],
        activation="elu",
    ).to(base.device)
    state = torch.load(ckpt, map_location=base.device)
    policy.load_state_dict(state["model_state_dict"])
    policy.eval()

    def _sanitize_obs(o):
        """Replace NaN/inf in observations with 0, matching training wrapper."""
        if isinstance(o, dict):
            return {k: torch.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0) for k, v in o.items()}
        return torch.nan_to_num(o, nan=0.0, posinf=0.0, neginf=0.0)

    obs = _sanitize_obs(obs)

    for step in range(1000):
        with torch.no_grad():
            # ActorCritic expects the full observation TensorDict and uses
            # obs_groups to select the "policy" keys internally.
            actions = policy.act_inference(obs)
        obs, rew, term, trunc, info = env.step(actions)
        obs = _sanitize_obs(obs)
        _update_robot_marker(env)
        if (term | trunc).any():
            _sample_goals(env)

        if step % 100 == 0:
            pos = base.scene["robot"].data.root_pos_w[0].cpu().numpy()
            print(f"  step {step:4d} | pos=({pos[0]:+.2f},{pos[1]:+.2f}) | reward={rew[0].item():+.3f}")

    print("\n[Stage 2 — eval] Done.\n")


# =========================================================================
# Main
# =========================================================================

def main() -> None:
    env_cfg = Stage2EnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    if hasattr(args, "device") and args.device is not None:
        env_cfg.sim.device = args.device

    # rgb_array render mode is required for RecordVideo
    render_mode = "rgb_array" if args.video else None
    env = ManagerBasedRLEnv(cfg=env_cfg, render_mode=render_mode)

    # Wrap with RecordVideo — gymnasium wrapper that writes .mp4 files
    if args.video:
        import gymnasium as gym
        video_dir = os.path.join("logs", "stage2", "videos")
        os.makedirs(video_dir, exist_ok=True)
        trigger = (
            (lambda step: step % args.video_interval == 0)
            if args.video_interval > 0
            else (lambda step: step == 0)
        )
        env = gym.wrappers.RecordVideo(
            env,
            video_folder=video_dir,
            step_trigger=trigger,
            video_length=args.video_length,
            disable_logger=True,
        )
        print(f"\n[Stage 2] Video recording ON — {args.video_length} steps → {video_dir}\n")

    # Use the unwrapped base env for Isaac Lab attribute access
    base = _get_base(env)
    print(
        f"\n[Stage 2] {args.mode} | {base.num_envs} envs "
        f"| obs={base.observation_space} | act={base.action_space}\n"
    )

    if args.mode == "verify":
        run_verify(env)
    elif args.mode == "train":
        run_train(env, args.max_iterations, args.checkpoint)
    elif args.mode == "eval":
        if args.checkpoint is None:
            print("ERROR: --checkpoint required for eval mode.")
        else:
            run_eval(env, args.checkpoint)

    env.close()


if __name__ == "__main__":
    main()
