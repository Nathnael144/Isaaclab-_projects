from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def eef_target_distance_l2(
    env: "ManagerBasedRLEnv", eef_cfg: SceneEntityCfg, target_cfg: SceneEntityCfg
) -> torch.Tensor:
    """L2 distance between end-effector and target (world frame)."""
    robot: Articulation = env.scene[eef_cfg.name]
    target: RigidObject = env.scene[target_cfg.name]
    eef_pos = robot.data.body_pos_w[:, eef_cfg.body_ids[0]]  # type: ignore[index]
    tgt_pos = target.data.root_pos_w
    return torch.norm(eef_pos - tgt_pos, dim=-1)


def eef_target_distance_tanh(
    env: "ManagerBasedRLEnv", std: float, eef_cfg: SceneEntityCfg, target_cfg: SceneEntityCfg
) -> torch.Tensor:
    """Shaped reward for distance tracking using tanh kernel."""
    d = eef_target_distance_l2(env, eef_cfg, target_cfg)
    return 1.0 - torch.tanh(d / std)


def eef_height_error_abs(
    env: "ManagerBasedRLEnv", target_height: float, eef_cfg: SceneEntityCfg
) -> torch.Tensor:
    """Absolute error between EEF height and desired table height."""
    robot: Articulation = env.scene[eef_cfg.name]
    eef_pos = robot.data.body_pos_w[:, eef_cfg.body_ids[0]]  # type: ignore[index]
    return torch.abs(eef_pos[:, 2] - target_height)

