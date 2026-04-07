# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause

import isaaclab.envs.mdp as base_mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
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

from isaaclab_tasks.manager_based.locomanipulation.pick_place.locomanipulation_g1_env_cfg import (
    ObservationsCfg as G1HierObservationsCfg,
)
from isaaclab_tasks.manager_based.locomanipulation.pick_place.locomanipulation_g1_env_cfg import (
    TerminationsCfg as G1HierTerminationsCfg,
)
from isaaclab.envs.mdp.actions.actions_cfg import JointPositionActionCfg
import isaaclab.envs.mdp.rewards as base_rew
from isaaclab_tasks.manager_based.locomanipulation.warehouse_box_arrange import mdp


@configclass
class WarehouseBoxArrangeSceneCfg(InteractiveSceneCfg):
    """Warehouse scene with a movable box and a goal marker."""

    # Mobile G1 robot is inherited via env cfg actions/observations; keep name "robot" consistent
    from isaaclab_assets.robots.unitree import G1_29DOF_CFG

    robot = G1_29DOF_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")

    def __post_init__(self):
        # Needed for ContactSensor to work on robot bodies
        self.robot.spawn.activate_contact_sensors = True

    # Box to pick/place (dynamic). Use a native cuboid spawner so it always has USD RigidBodyAPI.
    box = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Box",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[0.7, 0.0, 0.05], rot=[1.0, 0.0, 0.0, 0.0]),
        spawn=sim_utils.CuboidCfg(
            # Tuned: slightly smaller/lighter, higher friction, more solver iterations for stable grasping.
            size=(0.30, 0.20, 0.18),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                max_depenetration_velocity=2.0,
                solver_position_iteration_count=16,
                solver_velocity_iteration_count=4,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.6),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=2.0, dynamic_friction=1.6, restitution=0.0),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.72, 0.55, 0.35)),
        ),
    )

    # Goal marker (kinematic rigid object) so base_mdp.root_pos_w works (expects `.data`).
    goal = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Goal",
        init_state=RigidObjectCfg.InitialStateCfg(pos=[2.0, 0.5, 0.05], rot=[1.0, 0.0, 0.0, 0.0]),
        spawn=sim_utils.CuboidCfg(
            size=(0.25, 0.25, 0.05),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.1, 0.9, 0.1)),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            collision_props=sim_utils.CollisionPropertiesCfg(collision_enabled=False),
        ),
    )

    # Light (helps in warehouse USD)
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.9, 0.9, 0.9), intensity=2500.0),
    )

    # Contact sensor on right palm (for true contact grasp reward)
    hand_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_hand/right_hand_palm_link",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
        track_friction_forces=True,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Box"],
    )

    # Finger contact sensors (reward finger contacts, not just palm)
    thumb_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_hand/right_hand_thumb_1_link",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
        track_friction_forces=True,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Box"],
    )
    index_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_hand/right_hand_index_1_link",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
        track_friction_forces=True,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Box"],
    )
    middle_contact = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/right_hand/right_hand_middle_1_link",
        update_period=0.0,
        history_length=1,
        debug_vis=False,
        track_friction_forces=True,
        filter_prim_paths_expr=["{ENV_REGEX_NS}/Box"],
    )


@configclass
class ActionsCfg:
    """Hierarchical-ish control without IK (Hydra-safe).

    - lower_body_joint_pos: direct joint position targets for legs/hips (no external policy file)
    - upper_body_joint_pos: direct joint position targets for arms/waist/wrists
    - hand_joint_pos: direct joint position targets for finger joints (optional)
    """

    lower_body_joint_pos = JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            ".*_hip_.*_joint",
            ".*_knee_joint",
            ".*_ankle_.*_joint",
        ],
        scale=0.35,
        use_default_offset=True,
    )

    upper_body_joint_pos = JointPositionActionCfg(
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

    hand_joint_pos = JointPositionActionCfg(
        asset_name="robot",
        joint_names=[".*_hand.*"],
        scale=0.35,
        use_default_offset=True,
    )


@configclass
class RewardsCfg:
    """Reward terms for box arranging."""

    reach_box = RewTerm(
        func=mdp.hand_to_object_distance_tanh,
        weight=0.75,
        params={
            "robot_cfg": SceneEntityCfg("robot"),
            "object_cfg": SceneEntityCfg("box"),
            "hand_body_name": "right_wrist_yaw_link",
            "std": 0.35,
        },
    )

    lift_box = RewTerm(
        func=mdp.object_height_above_min,
        weight=0.5,
        params={"object_cfg": SceneEntityCfg("box"), "min_height": 0.25},
    )

    # Keep the box stable while manipulating
    box_speed_penalty = RewTerm(
        func=mdp.object_speed_l2,
        weight=-0.02,
        params={"object_cfg": SceneEntityCfg("box")},
    )
    box_ang_speed_penalty = RewTerm(
        func=mdp.object_angular_speed_l2,
        weight=-0.005,
        params={"object_cfg": SceneEntityCfg("box")},
    )

    grasp_palm_contact = RewTerm(
        func=mdp.contact_force_tanh,
        weight=0.25,
        params={"sensor_cfg": SceneEntityCfg("hand_contact"), "std": 50.0},
    )

    grasp_thumb_contact = RewTerm(
        func=mdp.contact_force_tanh,
        weight=0.35,
        params={"sensor_cfg": SceneEntityCfg("thumb_contact"), "std": 30.0},
    )
    grasp_index_contact = RewTerm(
        func=mdp.contact_force_tanh,
        weight=0.35,
        params={"sensor_cfg": SceneEntityCfg("index_contact"), "std": 30.0},
    )
    grasp_middle_contact = RewTerm(
        func=mdp.contact_force_tanh,
        weight=0.35,
        params={"sensor_cfg": SceneEntityCfg("middle_contact"), "std": 30.0},
    )

    drop_after_contact = RewTerm(
        func=mdp.DropPenaltyAfterContact,
        weight=-2.0,
        params={
            "box_cfg": SceneEntityCfg("box"),
            "sensor_cfgs": [
                SceneEntityCfg("hand_contact"),
                SceneEntityCfg("thumb_contact"),
                SceneEntityCfg("index_contact"),
                SceneEntityCfg("middle_contact"),
            ],
            "contact_force_threshold": 2.0,
            "drop_height_threshold": 0.08,
        },
    )

    # Dense "place" shaping: reward being near goal AND slow (avoid just throwing).
    place_near_goal_and_slow = RewTerm(
        func=mdp.object_near_goal_and_slow,
        weight=1.0,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "goal_cfg": SceneEntityCfg("goal"),
            "dist_thresh": 0.25,
            "speed_thresh": 0.25,
        },
    )

    box_to_goal = RewTerm(
        func=mdp.object_to_goal_distance_tanh,
        weight=2.0,
        params={
            "object_cfg": SceneEntityCfg("box"),
            "goal_cfg": SceneEntityCfg("goal"),
            "std": 0.75,
        },
    )

    # small time penalty
    alive = RewTerm(func=base_mdp.is_alive, weight=-0.01)

    # Regularize actions (dense shaping to reduce jitter)
    action_l2 = RewTerm(func=base_rew.action_l2, weight=-1.0e-4)
    action_rate_l2 = RewTerm(func=base_rew.action_rate_l2, weight=-2.0e-4)


@configclass
class TerminationsCfg(G1HierTerminationsCfg):
    """Termination terms for the MDP."""

    # keep time_out from parent; override success for this task
    success = DoneTerm(
        func=mdp.box_close_to_goal,
        params={"object_cfg": SceneEntityCfg("box"), "goal_cfg": SceneEntityCfg("goal"), "threshold": 0.25},
    )

    # allow dropping below floor-ish
    object_dropping = DoneTerm(
        func=base_mdp.root_height_below_minimum, params={"minimum_height": -0.2, "asset_cfg": SceneEntityCfg("box")}
    )


@configclass
class EventsCfg:
    """Reset randomization for box and robot pose."""

    reset_robot = EventTerm(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14)},
            "velocity_range": {},
        },
    )

    reset_box = EventTerm(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("box"),
            "pose_range": {"x": (0.5, 1.0), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14)},
            "velocity_range": {},
        },
    )


@configclass
class ObservationsCfg(G1HierObservationsCfg):
    @configclass
    class PolicyCfg(ObsGroup):
        actions = ObsTerm(func=base_mdp.last_action)

        robot_root_pos = ObsTerm(func=base_mdp.root_pos_w, params={"asset_cfg": SceneEntityCfg("robot")})
        robot_root_rot = ObsTerm(func=base_mdp.root_quat_w, params={"asset_cfg": SceneEntityCfg("robot")})

        box_pos = ObsTerm(func=base_mdp.root_pos_w, params={"asset_cfg": SceneEntityCfg("box")})
        box_rot = ObsTerm(func=base_mdp.root_quat_w, params={"asset_cfg": SceneEntityCfg("box")})

        goal_pos = ObsTerm(func=base_mdp.root_pos_w, params={"asset_cfg": SceneEntityCfg("goal")})

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()
    lower_body_policy = None


@configclass
class WarehouseBoxArrangeG1EnvCfg(ManagerBasedRLEnvCfg):
    """Mobile G1 box arrangement in a warehouse USD scene with hierarchical control."""

    scene: WarehouseBoxArrangeSceneCfg = WarehouseBoxArrangeSceneCfg(num_envs=64, env_spacing=5.0, replicate_physics=True)

    actions: ActionsCfg = ActionsCfg()
    observations: ObservationsCfg = ObservationsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventsCfg = EventsCfg()

    commands = None
    curriculum = None

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 25.0

        self.sim.dt = 1 / 200
        self.sim.render_interval = 2

        # Load prebuilt USD warehouse as terrain/environment
        self.scene.terrain = TerrainImporterCfg(
            prim_path="/World/ground",
            terrain_type="usd",
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Environments/Simple_Warehouse/warehouse.usd",
        )

