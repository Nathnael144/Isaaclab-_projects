# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import torch

from isaaclab.assets import Articulation, RigidObject
from isaaclab.managers import EventTermCfg, ManagerTermBase, SceneEntityCfg


class AttachBoxToHandOnProximity(ManagerTermBase):
    """Simple scripted grasp: attach box to right hand when close; detach at goal.

    This is a training-friendly scaffold:
    - When the hand is close to the box, we "grasp" by kinematically slaving the box pose to the hand.
    - When the box is close to the goal, we "release" and let physics take over.

    Note: This is not contact-based grasping. It’s a practical first step to get
    approach→lift→carry→place training working reliably.
    """

    def __init__(self, cfg: EventTermCfg, env):
        super().__init__(cfg, env)
        self.robot_cfg: SceneEntityCfg = cfg.params["robot_cfg"]
        self.box_cfg: SceneEntityCfg = cfg.params["box_cfg"]
        self.goal_cfg: SceneEntityCfg = cfg.params["goal_cfg"]
        self.hand_body_name: str = cfg.params.get("hand_body_name", "right_wrist_yaw_link")
        self.attach_distance: float = float(cfg.params.get("attach_distance", 0.12))
        self.detach_distance: float = float(cfg.params.get("detach_distance", 0.25))
        self.box_hand_offset: tuple[float, float, float] = tuple(cfg.params.get("box_hand_offset", (0.10, 0.00, -0.02)))

        robot: Articulation = env.scene[self.robot_cfg.name]
        self._hand_body_idx, _ = robot.find_bodies(self.hand_body_name)
        if isinstance(self._hand_body_idx, (list, tuple)):
            self._hand_body_idx = self._hand_body_idx[0]

        self._grasped = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)

    def __call__(
        self,
        env,
        env_ids: torch.Tensor | None,
        robot_cfg: SceneEntityCfg,
        box_cfg: SceneEntityCfg,
        goal_cfg: SceneEntityCfg,
        hand_body_name: str = "right_wrist_yaw_link",
        attach_distance: float = 0.12,
        detach_distance: float = 0.25,
        box_hand_offset: tuple[float, float, float] = (0.10, 0.0, -0.02),
    ):
        # allow overriding parameters (manager validates signature)
        self.hand_body_name = hand_body_name
        self.attach_distance = float(attach_distance)
        self.detach_distance = float(detach_distance)
        self.box_hand_offset = tuple(box_hand_offset)

        # resolve ids
        if env_ids is None:
            env_ids = torch.arange(env.num_envs, device=env.device)

        robot: Articulation = env.scene[robot_cfg.name]
        box: RigidObject = env.scene[box_cfg.name]
        goal: RigidObject = env.scene[goal_cfg.name]

        # world poses
        hand_pose_w = robot.data.body_pose_w[:, self._hand_body_idx, :7]
        hand_pos_w = hand_pose_w[:, 0:3]
        hand_quat_w = hand_pose_w[:, 3:7]

        box_pos_w = box.data.root_pos_w
        goal_pos_w = goal.data.root_pos_w

        # distances
        hand_box_dist = torch.norm(hand_pos_w - box_pos_w, dim=-1)
        box_goal_dist = torch.norm(box_pos_w - goal_pos_w, dim=-1)

        # attach if close and not already grasped
        to_attach = (~self._grasped) & (hand_box_dist < self.attach_distance)
        self._grasped = self._grasped | to_attach

        # detach if close to goal
        to_detach = self._grasped & (box_goal_dist < self.detach_distance)
        self._grasped = self._grasped & (~to_detach)

        # follow hand while grasped
        if self._grasped.any():
            # simple offset in world frame (ok as scaffold)
            offset = torch.tensor(self.box_hand_offset, device=env.device).unsqueeze(0)
            target_pos_w = hand_pos_w + offset
            target_quat_w = hand_quat_w
            root_pose = torch.cat([target_pos_w, target_quat_w], dim=-1)

            follow_ids = torch.nonzero(self._grasped).squeeze(-1)
            box.write_root_pose_to_sim(root_pose[follow_ids], follow_ids)
            # zero velocities so it doesn't explode
            zeros = torch.zeros((follow_ids.shape[0], 6), device=env.device)
            box.write_root_velocity_to_sim(zeros, follow_ids)

