# turtlebot3_mdp.py
# MDP terms for TurtleBot3 navigation

import torch
from isaaclab.managers import SceneEntityCfg

# --- Observations ---
def base_linear_velocity_xy(env, asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    return asset.data.root_lin_vel_b[:, :2]

def base_angular_velocity_z(env, asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    return asset.data.root_ang_vel_b[:, 2:3]

def goal_position_in_robot_frame(env, goal_pos_key="goal_pos", asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    if hasattr(env, goal_pos_key):
        goal_w = getattr(env, goal_pos_key)
    else:
        goal_w = env.scene.env_origins[:, :2] + torch.tensor([[2.0, 0.0]], device=env.device)
    robot_xy = asset.data.root_pos_w[:, :2]
    diff = goal_w[:, :2] - robot_xy
    quat = asset.data.root_quat_w
    siny_cosp = 2.0 * (quat[:, 0] * quat[:, 3] + quat[:, 1] * quat[:, 2])
    cosy_cosp = 1.0 - 2.0 * (quat[:, 2] ** 2 + quat[:, 3] ** 2)
    yaw = torch.atan2(siny_cosp, cosy_cosp)
    cos_yaw = torch.cos(-yaw)
    sin_yaw = torch.sin(-yaw)
    goal_body_x = diff[:, 0] * cos_yaw - diff[:, 1] * sin_yaw
    goal_body_y = diff[:, 0] * sin_yaw + diff[:, 1] * cos_yaw
    return torch.stack([goal_body_x, goal_body_y], dim=-1)

def lidar_scan(env, sensor_cfg=SceneEntityCfg("lidar")):
    sensor = env.scene[sensor_cfg.name]
    return sensor.data.ranges  # (N, num_rays)

# --- Rewards ---
def goal_distance_reward(env, std=1.0, goal_pos_key="goal_pos", asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    goal_w = getattr(env, goal_pos_key)
    robot_xy = asset.data.root_pos_w[:, :2]
    dist = torch.norm(goal_w[:, :2] - robot_xy, dim=-1)
    return 1.0 - torch.tanh(dist / std)

def goal_reached_bonus(env, threshold=0.25, goal_pos_key="goal_pos", asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    goal_w = getattr(env, goal_pos_key)
    dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)
    return (dist < threshold).float()

def collision_penalty(env, sensor_cfg=SceneEntityCfg("contact_sensor"), threshold=0.5):
    sensor = env.scene[sensor_cfg.name]
    net_force = torch.norm(sensor.data.net_forces_w[:, :, :], dim=-1)
    max_force = net_force.max(dim=-1).values
    return (max_force > threshold).float()

def angular_velocity_penalty(env, asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    return asset.data.root_ang_vel_b[:, 2] ** 2

# --- Terminations ---
def time_out_termination(env, *args, **kwargs):
    # Isaac Lab will handle time-out if time_out=True in TerminationTermCfg
    return None

def goal_reached_termination(env, threshold=0.25, goal_pos_key="goal_pos", asset_cfg=SceneEntityCfg("robot")):
    asset = env.scene[asset_cfg.name]
    goal_w = getattr(env, goal_pos_key)
    dist = torch.norm(goal_w[:, :2] - asset.data.root_pos_w[:, :2], dim=-1)
    return dist < threshold
