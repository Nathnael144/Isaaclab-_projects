"""Reward terms for place tasks (dense shaping + terminal bonus)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.assets import RigidObject
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import FrameTransformer

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


def ee_to_object_distance_exp(
    env: ManagerBasedRLEnv,
    ee_frame_cfg: SceneEntityCfg,
    object_cfg: SceneEntityCfg,
    std: float = 0.20,
) -> torch.Tensor:
    """Dense reach reward: exp(-||p_obj - p_ee||^2 / std^2)."""
    ee_frame: FrameTransformer = env.scene[ee_frame_cfg.name]
    obj: RigidObject = env.scene[object_cfg.name]
    p_ee = ee_frame.data.target_pos_w[:, 0, :] - env.scene.env_origins
    p_obj = obj.data.root_pos_w - env.scene.env_origins
    err = torch.sum(torch.square(p_obj - p_ee), dim=1)
    return torch.exp(-err / (std**2))


def object_a_to_object_b_xy_exp(
    env: ManagerBasedRLEnv,
    object_a_cfg: SceneEntityCfg,
    object_b_cfg: SceneEntityCfg,
    std: float = 0.25,
) -> torch.Tensor:
    """Dense place reward on XY only: exp(-||xy_a - xy_b||^2 / std^2)."""
    a: RigidObject = env.scene[object_a_cfg.name]
    b: RigidObject = env.scene[object_b_cfg.name]
    pa = a.data.root_pos_w - env.scene.env_origins
    pb = b.data.root_pos_w - env.scene.env_origins
    dxy2 = torch.sum(torch.square(pa[:, :2] - pb[:, :2]), dim=1)
    return torch.exp(-dxy2 / (std**2))


def toy2box_success(
    env: ManagerBasedRLEnv,
    robot_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
    toy_cfg: SceneEntityCfg = SceneEntityCfg("toy_truck"),
    box_cfg: SceneEntityCfg = SceneEntityCfg("box"),
    xy_threshold: float = 0.10,
    height_diff: float = 0.06,
    height_threshold: float = 0.04,
) -> torch.Tensor:
    """Sparse success signal (0/1) using the same predicate as the termination."""
    from .terminations import object_a_is_into_b

    return object_a_is_into_b(
        env,
        robot_cfg=robot_cfg,
        object_a_cfg=toy_cfg,
        object_b_cfg=box_cfg,
        xy_threshold=xy_threshold,
        height_threshold=height_threshold,
        height_diff=height_diff,
    ).float()

