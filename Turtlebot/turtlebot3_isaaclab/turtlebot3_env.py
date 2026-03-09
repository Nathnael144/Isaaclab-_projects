# turtlebot3_env.py
# Isaac Lab ManagerBasedRLEnv for TurtleBot3 navigation

from isaaclab.envs import ManagerBasedRLEnv
from turtlebot3_env_cfg import TurtleBot3EnvCfg
import torch

def sample_goal(env):
    goal = env.scene.env_origins[:, :2].clone()
    goal[:, 0] += torch.empty(env.num_envs, device=env.device).uniform_(-2.0, 2.0)
    goal[:, 1] += torch.empty(env.num_envs, device=env.device).uniform_(-2.0, 2.0)
    env.goal_pos = goal

class TurtleBot3RLEnv(ManagerBasedRLEnv):
    def reset(self, *args, **kwargs):
        result = super().reset(*args, **kwargs)
        sample_goal(self)
        return result

def make_env(num_envs=128):
    cfg = TurtleBot3EnvCfg()
    cfg.scene.num_envs = num_envs
    return TurtleBot3RLEnv(cfg=cfg)
