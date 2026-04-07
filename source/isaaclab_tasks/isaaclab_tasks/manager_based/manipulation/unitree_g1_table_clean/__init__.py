"""Unitree G1 table cleaning task.

This package registers Gymnasium environments for training a fixed-base Unitree G1
to wipe target points on a table surface.
"""

import gymnasium as gym

from . import agents


gym.register(
    id="Isaac-TableClean-G1-IK-Abs-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.table_clean_env_cfg:UnitreeG1TableCleanEnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:UnitreeG1TableCleanPPORunnerCfg",
    },
    disable_env_checker=True,
)

