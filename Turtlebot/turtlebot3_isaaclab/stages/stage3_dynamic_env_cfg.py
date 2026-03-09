# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 3 — Dynamic-environment configuration.

Purpose
-------
Extend Stage 2 by introducing **moving obstacles** (primitive shapes that
follow scripted paths or random velocities) to simulate real-world dynamic
scenes such as pedestrian crowds.

New components (over Stage 2)
-----------------------------
  * **Dynamic obstacles**: rigid cubes/spheres spawned with scripted
    random linear velocities, periodically re-randomised.
  * **Updated rewards**: time-to-collision reward, dynamic-clearance penalty.
  * **Updated events**: random velocity perturbation for dynamic obstacles.
"""

from __future__ import annotations

import math

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs.mdp import time_out
from isaaclab.managers import (
    EventTermCfg as EventTerm,
    ObservationGroupCfg as ObsGroup,
    ObservationTermCfg as ObsTerm,
    RewardTermCfg as RewTerm,
    SceneEntityCfg,
    TerminationTermCfg as DoneTerm,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.sensors.ray_caster import MultiMeshRayCasterCfg
from isaaclab.sensors.ray_caster.patterns import LidarPatternCfg
from isaaclab.utils import configclass

# -- Local imports -----------------------------------------------------------
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from turtlebot3_isaaclab.config.robot_cfg import TURTLEBOT3_CFG
from turtlebot3_isaaclab.mdp.actions import DifferentialDriveActionCfg
from turtlebot3_isaaclab.mdp import observations as obs_terms
from turtlebot3_isaaclab.mdp import rewards as rew_terms
from turtlebot3_isaaclab.mdp import terminations as term_terms

import isaaclab.envs.mdp as lab_mdp


# ============================================================================
# Scene
# ============================================================================


@configclass
class Stage3SceneCfg(InteractiveSceneCfg):
    """Ground + robot + static walls + dynamic obstacles + LiDAR + contact."""

    # -- Ground & light ------------------------------------------------------
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(size=(100.0, 100.0)),
    )
    dome_light = AssetBaseCfg(
        prim_path="/World/DomeLight",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=500.0),
    )

    # -- Robot ---------------------------------------------------------------
    robot: ArticulationCfg = TURTLEBOT3_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot",
    )

    # -- Arena boundary walls (static, kinematic) ----------------------------
    wall_north = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallNorth",
        spawn=sim_utils.CuboidCfg(
            size=(8.0, 0.1, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 4.0, 0.25)),
    )
    wall_south = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallSouth",
        spawn=sim_utils.CuboidCfg(
            size=(8.0, 0.1, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, -4.0, 0.25)),
    )
    wall_east = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallEast",
        spawn=sim_utils.CuboidCfg(
            size=(0.1, 8.0, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(4.0, 0.0, 0.25)),
    )
    wall_west = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallWest",
        spawn=sim_utils.CuboidCfg(
            size=(0.1, 8.0, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-4.0, 0.0, 0.25)),
    )

    # -- Dynamic obstacles (rigid, non-kinematic → physics-driven) -----------
    # Each is a RigidObjectCfg so we can set linear velocity at reset.
    dyn_cube_1: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynCube1",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,  # float at fixed height
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.4, 0.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(1.5, 1.5, 0.15),
            lin_vel=(0.3, -0.2, 0.0),
        ),
    )
    dyn_cube_2: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynCube2",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.6, 0.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-1.0, 2.0, 0.15),
            lin_vel=(-0.4, 0.1, 0.0),
        ),
    )
    dyn_sphere_1: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynSphere1",
        spawn=sim_utils.SphereCfg(
            radius=0.15,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.8, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(2.0, -1.0, 0.15),
            lin_vel=(0.2, 0.3, 0.0),
        ),
    )
    dyn_sphere_2: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynSphere2",
        spawn=sim_utils.SphereCfg(
            radius=0.15,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.0, 0.6, 0.8)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-2.0, -2.0, 0.15),
            lin_vel=(-0.1, -0.4, 0.0),
        ),
    )

    # -- Sensors -------------------------------------------------------------
    lidar = MultiMeshRayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/a__namespace_base_link",
        update_period=1.0 / 30.0,
        offset=MultiMeshRayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 0.172)),
        mesh_prim_paths=[
            "/World/ground",
            "{ENV_REGEX_NS}/WallNorth",
            "{ENV_REGEX_NS}/WallSouth",
            "{ENV_REGEX_NS}/WallEast",
            "{ENV_REGEX_NS}/WallWest",
            "{ENV_REGEX_NS}/DynCube1",
            "{ENV_REGEX_NS}/DynCube2",
            "{ENV_REGEX_NS}/DynSphere1",
            "{ENV_REGEX_NS}/DynSphere2",
        ],
        pattern_cfg=LidarPatternCfg(
            channels=1,
            vertical_fov_range=(0.0, 0.0),
            horizontal_fov_range=(0.0, 360.0),
            horizontal_res=2.0,
        ),
        max_distance=3.5,
    )

    contact_sensor = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/a__namespace_base_link",
        update_period=0.0,
    )


# ============================================================================
# Actions
# ============================================================================


@configclass
class Stage3ActionsCfg:
    drive = DifferentialDriveActionCfg(
        asset_name="robot",
        left_joint_name="a__namespace_wheel_left_joint",
        right_joint_name="a__namespace_wheel_right_joint",
        wheel_radius=0.033,
        track_width=0.16,
        scale=(0.22, 2.84),
    )


# ============================================================================
# Observations
# ============================================================================


@configclass
class Stage3ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        base_lin_vel = ObsTerm(func=obs_terms.base_linear_velocity_xy)
        base_ang_vel = ObsTerm(func=obs_terms.base_angular_velocity_z)
        goal_body = ObsTerm(func=obs_terms.goal_position_in_robot_frame)
        lidar = ObsTerm(
            func=obs_terms.lidar_scan,
            params={"sensor_cfg": SceneEntityCfg("lidar")},
        )

        def __post_init__(self) -> None:
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


# ============================================================================
# Rewards
# ============================================================================


@configclass
class Stage3RewardsCfg:
    # -- Goal tracking -------------------------------------------------------
    goal_distance = RewTerm(
        func=rew_terms.goal_distance_reward,
        weight=2.0,
        params={"std": 1.0},
    )
    goal_reached = RewTerm(
        func=rew_terms.goal_reached_bonus,
        weight=10.0,
        params={"threshold": 0.25},
    )

    # -- Static collision (contact sensor) -----------------------------------
    collision = RewTerm(
        func=rew_terms.collision_penalty,
        weight=-5.0,
        params={"sensor_cfg": SceneEntityCfg("contact_sensor"), "threshold": 0.5},
    )

    # -- Dynamic obstacle awareness ------------------------------------------
    time_to_collision = RewTerm(
        func=rew_terms.time_to_collision_reward,
        weight=1.0,
        params={"sensor_cfg": SceneEntityCfg("lidar"), "safe_ttc": 2.0},
    )
    dynamic_clearance = RewTerm(
        func=rew_terms.dynamic_obstacle_clearance,
        weight=-3.0,
        params={"sensor_cfg": SceneEntityCfg("lidar"), "min_clearance": 0.3},
    )

    # -- Smoothness ----------------------------------------------------------
    action_rate = RewTerm(func=rew_terms.action_rate_penalty, weight=-0.01)
    ang_vel = RewTerm(func=rew_terms.angular_velocity_penalty, weight=-0.005)


# ============================================================================
# Terminations
# ============================================================================


@configclass
class Stage3TerminationsCfg:
    time_out = DoneTerm(func=time_out, time_out=True)
    goal_reached = DoneTerm(
        func=term_terms.goal_reached,
        params={"threshold": 0.25},
    )
    robot_flipped = DoneTerm(
        func=term_terms.robot_flipped,
        params={"limit_angle": 0.8},
    )
    out_of_bounds = DoneTerm(
        func=term_terms.out_of_bounds,
        params={"x_bounds": (-4.5, 4.5), "y_bounds": (-4.5, 4.5)},
    )


# ============================================================================
# Events
# ============================================================================


@configclass
class Stage3EventsCfg:
    # Reset robot pose
    reset_robot = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5), "yaw": (-math.pi, math.pi)},
            "velocity_range": {},
        },
    )

    # Reset dynamic obstacle positions & velocities on episode reset
    reset_dyn_cube_1 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_cube_1"),
            "pose_range": {"x": (-3.0, 3.0), "y": (-3.0, 3.0)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_cube_2 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_cube_2"),
            "pose_range": {"x": (-3.0, 3.0), "y": (-3.0, 3.0)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_sphere_1 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_sphere_1"),
            "pose_range": {"x": (-3.0, 3.0), "y": (-3.0, 3.0)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_sphere_2 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_sphere_2"),
            "pose_range": {"x": (-3.0, 3.0), "y": (-3.0, 3.0)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )


# ============================================================================
# Top-level environment config
# ============================================================================


@configclass
class Stage3EnvCfg(ManagerBasedRLEnvCfg):
    """Stage 3 — dynamic obstacle navigation."""

    scene: Stage3SceneCfg = Stage3SceneCfg(num_envs=512, env_spacing=10.0)
    actions: Stage3ActionsCfg = Stage3ActionsCfg()
    observations: Stage3ObservationsCfg = Stage3ObservationsCfg()
    rewards: Stage3RewardsCfg = Stage3RewardsCfg()
    terminations: Stage3TerminationsCfg = Stage3TerminationsCfg()
    events: Stage3EventsCfg = Stage3EventsCfg()

    goal_pos: tuple[float, float] = (2.0, 0.0)

    def __post_init__(self) -> None:
        self.decimation = 4
        self.episode_length_s = 40.0
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
