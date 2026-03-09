# turtlebot3_env_cfg.py
# Isaac Lab environment config for TurtleBot3 navigation with LiDAR

from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import (
    ObservationGroupCfg as ObsGroup,
    ObservationTermCfg as ObsTerm,
    RewardTermCfg as RewTerm,
    TerminationTermCfg as DoneTerm,
    SceneEntityCfg,
)
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.sensors.ray_caster import MultiMeshRayCasterCfg
from isaaclab.sensors.ray_caster.patterns import LidarPatternCfg
from isaaclab.utils import configclass
import math

from turtlebot3_mdp import (
    base_linear_velocity_xy,
    base_angular_velocity_z,
    goal_position_in_robot_frame,
    lidar_scan,
    goal_distance_reward,
    goal_reached_bonus,
    collision_penalty,
    angular_velocity_penalty,
    time_out_termination,
    goal_reached_termination,
)

# --- Scene config ---
@configclass
class TurtleBot3SceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=dict(type="GroundPlane", size=(100.0, 100.0)),
    )
    robot = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
        usd_path="turtlebot3_isaaclab/assets/turtlebot3_burger.usd",
        # Set initial pose if needed
    )
    # 2D LiDAR
    lidar = MultiMeshRayCasterCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base_link",
        update_period=1.0 / 30.0,
        offset=MultiMeshRayCasterCfg.OffsetCfg(pos=(0.0, 0.0, 0.172)),
        mesh_prim_paths=["/World/ground"],
        pattern_cfg=LidarPatternCfg(
            channels=1,
            vertical_fov_range=(0.0, 0.0),
            horizontal_fov_range=(0.0, 360.0),
            horizontal_res=2.0,  # 180 rays
        ),
        max_distance=3.5,
    )
    contact_sensor = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/Robot/base_link",
        update_period=0.0,
    )

# --- Actions config ---
@configclass
class TurtleBot3ActionsCfg:
    # Differential drive: [linear_vel, angular_vel]
    pass  # Use default action manager for continuous actions

# --- Observations config ---
@configclass
class TurtleBot3ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        base_lin_vel = ObsTerm(func=base_linear_velocity_xy)
        base_ang_vel = ObsTerm(func=base_angular_velocity_z)
        goal_body = ObsTerm(func=goal_position_in_robot_frame)
        lidar = ObsTerm(func=lidar_scan, params={"sensor_cfg": SceneEntityCfg("lidar")})
        def __post_init__(self):
            self.concatenate_terms = True
    policy: PolicyCfg = PolicyCfg()

# --- Rewards config ---
@configclass
class TurtleBot3RewardsCfg:
    goal_distance = RewTerm(func=goal_distance_reward, weight=2.0)
    goal_reached = RewTerm(func=goal_reached_bonus, weight=10.0)
    collision = RewTerm(func=collision_penalty, weight=-5.0, params={"sensor_cfg": SceneEntityCfg("contact_sensor")})
    ang_vel = RewTerm(func=angular_velocity_penalty, weight=-0.01)

# --- Terminations config ---
@configclass
class TurtleBot3TerminationsCfg:
    time_out = DoneTerm(func=time_out_termination, time_out=True)
    goal_reached = DoneTerm(func=goal_reached_termination, params={"threshold": 0.25})

# --- Top-level environment config ---
@configclass
class TurtleBot3EnvCfg(ManagerBasedRLEnvCfg):
    scene: TurtleBot3SceneCfg = TurtleBot3SceneCfg(num_envs=128, env_spacing=8.0)
    actions: TurtleBot3ActionsCfg = TurtleBot3ActionsCfg()
    observations: TurtleBot3ObservationsCfg = TurtleBot3ObservationsCfg()
    rewards: TurtleBot3RewardsCfg = TurtleBot3RewardsCfg()
    terminations: TurtleBot3TerminationsCfg = TurtleBot3TerminationsCfg()
    # Goal position (sampled per env on reset)
    goal_pos: tuple[float, float] = (2.0, 0.0)
    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 30.0
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
