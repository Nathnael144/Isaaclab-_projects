# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""TurtleBot3 Burger robot configuration for Isaac Lab.

Defines the ArticulationCfg for the TurtleBot3 Burger differential-drive robot.
Uses a self-contained USD with physics parameters copied exactly from the
original URDF converter output, plus simple geometric visual primitives for
viewport visibility.  No composition arcs or external references.
"""

from __future__ import annotations

import os

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg

# ---------------------------------------------------------------------------
# Path to the clean TurtleBot3 Burger USD
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TURTLEBOT3_USD_PATH: str = os.path.normpath(os.path.join(
    _THIS_DIR,
    os.pardir,
    os.pardir,
    "turtlebot3",
    "turtlebot3_description",
    "urdf",
    "turtlebot3_burger",
    "turtlebot3_burger.usd",
))

# ---------------------------------------------------------------------------
# Physical constants (from URDF)
# ---------------------------------------------------------------------------
WHEEL_RADIUS: float = 0.033  # metres
TRACK_WIDTH: float = 0.16  # metres (left-to-right wheel separation)
MAX_LINEAR_VEL: float = 0.22  # m/s  (TurtleBot3 Burger spec)
MAX_ANGULAR_VEL: float = 2.84  # rad/s (TurtleBot3 Burger spec)

# ---------------------------------------------------------------------------
# ArticulationCfg — TurtleBot3 Burger
# ---------------------------------------------------------------------------
TURTLEBOT3_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=TURTLEBOT3_USD_PATH,
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            rigid_body_enabled=True,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
            enable_gyroscopic_forces=True,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=False,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=1,
            sleep_threshold=0.005,
            stabilization_threshold=0.001,
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        # Spawn slightly above ground so the robot settles down
        pos=(0.0, 0.0, 0.05),
        joint_pos={
            "a__namespace_wheel_left_joint": 0.0,
            "a__namespace_wheel_right_joint": 0.0,
        },
    ),
    actuators={
        "wheels": ImplicitActuatorCfg(
            joint_names_expr=["a__namespace_wheel_left_joint", "a__namespace_wheel_right_joint"],
            effort_limit_sim=10.0,
            velocity_limit_sim=30.0,
            stiffness=0.0,      # Velocity control → no position stiffness
            damping=1.5,
        ),
    },
)
