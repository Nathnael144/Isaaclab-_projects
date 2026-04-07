# Copyright (c) 2025-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""GR1T2 exhaust-pipe with Pink IK — state observations only, for RSL-RL (no RGB in policy obs)."""

from isaaclab.utils import configclass

from isaaclab_tasks.manager_based.manipulation.pick_place.exhaustpipe_gr1t2_base_env_cfg import (
    ObservationsStateOnlyCfg,
)
from isaaclab_tasks.manager_based.manipulation.pick_place.exhaustpipe_gr1t2_pink_ik_env_cfg import (
    ExhaustPipeGR1T2PinkIKEnvCfg,
)


@configclass
class ExhaustPipeGR1T2PinkIKRLEnvCfg(ExhaustPipeGR1T2PinkIKEnvCfg):
    """Same as :class:`ExhaustPipeGR1T2PinkIKEnvCfg` but uses concatenated proprio (drops onboard camera)."""

    observations: ObservationsStateOnlyCfg = ObservationsStateOnlyCfg()
