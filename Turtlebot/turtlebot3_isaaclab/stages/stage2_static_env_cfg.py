# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""Stage 2 — Static-environment configuration.

Purpose
-------
Train a TurtleBot3 to navigate to a goal coordinate while avoiding **fixed**
obstacles (walls and pillars) placed on a ground plane.

Components
----------
  * **Scene**: ground plane + robot + static obstacles (walls & pillars) +
    2-D LiDAR (RayCaster) + contact sensor.
  * **Actions**: differential-drive ``[v, omega]``.
  * **Observations**: LiDAR scan, robot velocity, goal in robot frame.
  * **Rewards**: goal-distance shaping, goal-reached bonus, collision penalty,
    action-rate penalty, angular-velocity penalty.
  * **Terminations**: time-out, goal reached, robot flipped, out-of-bounds.
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
from turtlebot3_isaaclab.goal_visual import sample_goals_and_update_marker_for_envs

import isaaclab.envs.mdp as lab_mdp


# ============================================================================
# Scene
# ============================================================================


@configclass
class Stage2SceneCfg(InteractiveSceneCfg):
    """Ground + robot + static obstacles + LiDAR + contact sensor."""

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

    # -- Static obstacles ----------------------------------------------------
    # Wall segments
    wall_north = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallNorth",
        spawn=sim_utils.CuboidCfg(
            size=(6.0, 0.1, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 3.0, 0.25)),
    )
    wall_south = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallSouth",
        spawn=sim_utils.CuboidCfg(
            size=(6.0, 0.1, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, -3.0, 0.25)),
    )
    wall_east = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallEast",
        spawn=sim_utils.CuboidCfg(
            size=(0.1, 6.0, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(3.0, 0.0, 0.25)),
    )
    wall_west = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/WallWest",
        spawn=sim_utils.CuboidCfg(
            size=(0.1, 6.0, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-3.0, 0.0, 0.25)),
    )

    # Pillars (interior obstacles)
    pillar_a = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarA",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.3, 0.3)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(1.0, 1.0, 0.25)),
    )
    pillar_b = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarB",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.3, 0.3)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-1.0, -0.5, 0.25)),
    )
    pillar_c = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarC",
        spawn=sim_utils.CylinderCfg(
            radius=0.2,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.3, 0.3, 0.8)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.5, -1.5, 0.25)),
    )

    # Extra pillars to make the maze more complex
    pillar_d = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarD",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.2, 0.7, 0.7)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-2.0, 1.5, 0.25)),
    )
    pillar_e = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarE",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.7, 0.2)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(2.0, -1.2, 0.25)),
    )
    pillar_f = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarF",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.4, 0.8, 0.4)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 2.2, 0.25)),
    )
    pillar_g = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PillarG",
        spawn=sim_utils.CylinderCfg(
            radius=0.15,
            height=0.5,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.4, 0.6)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-2.5, -2.0, 0.25)),
    )

    # Inner wall segment (partial barrier)
    inner_wall = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/InnerWall",
        spawn=sim_utils.CuboidCfg(
            size=(2.0, 0.1, 0.5),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.5, 0.5, 0.5)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-0.5, 1.0, 0.25)),
    )

    # -- Simple dynamic obstacles (physics-driven) ----------------------------
    # These rigid bodies are given random linear velocities at reset to act as
    # moving obstacles inside the existing 6x6 m arena.
    dyn_obstacle_1: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle1",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.5, 0.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(1.5, 0.0, 0.15),
            lin_vel=(0.3, 0.2, 0.0),
        ),
    )
    dyn_obstacle_2: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle2",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.8, 0.0)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-1.5, 0.0, 0.15),
            lin_vel=(-0.3, -0.2, 0.0),
        ),
    )
    dyn_obstacle_3: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle3",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.4, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.0, 1.5, 0.15),
            lin_vel=(0.2, -0.3, 0.0),
        ),
    )
    dyn_obstacle_4: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle4",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.9, 0.6, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.0, -1.5, 0.15),
            lin_vel=(-0.2, 0.3, 0.0),
        ),
    )
    dyn_obstacle_5: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle5",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.3, 0.1)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(2.0, 1.0, 0.15),
            lin_vel=(0.25, -0.25, 0.0),
        ),
    )
    dyn_obstacle_6: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle6",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.7, 0.5, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-2.0, -1.0, 0.15),
            lin_vel=(-0.25, 0.25, 0.0),
        ),
    )
    dyn_obstacle_7: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle7",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.4, 0.3)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(2.5, -0.5, 0.15),
            lin_vel=(-0.3, 0.15, 0.0),
        ),
    )
    dyn_obstacle_8: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle8",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.8, 0.7, 0.3)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-2.5, 0.5, 0.15),
            lin_vel=(0.3, -0.15, 0.0),
        ),
    )
    dyn_obstacle_9: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle9",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.9, 0.5, 0.4)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.5, 0.5, 0.15),
            lin_vel=(0.2, 0.2, 0.0),
        ),
    )
    dyn_obstacle_10: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/DynObstacle10",
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.25),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_linear_velocity=2.0,
                max_angular_velocity=0.0,
                disable_gravity=True,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.6, 0.6, 0.2)),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(-0.5, -0.5, 0.15),
            lin_vel=(-0.2, -0.2, 0.0),
        ),
    )

    # -- Sensors -------------------------------------------------------------
    # 2-D LiDAR (360° single-beam) — debug_vis=True renders a dense red spray
    # of hit points so LiDAR coverage is clearly visible in the viewport.
    lidar = MultiMeshRayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/a__namespace_base_link",
        update_period=1.0 / 30.0,
        offset=MultiMeshRayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 0.172)),  # LDS mount height
        mesh_prim_paths=[
            "/World/ground",
            "{ENV_REGEX_NS}/WallNorth",
            "{ENV_REGEX_NS}/WallSouth",
            "{ENV_REGEX_NS}/WallEast",
            "{ENV_REGEX_NS}/WallWest",
            "{ENV_REGEX_NS}/PillarA",
            "{ENV_REGEX_NS}/PillarB",
            "{ENV_REGEX_NS}/PillarC",
            "{ENV_REGEX_NS}/PillarD",
            "{ENV_REGEX_NS}/PillarE",
            "{ENV_REGEX_NS}/PillarF",
            "{ENV_REGEX_NS}/PillarG",
            "{ENV_REGEX_NS}/InnerWall",
            "{ENV_REGEX_NS}/DynObstacle1",
            "{ENV_REGEX_NS}/DynObstacle2",
            "{ENV_REGEX_NS}/DynObstacle3",
            "{ENV_REGEX_NS}/DynObstacle4",
            "{ENV_REGEX_NS}/DynObstacle5",
            "{ENV_REGEX_NS}/DynObstacle6",
            "{ENV_REGEX_NS}/DynObstacle7",
            "{ENV_REGEX_NS}/DynObstacle8",
            "{ENV_REGEX_NS}/DynObstacle9",
            "{ENV_REGEX_NS}/DynObstacle10",
        ],
        pattern_cfg=LidarPatternCfg(
            channels=1,
            vertical_fov_range=(0.0, 0.0),
            horizontal_fov_range=(0.0, 360.0),
            # Higher angular resolution for a denser 360° LiDAR spray.
            horizontal_res=5.0,
        ),
        max_distance=3.5,  # TurtleBot3 LDS-01 max range
        # Enable per-hit spheres so the LiDAR spray is visible in the viewport.
        debug_vis=True,
    )

    # Contact sensor on robot base
    contact_sensor = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/a__namespace_base_link",
        update_period=0.0,  # every sim step
    )


# ============================================================================
# Actions
# ============================================================================


@configclass
class Stage2ActionsCfg:
    # Constant forward velocity 0.50 m/s — policy only learns angular velocity.
    # Angular action range mirrors DQN's [-1.5, 1.5] rad/s.
    drive = DifferentialDriveActionCfg(
        asset_name="robot",
        left_joint_name="a__namespace_wheel_left_joint",
        right_joint_name="a__namespace_wheel_right_joint",
        wheel_radius=0.033,
        track_width=0.16,
        # maps [-1, 1] → [-0.7, 0.7] rad/s (angular only)
        # very gentle turns to avoid overshoot / backwards drift
        scale=(0.7,),
        offset=(0.0,),
        fixed_linear_vel=0.50,
        # smooth_alpha closer to 0 simulates inertia and smoother acceleration.
        smooth_alpha=0.1,
    )


# ============================================================================
# Observations
# ============================================================================


@configclass
class Stage2ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        # --- DQN-inspired compact state (28 dimensions total) ---
        # Goal information (2 values)
        heading = ObsTerm(func=obs_terms.heading_to_goal)        # (N,1) angle to goal
        distance = ObsTerm(func=obs_terms.distance_to_goal)      # (N,1) distance to goal

        # Obstacle information (2 values — mirrors DQN's obstacle_min_range + obstacle_angle)
        obs_min_range = ObsTerm(
            func=obs_terms.obstacle_min_range,
            params={"sensor_cfg": SceneEntityCfg("lidar"), "max_distance": 3.5},
        )
        obs_angle = ObsTerm(
            func=obs_terms.obstacle_angle,
            params={
                "sensor_cfg": SceneEntityCfg("lidar"),
                "asset_cfg": SceneEntityCfg("robot"),
            },
        )

        # 2-D LiDAR ranges — 24 rays at 15° resolution (24 values)
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
class Stage2RewardsCfg:
    # Dense goal-distance shaping (disabled to mirror DQN rewards).
    goal_distance = RewTerm(
        func=rew_terms.goal_distance_reward,
        weight=0.0,
    )
    # Positive: Goal Reached +100 — awarded when within 20 cm of target.
    goal_reached = RewTerm(
        func=rew_terms.goal_reached_bonus,
        weight=100.0,
        params={"threshold": 0.2},  # 20 cm
    )
    # Negative: Collision -110 — slightly stronger terminal penalty for failure.
    collision = RewTerm(
        func=rew_terms.collision_penalty,
        weight=-110.0,
        params={"sensor_cfg": SceneEntityCfg("contact_sensor"), "threshold": 0.5},
    )
    # Distance progress shaping — gives the robot a "scent" to follow.
    distance_progress = RewTerm(
        func=rew_terms.distance_progress_reward,
        weight=50.0,
    )
    # Positive: Heading Alignment — kept low so it doesn't just spin in place.
    heading = RewTerm(
        func=rew_terms.heading_reward,
        weight=1.0,
    )
    # Per-step time penalty (~ -0.001) to encourage faster completion.
    time_penalty = RewTerm(func=rew_terms.time_step_penalty, weight=-0.001)
    # Penalize rapid changes in steering (discourage twitchy actions).
    action_rate = RewTerm(
        func=rew_terms.action_rate_penalty,
        weight=-0.1,
    )
    # Penalize excessive spinning (large yaw rates).
    angular_vel = RewTerm(
        func=rew_terms.angular_velocity_penalty,
        weight=-0.5,
    )


# ============================================================================
# Terminations
# ============================================================================


@configclass
class Stage2TerminationsCfg:
    time_out = DoneTerm(func=time_out, time_out=True)
    # Robot reached goal — restart at new random position
    goal_reached = DoneTerm(
        func=term_terms.goal_reached,
        params={"threshold": 0.2},   # 0.2m — matches DQN's goal threshold
    )
    # Robot hit an obstacle — restart immediately (DQN behaviour)
    collision = DoneTerm(
        func=term_terms.collision_with_obstacle,
        params={"sensor_cfg": SceneEntityCfg("contact_sensor"), "threshold": 0.5},
    )
    robot_flipped = DoneTerm(
        func=term_terms.robot_flipped,
        params={"limit_angle": 0.8},
    )
    out_of_bounds = DoneTerm(
        func=term_terms.out_of_bounds,
        params={"x_bounds": (-3.5, 3.5), "y_bounds": (-3.5, 3.5)},
    )


# ============================================================================
# Events (resets & goal randomisation)
# ============================================================================


@configclass
class Stage2EventsCfg:
    reset_robot = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            # Always reset the robot back to the initial position at the origin.
            # z is taken from the robot's default root state (typically ~0.05 m).
            "pose_range": {"x": (0.0, 0.0), "y": (0.0, 0.0), "yaw": (0.0, 0.0)},
            "velocity_range": {},
        },
    )
    # Resample navigation goal + update green marker on every episode reset.
    reset_goal = EventTerm(
        func=sample_goals_and_update_marker_for_envs,
        mode="reset",
        params={},
    )

    # Randomise positions and linear velocities of the dynamic obstacles on
    # every episode reset so they move differently each rollout.
    reset_dyn_obstacle_1 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_1"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_2 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_2"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_3 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_3"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_4 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_4"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_5 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_5"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_6 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_6"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_7 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_7"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_8 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_8"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_9 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_9"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )
    reset_dyn_obstacle_10 = EventTerm(
        func=lab_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("dyn_obstacle_10"),
            "pose_range": {"x": (-2.5, 2.5), "y": (-2.5, 2.5)},
            "velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)},
        },
    )


# ============================================================================
# Top-level environment config
# ============================================================================


@configclass
class Stage2EnvCfg(ManagerBasedRLEnvCfg):
    """Stage 2 — static obstacles, goal-reaching navigation."""

    scene: Stage2SceneCfg = Stage2SceneCfg(num_envs=512, env_spacing=8.0)
    actions: Stage2ActionsCfg = Stage2ActionsCfg()
    observations: Stage2ObservationsCfg = Stage2ObservationsCfg()
    rewards: Stage2RewardsCfg = Stage2RewardsCfg()
    terminations: Stage2TerminationsCfg = Stage2TerminationsCfg()
    events: Stage2EventsCfg = Stage2EventsCfg()

    # Goal position (sampled per env on reset) — stored as env attribute
    goal_pos: tuple[float, float] = (2.0, 0.0)  # default; overridden by reset logic

    def __post_init__(self) -> None:
        self.decimation = 4
        # DQN uses max_step=800; at 120Hz/4 decimation = 30 policy steps/s
        # → 800 steps = ~26.6s per episode
        self.episode_length_s = 26.6
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
