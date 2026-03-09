# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 1 — Empty-environment configuration.

Purpose
-------
Spawn the TurtleBot3 Burger on a flat ground plane with a dome light.
Only the robot and the ground are present — no obstacles, no RL rewards.

This stage is used to **verify** that:
  1. The USD loads without errors.
  2. The robot does not fall through the floor.
  3. The robot does not explode due to physics instabilities.
  4. Wheel joints are controllable via velocity targets.
"""

from __future__ import annotations

import math

import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, ArticulationCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs.mdp import time_out
from isaaclab.managers import (
    EventTermCfg as EventTerm,
    ObservationGroupCfg as ObsGroup,
    ObservationTermCfg as ObsTerm,
    RewardTermCfg as RewTerm,
    TerminationTermCfg as DoneTerm,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

# -- Local imports -----------------------------------------------------------
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from turtlebot3_isaaclab.config.robot_cfg import TURTLEBOT3_CFG
from turtlebot3_isaaclab.mdp.actions import DifferentialDriveActionCfg
from turtlebot3_isaaclab.mdp import observations as obs_terms

import isaaclab.envs.mdp as lab_mdp

# ============================================================================
# Scene
# ============================================================================


@configclass
class Stage1SceneCfg(InteractiveSceneCfg):
    """Ground plane + TurtleBot3 robot."""

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )
    robot: ArticulationCfg = TURTLEBOT3_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot",
    )


# ============================================================================
# Actions
# ============================================================================


@configclass
class Stage1ActionsCfg:
    """Differential-drive: 2-D action [v_linear, omega]."""

    drive = DifferentialDriveActionCfg(
        asset_name="robot",
        left_joint_name="a__namespace_wheel_left_joint",
        right_joint_name="a__namespace_wheel_right_joint",
        wheel_radius=0.033,
        track_width=0.16,
        scale=(0.22, 2.84),
    )


# ============================================================================
# Observations  (minimal — just base state for debugging)
# ============================================================================


@configclass
class Stage1ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        base_lin_vel = ObsTerm(func=obs_terms.base_linear_velocity_xy)
        base_ang_vel = ObsTerm(func=obs_terms.base_angular_velocity_z)
        base_pos = ObsTerm(func=obs_terms.base_position_xy)
        base_yaw = ObsTerm(func=obs_terms.base_yaw)

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


# ============================================================================
# Rewards (dummy — just keep alive)
# ============================================================================


@configclass
class Stage1RewardsCfg:
    alive = RewTerm(func=lab_mdp.is_alive, weight=1.0)


# ============================================================================
# Terminations
# ============================================================================


@configclass
class Stage1TerminationsCfg:
    time_out = DoneTerm(func=time_out, time_out=True)


# ============================================================================
# Events (resets)
# ============================================================================


@configclass
class Stage1EventsCfg:
    from isaaclab.managers import SceneEntityCfg
    reset_robot = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-math.pi, math.pi)},
            "velocity_range": {},
        },
    )


# ============================================================================
# Top-level environment config
# ============================================================================


@configclass
class Stage1EnvCfg(ManagerBasedRLEnvCfg):
    """Stage 1 — empty world, just the robot on a ground plane."""

    scene: Stage1SceneCfg = Stage1SceneCfg(num_envs=16, env_spacing=4.0)
    actions: Stage1ActionsCfg = Stage1ActionsCfg()
    observations: Stage1ObservationsCfg = Stage1ObservationsCfg()
    rewards: Stage1RewardsCfg = Stage1RewardsCfg()
    terminations: Stage1TerminationsCfg = Stage1TerminationsCfg()
    events: Stage1EventsCfg = Stage1EventsCfg()

    def __post_init__(self) -> None:
        self.decimation = 4
        self.episode_length_s = 10.0
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
