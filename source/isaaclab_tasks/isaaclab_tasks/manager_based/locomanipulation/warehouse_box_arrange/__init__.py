"""Mobile G1 warehouse box arranging task (RSL-RL)."""

import gymnasium as gym

from . import agents


gym.register(
    id="Isaac-Warehouse-BoxArrange-G1-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    kwargs={
        "env_cfg_entry_point": f"{__name__}.warehouse_box_arrange_env_cfg:WarehouseBoxArrangeG1EnvCfg",
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:WarehouseBoxArrangeG1PPORunnerCfg",
    },
    disable_env_checker=True,
)

