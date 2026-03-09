#!/usr/bin/env python3
"""Play a trained Stage-2 TurtleBot3 PPO policy and record a LiDAR video.

This script:
- Loads the Stage-2 static PPO policy (same architecture as ``train2.py``).
- Runs it in the Stage-2 environment for a fixed duration.
- Records a simple 2D LiDAR visualization to an MP4 file (no RGB camera, no Cosmos).

Example usage (non-headless, 60-second LiDAR video):

    ./isaaclab.sh -p Turtlebot/turtlebot3_isaaclab/play_ppo_record_lidar.py \\
      --checkpoint /home/nathan/IsaacLab/logs/train2/model_999.pt \\
      --duration_sec 60

The output video is written under:

    Turtlebot/turtlebot3_isaaclab/recordings/
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

import cv2
import numpy as np
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


def _render_lidar_frame(lidar_ranges: np.ndarray, max_range: float = 3.5, size: int = 512) -> np.ndarray:
    """Render a simple top-down LiDAR fan image.

    Args:
        lidar_ranges: 1-D array of LiDAR distances (len = num_rays).
        max_range: Maximum LiDAR range used for normalization.
        size: Output image size (square, in pixels).

    Returns:
        BGR image (uint8) suitable for OpenCV VideoWriter.
    """
    img = np.zeros((size, size, 3), dtype=np.uint8)
    center = np.array([size // 2, size // 2], dtype=np.int32)
    radius_max = int(size * 0.45)

    num_rays = lidar_ranges.shape[0]
    # Rays cover 360 degrees with equal spacing.
    angles = np.linspace(0.0, 2.0 * np.pi, num_rays, endpoint=False)

    # Draw robot center.
    cv2.circle(img, center_tuple := tuple(center), 4, (0, 255, 0), -1)

    for r, theta in zip(lidar_ranges, angles):
        r_clamped = float(max(0.0, min(max_range, float(r))))
        # Normalize radius into [0, radius_max].
        rho = (r_clamped / max_range) * radius_max
        end_x = int(center[0] + rho * np.cos(theta))
        end_y = int(center[1] - rho * np.sin(theta))
        cv2.line(img, center_tuple, (end_x, end_y), (0, 255, 255), 2)

    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Stage-2 PPO and record LiDAR video.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to the trained PPO checkpoint (e.g. logs/train2/model_999.pt).",
    )
    parser.add_argument(
        "--duration_sec",
        type=float,
        default=60.0,
        help="Duration of the recording in seconds.",
    )
    parser.add_argument(
        "--num_envs",
        type=int,
        default=1,
        help="Number of parallel environments to simulate (video uses env 0).",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Video frames per second.",
    )
    parser.add_argument(
        "--log_dir",
        type=str,
        default="logs/train2",
        help="Log directory (used only for OnPolicyRunner bookkeeping).",
    )

    from isaaclab.app import AppLauncher

    # Allow user to control headless/GUI etc. (same as other Isaac Lab scripts).
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()

    app_launcher = AppLauncher(args)
    _simulation_app = app_launcher.app  # noqa: F841

    # Delay heavy imports until after AppLauncher.
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.managers import SceneEntityCfg
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
    from rsl_rl.runners import OnPolicyRunner
    from turtlebot3_isaaclab.stages.stage2_static_env_cfg import Stage2EnvCfg

    # --- Environment setup ----------------------------------------------------
    env_cfg = Stage2EnvCfg()
    env_cfg.scene.num_envs = args.num_envs
    env_cfg.events.reset_robot.params["asset_cfg"] = SceneEntityCfg("robot")
    if hasattr(args, "device") and args.device is not None:
        env_cfg.sim.device = args.device

    env = ManagerBasedRLEnv(cfg=env_cfg)
    sample_goals_and_update_marker(env)

    # Resample goals on every reset.
    _orig_reset = env.reset

    def _reset_with_goals(*a, **kw):
        result = _orig_reset(*a, **kw)
        sample_goals_and_update_marker(env)
        return result

    env.reset = _reset_with_goals  # type: ignore[method-assign]

    # --- PPO runner (same architecture as train2) -----------------------------
    runner_cfg = {
        "num_steps_per_env": 24,
        "max_iterations": 1,  # not used for inference; required by API
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
            "entropy_coef": 0.005,
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

    # Load trained policy.
    print(f"[play_ppo_record_lidar] Loading checkpoint: {args.checkpoint}")
    runner.load(args.checkpoint)
    policy = runner.get_inference_policy(device=env.device)

    # --- Video writer ---------------------------------------------------------
    recordings_dir = os.path.join(os.path.dirname(__file__), "recordings")
    os.makedirs(recordings_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(recordings_dir, f"train2_lidar_{timestamp}.mp4")

    fps = max(1, args.fps)
    frame_size = 512
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_path, fourcc, fps, (frame_size, frame_size))

    # --- Rollout loop ---------------------------------------------------------
    obs = rsl_env.get_observations()
    dt = env.step_dt
    total_frames = int(args.duration_sec * fps)
    step_skip = max(1, int(round(1.0 / (fps * dt))))  # env steps per video frame

    print(
        f"[play_ppo_record_lidar] Starting rollout: "
        f"duration={args.duration_sec}s, fps={fps}, frames={total_frames}, "
        f"env_dt={dt:.4f}, step_skip={step_skip}"
    )

    frame_count = 0
    step_idx = 0

    try:
        while frame_count < total_frames:
            with torch.inference_mode():
                actions = policy(obs)
                obs, _, dones, _ = rsl_env.step(actions)

            # Episode resets handled by env; keep rolling.
            if step_idx % step_skip == 0:
                # RslRlVecEnvWrapper returns dict of obs groups; we trained on 'policy'.
                obs_vec = obs["policy"][0]  # shape: (28,)
                lidar = obs_vec[4:].detach().cpu().numpy()  # last 24 dims
                frame = _render_lidar_frame(lidar, max_range=3.5, size=frame_size)
                writer.write(frame)
                frame_count += 1

            step_idx += 1

        print(f"[play_ppo_record_lidar] Finished recording to: {video_path}")
    finally:
        writer.release()
        env.close()


if __name__ == "__main__":
    main()

