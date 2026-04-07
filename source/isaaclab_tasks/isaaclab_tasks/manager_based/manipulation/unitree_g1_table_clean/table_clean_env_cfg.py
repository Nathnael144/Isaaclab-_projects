from __future__ import annotations

import isaaclab.envs.mdp as base_mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import ActionTermCfg as ActionTerm
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim.schemas.schemas_cfg import MassPropertiesCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import GroundPlaneCfg, UsdFileCfg
from isaaclab.sim.spawners.materials.physics_materials_cfg import RigidBodyMaterialCfg
from isaaclab.sim.spawners.shapes.shapes_cfg import CuboidCfg
from isaaclab.sim.spawners.shapes.shapes_cfg import SphereCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from isaaclab_assets.robots.unitree import G1_INSPIRE_FTP_CFG

from . import mdp


TABLE_HEIGHT_W = 0.75
TARGET_RADIUS = 0.015
SPONGE_SIZE = (0.06, 0.03, 0.02)


@configclass
class UnitreeG1TableCleanSceneCfg(InteractiveSceneCfg):
    """Scene with fixed-base G1 and a tabletop target marker."""

    # Table (use a known-good asset used across IsaacLab tasks)
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=UsdFileCfg(
            usd_path=f"{ISAAC_NUCLEUS_DIR}/Props/PackingTable/packing_table.usd",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.55, 0.0), rot=(1.0, 0.0, 0.0, 0.0)),
    )

    # Sponge tool (kinematic). We attach it to the right wrist each step via an interval event.
    sponge = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Sponge",
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.30, 0.30, TABLE_HEIGHT_W + 0.05), rot=(1.0, 0.0, 0.0, 0.0)),
        spawn=CuboidCfg(
            size=SPONGE_SIZE,
            # Dynamic rigid body: fingers can grasp it with contact + friction.
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=False,
                disable_gravity=False,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=2,
                max_depenetration_velocity=2.0,
            ),
            mass_props=MassPropertiesCfg(mass=0.02),
            collision_props=sim_utils.CollisionPropertiesCfg(contact_offset=0.005, rest_offset=0.0),
            physics_material=RigidBodyMaterialCfg(
                static_friction=2.0,
                dynamic_friction=1.5,
                restitution=0.0,
                friction_combine_mode="max",
                restitution_combine_mode="min",
            ),
        ),
    )

    # Target marker (small sphere) randomized on reset.
    target = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Target",
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.55, 0.0, TABLE_HEIGHT_W + 0.02), rot=(1.0, 0.0, 0.0, 0.0)),
        spawn=SphereCfg(
            radius=TARGET_RADIUS,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True),
            mass_props=MassPropertiesCfg(mass=0.01),
        ),
    )

    # Robot
    robot: ArticulationCfg = G1_INSPIRE_FTP_CFG.replace(
        prim_path="{ENV_REGEX_NS}/Robot",
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.95),
            rot=(0.7071, 0.0, 0.0, 0.7071),
            joint_pos={
                # arms/waist
                "right_shoulder_.*_joint": 0.0,
                "right_elbow_joint": 0.0,
                "right_wrist_.*_joint": 0.0,
                "left_shoulder_.*_joint": 0.0,
                "left_elbow_joint": 0.0,
                "left_wrist_.*_joint": 0.0,
                "waist_.*": 0.0,
                # legs fixed at zero
                ".*_hip_.*": 0.0,
                ".*_knee_.*": 0.0,
                ".*_ankle_.*": 0.0,
                # hands open (keep patterns non-overlapping)
                "L_.*_joint": 0.0,
                "R_.*_joint": 0.0,
            },
            joint_vel={".*": 0.0},
        ),
    )

    # Ground plane + lights
    ground = AssetBaseCfg(prim_path="/World/GroundPlane", spawn=GroundPlaneCfg())
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(color=(0.75, 0.75, 0.75), intensity=3000.0),
    )

    def __post_init__(self):
        self.robot.spawn.articulation_props.fix_root_link = True


@configclass
class ActionsCfg:
    """Action specifications."""

    # Joint position control for a simple first training baseline.
    # (Right arm + waist) action is delta joint position scaled and offset by default joint pose.
    arm_joint_pos: ActionTerm = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            "right_shoulder_.*_joint",
            "right_elbow_joint",
            "right_wrist_.*_joint",
            "waist_.*_joint",
        ],
        scale=0.25,
        use_default_offset=True,
    )

    # Finger joints (Inspire hand). This enables real finger articulation.
    hand_joint_pos: ActionTerm = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[
            # Inspire hand joint naming used by the G1 Inspire USD
            "L_.*_joint",
            "R_.*_joint",
        ],
        scale=0.6,
        use_default_offset=True,
    )


@configclass
class ObservationsCfg:
    """Observation specifications."""

    @configclass
    class PolicyCfg(ObsGroup):
        actions = ObsTerm(func=mdp.last_action)

        robot_joint_pos = ObsTerm(func=base_mdp.joint_pos, params={"asset_cfg": SceneEntityCfg("robot")})
        robot_joint_vel = ObsTerm(func=base_mdp.joint_vel, params={"asset_cfg": SceneEntityCfg("robot")})

        right_wrist_pos = ObsTerm(func=mdp.eef_pos_w, params={"asset_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"])})
        target_pos = ObsTerm(func=mdp.target_pos_w, params={"asset_cfg": SceneEntityCfg("target")})

        eef_to_target = ObsTerm(
            func=mdp.eef_to_target_vec_w,
            params={
                "eef_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"]),
                "target_cfg": SceneEntityCfg("target"),
            },
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


@configclass
class RewardsCfg:
    """Reward terms."""

    track_target = RewTerm(
        func=mdp.eef_target_distance_tanh,
        weight=2.0,
        params={
            "std": 0.10,
            "eef_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"]),
            "target_cfg": SceneEntityCfg("target"),
        },
    )

    stay_on_plane = RewTerm(
        func=mdp.eef_height_error_abs,
        weight=-0.5,
        params={"target_height": TABLE_HEIGHT_W + 0.02, "eef_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"])},
    )

    action_rate = RewTerm(func=mdp.action_rate_l2, weight=-1.0e-4)


@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=mdp.time_out, time_out=True)
    success = DoneTerm(
        func=mdp.eef_close_to_target,
        params={
            "threshold": 0.04,
            "eef_cfg": SceneEntityCfg("robot", body_names=["right_wrist_yaw_link"]),
            "target_cfg": SceneEntityCfg("target"),
        },
    )


@configclass
class EventCfg:
    reset_robot = EventTerm(
        func=mdp.reset_joints_by_scale,
        mode="reset",
        params={"asset_cfg": SceneEntityCfg("robot"), "position_range": (0.95, 1.05), "velocity_range": (0.0, 0.0)},
    )

    reset_target = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("target"),
            "pose_range": {
                "x": [0.45, 0.70],
                "y": [-0.20, 0.20],
                "z": [TABLE_HEIGHT_W + 0.02, TABLE_HEIGHT_W + 0.02],
            },
            "velocity_range": {},
        },
    )

    reset_sponge = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("sponge"),
            "pose_range": {
                "x": [0.35, 0.55],
                "y": [0.35, 0.55],
                "z": [TABLE_HEIGHT_W + 0.05, TABLE_HEIGHT_W + 0.05],
                "roll": [-0.2, 0.2],
                "pitch": [-0.2, 0.2],
                "yaw": [-3.14, 3.14],
            },
            "velocity_range": {},
        },
    )


@configclass
class UnitreeG1TableCleanEnvCfg(ManagerBasedRLEnvCfg):
    """Manager-based RL environment for Unitree G1 table cleaning."""

    scene: UnitreeG1TableCleanSceneCfg = UnitreeG1TableCleanSceneCfg(num_envs=1024, env_spacing=2.5)

    observations: ObservationsCfg = ObservationsCfg()
    actions: ActionsCfg = ActionsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: EventCfg = EventCfg()

    commands = None
    curriculum = None

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 8.0
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
        self.viewer.eye = (2.5, 2.5, 1.8)

