# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from isaaclab.managers import SceneEntityCfg


def box_close_to_goal(
    env,
    object_cfg: SceneEntityCfg,
    goal_cfg: SceneEntityCfg,
    threshold: float,
) -> torch.Tensor:
    obj_pos = env.scene[object_cfg.name].data.root_pos_w
    goal_pos = env.scene[goal_cfg.name].data.root_pos_w
    dist = torch.norm(obj_pos - goal_pos, dim=-1)
    return dist < threshold

