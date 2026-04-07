from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def target_pos_w(env: "ManagerBasedRLEnv", asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Return target position in world frame."""
    target: RigidObject = env.scene[asset_cfg.name]
    return target.data.root_pos_w


def eef_pos_w(env: "ManagerBasedRLEnv", asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Return end-effector position in world frame for the specified robot body."""
    robot: Articulation = env.scene[asset_cfg.name]
    return robot.data.body_pos_w[:, asset_cfg.body_ids[0]]  # type: ignore[index]


def eef_quat_w(env: "ManagerBasedRLEnv", asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Return end-effector orientation (quat xyzw) in world frame for the specified robot body."""
    robot: Articulation = env.scene[asset_cfg.name]
    return robot.data.body_quat_w[:, asset_cfg.body_ids[0]]  # type: ignore[index]


def eef_to_target_vec_w(
    env: "ManagerBasedRLEnv", eef_cfg: SceneEntityCfg, target_cfg: SceneEntityCfg
) -> torch.Tensor:
    """Vector from EEF to target in world frame."""
    eef = eef_pos_w(env, eef_cfg)
    target = target_pos_w(env, target_cfg)
    return target - eef


def attach_sponge_to_wrist(
    env: "ManagerBasedRLEnv",
    env_ids: torch.Tensor | None,
    eef_cfg: SceneEntityCfg,
    sponge_cfg: SceneEntityCfg,
    pos_offset: tuple[float, float, float] = (0.0, 0.0, -0.04),
) -> None:
    """Kinematically attach sponge root pose to the wrist pose (with a small offset)."""
    if env_ids is None:
        env_ids = torch.arange(env.scene.num_envs, device=env.device)

    robot: Articulation = env.scene[eef_cfg.name]
    sponge: RigidObject = env.scene[sponge_cfg.name]

    eef_pos = robot.data.body_pos_w[env_ids, eef_cfg.body_ids[0]]  # type: ignore[index]
    eef_quat = robot.data.body_quat_w[env_ids, eef_cfg.body_ids[0]]  # type: ignore[index]

    # Sponge pose: same orientation as wrist, position offset in world frame (simple, stable).
    offset = torch.tensor(pos_offset, device=env.device).unsqueeze(0).repeat(len(env_ids), 1)
    sponge_pos = eef_pos + offset

    sponge.write_root_pose_to_sim(torch.cat([sponge_pos, eef_quat], dim=-1), env_ids=env_ids)
    sponge.write_root_velocity_to_sim(torch.zeros((len(env_ids), 6), device=env.device), env_ids=env_ids)

