# Copyright (c) 2026.
# SPDX-License-Identifier: BSD-3-Clause

"""Play a trained RSL-RL checkpoint on Unitree tasks.

Mirrors the external play.py but fixes the broken
`isaaclab.utils.pretrained_checkpoint` import and imports the
Unitree task package so Gym registrations are available.
"""

import argparse
import os
import time
from importlib.metadata import version

from isaaclab.app import AppLauncher

# local imports (same directory as the external play.py)
import cli_args  # isort: skip

parser = argparse.ArgumentParser(description="Play a trained RSL-RL policy on Unitree tasks.")
parser.add_argument("--video", action="store_true", default=False, help="Record a video of the rollout.")
parser.add_argument("--video_length", type=int, default=200, help="Number of steps to record.")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument("--real-time", action="store_true", default=False, help="Try to run in real-time.")

cli_args.add_rsl_rl_args(parser)   # adds --checkpoint, --load_run, --resume ...
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

if args_cli.video:
    args_cli.enable_cameras = True

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# rest of imports (after Isaac Sim is up)
import gymnasium as gym  # noqa: E402
import torch  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from isaaclab.envs import DirectMARLEnv, multi_agent_to_single_agent  # noqa: E402
from isaaclab.utils.dict import print_dict  # noqa: E402
from isaaclab_rl.rsl_rl import (  # noqa: E402
    RslRlOnPolicyRunnerCfg,
    RslRlVecEnvWrapper,
    export_policy_as_jit,
    export_policy_as_onnx,
)
from isaaclab_tasks.utils import get_checkpoint_path  # noqa: E402

# import Unitree tasks (registers gym envs)
try:
    import unitree_rl_lab.tasks  # noqa: F401
    from unitree_rl_lab.utils.parser_cfg import parse_env_cfg
except Exception as exc:
    raise RuntimeError(
        "Failed to import unitree_rl_lab. "
        "Make sure the package is installed or on PYTHONPATH."
    ) from exc


def main():
    """Run inference with the trained Unitree G1 policy."""

    # agent config
    agent_cfg: RslRlOnPolicyRunnerCfg = cli_args.parse_rsl_rl_cfg(args_cli.task, args_cli)

    # env config (play variant with fewer envs / no curriculum)
    env_cfg = parse_env_cfg(
        args_cli.task,
        device=args_cli.device,
        num_envs=args_cli.num_envs,
        use_fabric=not args_cli.disable_fabric,
        entry_point_key="play_env_cfg_entry_point",
    )

    # resolve checkpoint path
    # If load_run and load_checkpoint are set, construct the path directly to
    # avoid experiment_name ambiguity when using external task packages.
    if agent_cfg.load_run and agent_cfg.load_checkpoint:
        # Try direct construction first: logs/rsl_rl/<experiment>/<run>/<ckpt>
        for candidate_exp in [agent_cfg.experiment_name, "unitree_g1_29dof_velocity"]:
            candidate = os.path.abspath(
                os.path.join("logs", "rsl_rl", candidate_exp, agent_cfg.load_run, agent_cfg.load_checkpoint)
            )
            if os.path.isfile(candidate):
                resume_path = candidate
                break
        else:
            log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
            resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
    else:
        log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)

    log_dir = os.path.dirname(resume_path)
    print(f"[INFO] Using checkpoint: {resume_path}")

    # make the environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)

    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "play"),
            "step_trigger": lambda step: step == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording video.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    # load runner & extract policy
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(resume_path)
    policy = runner.get_inference_policy(device=env.unwrapped.device)

    # export JIT / ONNX for deployment
    try:
        policy_nn = runner.alg.policy
    except AttributeError:
        policy_nn = runner.alg.actor_critic

    normalizer = None
    if hasattr(policy_nn, "actor_obs_normalizer"):
        normalizer = policy_nn.actor_obs_normalizer
    elif hasattr(policy_nn, "student_obs_normalizer"):
        normalizer = policy_nn.student_obs_normalizer

    export_dir = os.path.join(log_dir, "exported")
    export_policy_as_jit(policy_nn, normalizer=normalizer, path=export_dir, filename="policy.pt")
    export_policy_as_onnx(policy_nn, normalizer=normalizer, path=export_dir, filename="policy.onnx")

    # rollout loop
    dt = env.unwrapped.step_dt

    if version("rsl-rl-lib").startswith("2.3."):
        obs, _ = env.get_observations()
    else:
        obs = env.get_observations()

    timestep = 0
    while simulation_app.is_running():
        start_time = time.time()
        with torch.inference_mode():
            actions = policy(obs)
            obs, _, _, _ = env.step(actions)

        if args_cli.video:
            timestep += 1
            if timestep == args_cli.video_length:
                break

        sleep_time = dt - (time.time() - start_time)
        if args_cli.real_time and sleep_time > 0:
            time.sleep(sleep_time)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
