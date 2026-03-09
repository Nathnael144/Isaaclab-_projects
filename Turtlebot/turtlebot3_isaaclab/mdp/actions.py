# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Custom differential-drive action term for TurtleBot3.

Maps a 2-D action ``[v_linear, omega]`` to per-wheel angular-velocity targets
using standard differential-drive kinematics:

    v_left  = (v - omega * track_width / 2) / wheel_radius
    v_right = (v + omega * track_width / 2) / wheel_radius
"""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

from isaaclab.assets import Articulation
from isaaclab.envs.mdp.actions import ActionTerm, ActionTermCfg
from isaaclab.utils import configclass

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedEnv

# ---------------------------------------------------------------------------
# Differential-drive action term
# ---------------------------------------------------------------------------


class DifferentialDriveAction(ActionTerm):
    """Converts ``(v, omega)`` into left/right wheel angular velocities."""

    cfg: DifferentialDriveActionCfg
    _asset: Articulation

    def __init__(self, cfg: DifferentialDriveActionCfg, env: ManagerBasedEnv):
        super().__init__(cfg, env)

        # Resolve joint indices for left and right wheels
        self._left_idx, _ = self._asset.find_joints(cfg.left_joint_name)
        self._right_idx, _ = self._asset.find_joints(cfg.right_joint_name)

        # Pre-compute kinematics matrix:  [v, omega] -> [wl, wr]
        #   wl = (v - omega * track/2) / R
        #   wr = (v + omega * track/2) / R
        R = cfg.wheel_radius
        d = cfg.track_width
        self._kin = torch.tensor(
            [[1.0 / R, -d / (2.0 * R)], [1.0 / R, d / (2.0 * R)]],
            device=env.device,
        )  # (2, 2)

        # Scale factors: allow action space to be normalised to [-1, 1]
        self._scale = torch.tensor(cfg.scale, device=env.device)
        self._offset = torch.tensor(cfg.offset, device=env.device)

        # When fixed_linear_vel is set the policy only outputs angular velocity
        self._fixed_lin = cfg.fixed_linear_vel

        # EMA smoothing buffer — initialised lazily on first process_actions call
        self._smooth_action: torch.Tensor | None = None
        self._smooth_alpha = cfg.smooth_alpha

    # -- properties ----------------------------------------------------------

    @property
    def action_dim(self) -> int:
        # 1-D when linear velocity is fixed (agent only learns angular vel)
        return 1 if self._fixed_lin is not None else 2

    @property
    def raw_actions(self) -> torch.Tensor:
        return self._raw

    @property
    def processed_actions(self) -> torch.Tensor:
        return self._processed

    # -- operations -----------------------------------------------------------

    def process_actions(self, actions: torch.Tensor) -> None:
        self._raw = actions

        # EMA smoothing: blends the new action with the previous smoothed action
        # to reduce jitter and produce fluid wheel-velocity commands.
        # smooth_alpha=1.0 disables smoothing (pass-through).
        if self._smooth_alpha < 1.0:
            if self._smooth_action is None or self._smooth_action.shape != actions.shape:
                self._smooth_action = actions.clone()
            else:
                self._smooth_action = (
                    self._smooth_alpha * actions
                    + (1.0 - self._smooth_alpha) * self._smooth_action
                )
            smoothed = self._smooth_action
        else:
            smoothed = actions

        if self._fixed_lin is not None:
            # Policy outputs (N, 1) — angular velocity only
            # Linear velocity is held constant at self._fixed_lin m/s
            linear = torch.full((smoothed.shape[0], 1), self._fixed_lin, device=smoothed.device)
            omega = smoothed * self._scale + self._offset  # (N, 1)
            self._processed = torch.cat([linear, omega], dim=-1)  # (N, 2)
        else:
            # De-normalise: actual_cmd = smoothed * scale + offset
            self._processed = smoothed * self._scale + self._offset  # (N, 2)

    def apply_actions(self) -> None:
        # (N, 2) @ (2, 2)^T -> (N, 2)  <=> [v, omega] -> [wl, wr]
        wheel_vels = self._processed @ self._kin.T  # (N, 2)
        # Set velocity targets on both wheel joints
        self._asset.set_joint_velocity_target(
            wheel_vels[:, 0:1], joint_ids=self._left_idx
        )
        self._asset.set_joint_velocity_target(
            wheel_vels[:, 1:2], joint_ids=self._right_idx
        )


# ---------------------------------------------------------------------------
# Config dataclass
# ---------------------------------------------------------------------------


@configclass
class DifferentialDriveActionCfg(ActionTermCfg):
    """Configuration for :class:`DifferentialDriveAction`."""

    class_type: type[ActionTerm] = DifferentialDriveAction

    # Joint names (must match USD prim names — note the a__namespace_ prefix)
    left_joint_name: str = "a__namespace_wheel_left_joint"
    right_joint_name: str = "a__namespace_wheel_right_joint"

    # Kinematics
    wheel_radius: float = 0.033
    track_width: float = 0.16

    # Action scaling:  cmd = action * scale + offset
    #  Default: scale=(0.22, 2.84) maps normalised [-1,1] to TurtleBot3's
    #  full [v, omega] range.
    #  When fixed_linear_vel is set, scale/offset apply to angular only,
    #  e.g. scale=(2.84,) maps [-1,1] to [-2.84, 2.84] rad/s.
    scale: tuple[float, ...] = (0.22, 2.84)
    offset: tuple[float, ...] = (0.0, 0.0)

    # When set, linear velocity is fixed at this value (m/s) and the policy
    # only outputs a 1-D angular velocity — matching the DQN training setup.
    fixed_linear_vel: float | None = None

    # EMA smoothing factor for the outgoing angular-velocity command.
    # new_cmd = alpha * raw + (1 - alpha) * prev_cmd
    # 0.3 = very smooth (70% momentum), 1.0 = no smoothing (pass-through).
    smooth_alpha: float = 0.3
