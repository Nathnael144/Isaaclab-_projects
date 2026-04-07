from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import SceneEntityCfg

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def eef_close_to_target(
    env: "ManagerBasedRLEnv",
    threshold: float,
    eef_cfg: SceneEntityCfg,
    target_cfg: SceneEntityCfg,
) -> torch.Tensor:
    """Terminate when the end-effector gets within a distance threshold."""
    robot: Articulation = env.scene[eef_cfg.name]
    target: RigidObject = env.scene[target_cfg.name]
    eef_pos = robot.data.body_pos_w[:, eef_cfg.body_ids[0]]  # type: ignore[index]
    tgt_pos = target.data.root_pos_w
    d = torch.norm(eef_pos - tgt_pos, dim=-1)
    return d < threshold

