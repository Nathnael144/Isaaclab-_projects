# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

"""Humanoid G1 warehouse pick-and-place environment configuration.

A Unitree G1 humanoid robot with **fixed base** in a warehouse environment
picks up a box from a nearby table and places it on a second table.

The robot uses:
- Joint-position control for the upper body (waist + arms)
- Binary open/close control for the hand fingers (inspired by hands.py demo
  which uses ``soft_joint_pos_limits`` to toggle between open and closed states)

The base is fixed so the robot does not need to balance, and the task is focused
purely on reaching, grasping, lifting, and placing.
"""

from __future__ import annotations

import isaaclab.envs.mdp as base_mdp
import isaaclab.envs.mdp.rewards as base_rew
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs.mdp.actions.actions_cfg import (
    BinaryJointPositionActionCfg,
    JointPositionActionCfg,
)
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from isaaclab_assets.robots.unitree import G1_29DOF_CFG

from . import mdp

# ── Scene constants ───────────────────────────────────────────────────────────

TABLE_HEIGHT = 0.80  # approximate packing-table surface height
BOX_SIZE = (0.12, 0.08, 0.08)  # small box the robot can grasp
BOX_MASS = 0.2  # 200 g – light enough for the hand to grip


# ==============================================================================
# Scene
# ==============================================================================


@configclass
class WarehousePickPlaceSceneCfg(InteractiveSceneCfg):
    """Warehouse scene: fixed-base G1 robot, pick table, place table, box, goal."""

    # ── Robot ─────────────────────────────────────────────────────────────────
    robot: ArticulationCfg = G1_29DOF_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot",
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            rot=(1.0, 0.0, 0.0, 0.0),
            joint_pos={
                # Arms: reach-ready pose
                "left_shoulder_pitch_joint": 0.3,
                "left_shoulder_roll_joint": 0.2,
                "left_shoulder_yaw_joint": 0.0,
                "left_elbow_joint": 0.6,
                "left_wrist_.*_joint": 0.0,
                "right_shoulder_pitch_joint": 0.3,
                "right_shoulder_roll_joint": -0.2,
                "right_shoulder_yaw_joint": 0.0,
                "right_elbow_joint": 0.6,
                "right_wrist_.*_joint": 0.0,
                # Waist neutral
                "waist_.*_joint": 0.0,
                # Legs standing (fixed, won't move)
                ".*_hip_pitch_joint": -0.2,
                ".*_hip_roll_joint": 0.0,
                ".*_hip_yaw_joint": 0.0,
                ".*_knee_joint": 0.4,
                ".*_ankle_pitch_joint": -0.2,
                ".*_ankle_roll_joint": 0.0,
                # Fingers open
                ".*_hand_index_.*": 0.0,
                ".*_hand_middle_.*": 0.0,
                ".*_hand_thumb_.*": 0.0,
            },
            joint_vel={".*": 0.0},
        ),
    )

    def __post_init__(self):
        # Fixed base – no balancing needed
        self.robot.spawn.articulation_props.fix_root_link = True
        # Enable contact sensors on robot for grasp detection
        self.robot.spawn.activate_contact_sensors = True

    # ── Pick Table (right in front of robot) ──────────────────────────────────
    pick_table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PickTable",
        spawn=sim_utils.CuboidCfg(
            size=(0.6, 0.8, TABLE_HEIGHT),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=True),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.45, 0.35, 0.25)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.50, 0.0, TABLE_HEIGHT / 2),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # ── Place Table (to the side, within arm reach) ───────────────────────────
    place_table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/PlaceTable",
        spawn=sim_utils.CuboidCfg(
            size=(0.6, 0.8, TABLE_HEIGHT),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=True),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.3, 0.3, 0.5)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.50, 0.55, TABLE_HEIGHT / 2),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )

    # ── Box (object to pick and place) ────────────────────────────────────────
    box = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Box",
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.45, 0.0, TABLE_HEIGHT + BOX_SIZE[2] / 2 + 0.01),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
        spawn=sim_utils.CuboidCfg(
            size=BOX_SIZE,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_depenetration_velocity=2.0,
                solver_position_iteration_count=16,
                solver_velocity_iteration_count=4,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=BOX_MASS),
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=2.5,
                dynamic_friction=2.0,
                restitution=0.0,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                contact_offset=0.005,
                rest_offset=0.0,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.85, 0.2, 0.15)),
        ),
    )

    # ── Goal marker (kinematic, no collision) ─────────────────────────────────
    goal = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Goal",
        init_state=RigidObjectCfg.InitialStateCfg(
            pos=(0.50, 0.55, TABLE_HEIGHT + 0.02),
            rot=(1.0, 0.0, 0.0, 0.0),
        ),
        spawn=sim_utils.CuboidCfg(
            size=(0.15, 0.10, 0.02),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.1, 0.9, 0.1), opacity=0.6),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=False),
        ),
    )

    # ── Lighting ──────────────────────────────────────────────────────────────
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=2500.0),
    )

    # ── Contact sensors on right hand ─────────────────────────────────────────
    hand_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_wrist_yaw_link",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
        track_friction_forces=True,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Box"],
    )


# ==============================================================================
# Actions
# ==============================================================================


@configclass
class ActionsCfg:
    """Actions for fixed-base G1 manipulation.

    Three action groups:
    - upper_body: waist + arms (joint position control)
    - right_hand_grasp: binary open/close for right hand fingers
      (inspired by hands.py soft_joint_pos_limits toggling)
    - left_hand_grasp: binary open/close for left hand fingers
    """

    upper_body = JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            "waist_.*_joint",
            "left_shoulder_.*_joint",
            "left_elbow_joint",
            "left_wrist_.*_joint",
            "right_shoulder_.*_joint",
            "right_elbow_joint",
            "right_wrist_.*_joint",
        ],
        scale=0.25,
        use_default_offset=True,
    )

    # Binary grasp for right hand fingers: open (0.0) ↔ close (limits)
    # Inspired by hands.py which toggles between soft_joint_pos_limits[0] (close)
    # and soft_joint_pos_limits[1] (open)
    right_hand_grasp = BinaryJointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            "right_hand_index_.*",
            "right_hand_middle_.*",
            "right_hand_thumb_.*",
        ],
        open_command_expr={
            "right_hand_index_.*": 0.0,
            "right_hand_middle_.*": 0.0,
            "right_hand_thumb_.*": 0.0,
        },
        close_command_expr={
            "right_hand_index_.*": 1.0,
            "right_hand_middle_.*": 1.0,
            "right_hand_thumb_.*": 1.0,
        },
    )

    left_hand_grasp = BinaryJointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            "left_hand_index_.*",
            "left_hand_middle_.*",
            "left_hand_thumb_.*",
        ],
        open_command_expr={
            "left_hand_index_.*": 0.0,
            "left_hand_middle_.*": 0.0,
            "left_hand_thumb_.*": 0.0,
        },
        close_command_expr={
            "left_hand_index_.*": 1.0,
            "left_hand_middle_.*": 1.0,
            "left_hand_thumb_.*": 1.0,
        },
    )


# ==============================================================================
# Observations
# ==============================================================================


@configclass
class ObservationsCfg:
    """Observation specifications for the fixed-base pick-and-place task."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for the policy."""

        # Last actions
        actions = ObsTerm(func=base_mdp.last_action)

        # Upper body joint state (waist + arms)
        robot_joint_pos = ObsTerm(func=base_mdp.joint_pos_rel, params={"asset_cfg": SceneEntityCfg("robot")})
        robot_joint_vel = ObsTerm(
            func=base_mdp.joint_vel_rel, params={"asset_cfg": SceneEntityCfg("robot")}, scale=0.1
        )

        # Right hand end-effector
        right_eef_pos = ObsTerm(
            func=mdp.eef_pos_w,
            params={"asset_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"])},
        )

        # Left hand end-effector
        left_eef_pos = ObsTerm(
            func=mdp.eef_pos_w,
            params={"asset_cfg": SceneEntityCfg("robot", body_names=["left_wrist_yaw_link"])},
        )

        # Object state
        box_pos = ObsTerm(func=base_mdp.root_pos_w, params={"asset_cfg": SceneEntityCfg("box")})
        box_rot = ObsTerm(func=base_mdp.root_quat_w, params={"asset_cfg": SceneEntityCfg("box")})

        # Relational observations (hand → box, box → goal)
        eef_to_box = ObsTerm(
            func=mdp.eef_to_object_vec,
            params={
                "eef_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"]),
                "object_cfg": SceneEntityCfg("box"),
            },
        )
        box_to_goal = ObsTerm(
            func=mdp.object_to_goal_vec,
            params={
                "object_cfg": SceneEntityCfg("box"),
                "goal_cfg": SceneEntityCfg("goal"),
            },
        )

        # Goal position
        goal_pos = ObsTerm(func=base_mdp.root_pos_w, params={"asset_cfg": SceneEntityCfg("goal")})

        # Grasp state: contact force magnitude (tells policy if it's gripping)
        grasp_contact_force = ObsTerm(
            func=mdp.contact_force_obs,
            params={"sensor_cfg": SceneEntityCfg("hand_contact")},
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


# ==============================================================================
# Rewards
# ==============================================================================


@configclass
class RewardsCfg:
    """Reward terms for fixed-base pick-and-place.

    Reward structure (curriculum-like):
    1. Reach: guide hand to object
    2. Grasp: reward contact forces on fingers + finger closure
    3. Lift: reward object height
    4. Place: reward object near goal
    5. Regularization: smooth actions
    """

    # ── Phase 1: Reach ────────────────────────────────────────────────────────
    reach_object = RewTerm(
        func=mdp.hand_to_object_distance_tanh,
        weight=2.0,
        params={
            "robot_cfg": SceneEntityCfg("robot"),
            "object_cfg": SceneEntityCfg("box"),
            "hand_body_name": "right_wrist_yaw_link",
            "std": 0.15,
        },
    )

    # ── Phase 2: Grasp ────────────────────────────────────────────────────────
    # Reward contact force between hand and box
    grasp_contact = RewTerm(
        func=mdp.contact_force_reward,
        weight=2.0,
        params={
            "sensor_cfg": SceneEntityCfg("hand_contact"),
            "min_force": 1.0,
            "max_force": 50.0,
        },
    )

    # Reward fingers closing when near the object
    finger_close_reward = RewTerm(
        func=mdp.finger_close_near_object,
        weight=1.0,
        params={
            "robot_cfg": SceneEntityCfg("robot"),
            "object_cfg": SceneEntityCfg("box"),
            "hand_body_name": "right_wrist_yaw_link",
            "finger_joint_names": ["right_hand_index_.*", "right_hand_middle_.*", "right_hand_thumb_.*"],
            "proximity_threshold": 0.15,
        },
    )

    # ── Phase 3: Lift ─────────────────────────────────────────────────────────
    lift_object = RewTerm(
        func=mdp.object_lifted_reward,
        weight=4.0,
        params={"object_cfg": SceneEntityCfg("box"), "min_height": TABLE_HEIGHT + 0.05},
    )

    # ── Phase 4: Place ────────────────────────────────────────────────────────
    object_to_goal = RewTerm(
        func=mdp.object_to_goal_distance_tanh,
        weight=5.0,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "goal_cfg": SceneEntityCfg("goal"),
            "std": 0.3,
        },
    )

    place_success = RewTerm(
        func=mdp.object_near_goal_and_slow,
        weight=15.0,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "goal_cfg": SceneEntityCfg("goal"),
            "dist_thresh": 0.15,
            "speed_thresh": 0.15,
        },
    )

    # ── Anti-drop ─────────────────────────────────────────────────────────────
    drop_penalty = RewTerm(
        func=mdp.DropPenaltyAfterContact,
        weight=-5.0,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "sensor_cfgs": [SceneEntityCfg("hand_contact")],
            "contact_force_threshold": 2.0,
            "drop_height_threshold": 0.08,
        },
    )

    # ── Regularization ────────────────────────────────────────────────────────
    action_rate = RewTerm(func=base_rew.action_rate_l2, weight=-2.0e-4)
    action_l2 = RewTerm(func=base_rew.action_l2, weight=-1.0e-4)

    # Alive bonus
    alive = RewTerm(func=base_mdp.is_alive, weight=0.05)


# ==============================================================================
# Terminations
# ==============================================================================


@configclass
class TerminationsCfg:
    """Termination conditions."""

    time_out = DoneTerm(func=base_mdp.time_out, time_out=True)

    # Success: object placed at goal
    success = DoneTerm(
        func=mdp.object_placed_on_goal,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "goal_cfg": SceneEntityCfg("goal"),
            "xy_threshold": 0.12,
            "z_range": (0.70, 0.90),
            "speed_threshold": 0.15,
        },
    )

    # Failure: object fell off
    object_dropped = DoneTerm(
        func=mdp.object_dropped,
        params={"object_cfg": SceneEntityCfg("box"), "min_height": -0.1},
    )


# ==============================================================================
# Events (Reset randomization)
# ==============================================================================


@configclass
class EventsCfg:
    """Randomization events for each episode reset."""

    reset_robot = EventTerm(
        func=base_mdp.reset_joints_by_scale,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "position_range": (0.95, 1.05),
            "velocity_range": (0.0, 0.0),
        },
    )

    reset_box = EventTerm(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("box"),
            "pose_range": {
                "x": (0.35, 0.55),
                "y": (-0.15, 0.15),
                "z": (TABLE_HEIGHT + BOX_SIZE[2] / 2 + 0.01, TABLE_HEIGHT + BOX_SIZE[2] / 2 + 0.01),
                "yaw": (-0.5, 0.5),
            },
            "velocity_range": {},
        },
    )

    reset_goal = EventTerm(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("goal"),
            "pose_range": {
                "x": (0.40, 0.60),
                "y": (0.40, 0.70),
                "z": (TABLE_HEIGHT + 0.02, TABLE_HEIGHT + 0.02),
            },
            "velocity_range": {},
        },
    )


# ==============================================================================
# Environment Configuration
# ==============================================================================


@configclass
class HumanoidWarehousePickPlaceEnvCfg(ManagerBasedRLEnvCfg):
    """Manager-based RL environment: fixed-base G1 pick-and-place in warehouse."""

    scene: WarehousePickPlaceSceneCfg = WarehousePickPlaceSceneCfg(
        num_envs=256,
        env_spacing=5.0,
        replicate_physics=True,
    )

    actions: ActionsCfg = ActionsCfg()
    observations: ObservationsCfg = ObservationsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventsCfg = EventsCfg()

    commands = None
    curriculum = None

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 15.0
        self.sim.dt = 1.0 / 200.0
        self.sim.render_interval = 2
        self.sim.physx.gpu_collision_stack_size = 2**28  # Warehouse contact-rich scene

        # Warehouse USD as the environment ground/backdrop
        self.scene.terrain = TerrainImporterCfg(
            prim_path="/World/ground",
            terrain_type="usd",
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Environments/Simple_Warehouse/warehouse.usd",
        )

        # Viewer camera – close-up of robot and tables
        self.viewer.eye = (1.5, -0.8, 1.5)
        self.viewer.lookat = (0.4, 0.2, 0.85)
