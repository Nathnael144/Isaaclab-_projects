# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Navigation environment config with camera for Cosmos visual augmentation pipeline.

Use this config to:
- Record camera streams (RGB, depth, segmentation) for Cosmos augmentation.
- Train a visuomotor policy (with RL Games camera PPO or Robomimic BC after Cosmos).

See docs/source/overview/imitation-learning/cosmos_navigation_integration.md for the full pipeline.
"""

import isaaclab.sim as sim_utils
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

import isaaclab_tasks.manager_based.navigation.mdp as mdp

from .navigation_env_cfg import LOW_LEVEL_ENV_CFG, NavigationEnvCfg


@configclass
class ObservationsCfg:
    """Observation specifications with vector + image for Cosmos pipeline."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Policy obs: state + nav_cam (and optional depth/seg for Cosmos)."""

        base_lin_vel = ObsTerm(func=mdp.base_lin_vel)
        projected_gravity = ObsTerm(func=mdp.projected_gravity)
        pose_command = ObsTerm(func=mdp.generated_commands, params={"command_name": "pose_command"})
        nav_cam = ObsTerm(
            func=mdp.image,
            params={"sensor_cfg": SceneEntityCfg("nav_cam"), "data_type": "rgb", "normalize": False},
        )
        nav_cam_depth = ObsTerm(
            func=mdp.image,
            params={
                "sensor_cfg": SceneEntityCfg("nav_cam"),
                "data_type": "distance_to_image_plane",
                "normalize": True,
            },
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = False

    policy: PolicyCfg = PolicyCfg()


@configclass
class NavigationVisuomotorCosmosEnvCfg(NavigationEnvCfg):
    """Navigation config with forward camera for Cosmos augmentation and visuomotor training."""

    observations: ObservationsCfg = ObservationsCfg()

    def __post_init__(self):
        super().__post_init__()

        # Forward-facing camera on robot base for navigation (RGB + depth for Cosmos)
        self.scene.nav_cam = CameraCfg(
            prim_path="{ENV_REGEX_NS}/Robot/base/nav_cam",
            update_period=0.0,
            height=128,
            width=128,
            data_types=["rgb", "distance_to_image_plane"],
            spawn=sim_utils.PinholeCameraCfg(
                focal_length=24.0,
                focus_distance=400.0,
                horizontal_aperture=20.955,
                clipping_range=(0.1, 20.0),
            ),
            offset=CameraCfg.OffsetCfg(
                pos=(0.32, 0.0, 0.0),
                rot=(0.5, -0.5, 0.5, -0.5),
                convention="ros",
            ),
        )


@configclass
class NavigationVisuomotorCosmosEnvCfg_PLAY(NavigationVisuomotorCosmosEnvCfg):
    """Play config: fewer envs, no obs corruption."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.scene.num_envs = 50
        self.scene.env_spacing = 2.5
        self.observations.policy.enable_corruption = False
