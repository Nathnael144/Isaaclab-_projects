"""Humanoid warehouse pick-and-place task.

This package registers a Gymnasium environment for training a Unitree G1
humanoid robot to pick up a box object from one table and place it on another
table in a warehouse environment.
"""

import gymnasium as gym

from . import agents

gym.register(
    id="Isaac-Humanoid-Warehouse-PickPlace-G1-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.warehouse_pickplace_env_cfg:HumanoidWarehousePickPlaceEnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:HumanoidWarehousePickPlacePPORunnerCfg",
    },
    disable_env_checker=True,
)
