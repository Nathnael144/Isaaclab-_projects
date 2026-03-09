# TurtleBot3 Isaac Lab RL Training Framework

A modular three-stage pipeline for training a **TurtleBot3 Burger** to navigate
using reinforcement learning in **Isaac Lab** (Orbit).

## Project Structure

```
turtlebot3_isaaclab/
├── __init__.py
├── README.md                        ← you are here
│
├── config/
│   ├── __init__.py
│   └── robot_cfg.py                 ← ArticulationCfg for TurtleBot3 Burger
│
├── mdp/
│   ├── __init__.py
│   ├── actions.py                   ← DifferentialDriveAction  [v, ω] → wheel velocities
│   ├── observations.py              ← LiDAR scan, goal-in-body-frame, base state
│   ├── rewards.py                   ← goal distance, collision, TTC, clearance
│   └── terminations.py              ← goal reached, flipped, out-of-bounds
│
├── stages/
│   ├── __init__.py
│   ├── stage1_empty_env_cfg.py      ← Stage 1 env config
│   ├── stage2_static_env_cfg.py     ← Stage 2 env config
│   └── stage3_dynamic_env_cfg.py    ← Stage 3 env config
│
├── run_stage1.py                    ← Spawn-verification script
├── run_stage2.py                    ← Static-env training / evaluation
└── run_stage3.py                    ← Dynamic-env training / evaluation
```

## Prerequisites

| Package | Purpose |
|---------|---------|
| **Isaac Lab** (≥ 4.x) | Simulation framework |
| **PyTorch** (≥ 2.x) | Tensor operations |
| **rsl_rl** *(optional)* | PPO training (RSL-RL) |
| **isaaclab_rl** *(optional)* | RSL-RL ↔ Isaac Lab wrapper |

The TurtleBot3 USD file is expected at:
```
Turtlebot3_ws/turtlebot3/turtlebot3_description/urdf/turtlebot3_burger/turtlebot3_burger.usd
```

## Quick Start

### Stage 1 — Empty Environment (Spawn Verification)

```bash
# Activate your Isaac Lab Python environment
source ~/isaac_env311/bin/activate

# Run with GUI (16 envs by default)
python run_stage1.py

# Headless
python run_stage1.py --headless --num_envs 64
```

The script drives the robot through three phases (idle → forward → spin) and
prints position/velocity diagnostics.  If the robot sits stably on the ground
and responds to commands, the USD and physics configuration are correct.

### Stage 2 — Static Obstacles (Navigation RL)

```bash
# Verify the environment builds correctly (random actions)
python run_stage2.py --headless --mode verify --num_envs 32

# Train with RSL-RL PPO
python run_stage2.py --headless --mode train --num_envs 512 --max_iterations 1000

# Evaluate a checkpoint (with GUI)
python run_stage2.py --mode eval --checkpoint logs/stage2/model_1000.pt
```

**Scene**: 6 × 6 m walled arena with 3 cylindrical pillars and 1 inner wall.
**Observation space** (185-D by default):
  - Robot body-frame linear velocity (2)
  - Robot body-frame angular velocity (1)
  - Goal position in robot frame (2)
  - 2-D LiDAR scan — 180 rays @ 2° resolution (180)

**Reward terms**:
| Term | Weight | Description |
|------|--------|-------------|
| `goal_distance` | +2.0 | `1 − tanh(dist)` dense shaping |
| `goal_reached` | +10.0 | Sparse bonus within 0.25 m |
| `collision` | −5.0 | Contact-sensor penalty |
| `action_rate` | −0.01 | Smoothness (L2 Δ-action) |
| `ang_vel` | −0.005 | Discourage spinning |

### Stage 3 — Dynamic Obstacles

```bash
# Verify
python run_stage3.py --headless --mode verify --num_envs 32

# Train
python run_stage3.py --headless --mode train --num_envs 512 --max_iterations 2000

# Evaluate
python run_stage3.py --mode eval --checkpoint logs/stage3/model_2000.pt
```

**Added over Stage 2**:
  - 4 dynamic rigid objects (2 cubes + 2 spheres) with gravity disabled,
    moving at random velocities and re-randomised on reset.
  - Arena enlarged to 8 × 8 m.
  - LiDAR mesh list includes `/DynObs` so rays detect moving objects.

**Additional reward terms**:
| Term | Weight | Description |
|------|--------|-------------|
| `time_to_collision` | +1.0 | `tanh(min_range / fwd_speed / safe_ttc)` |
| `dynamic_clearance` | −3.0 | Penalty when closest obstacle < 0.3 m |

## Custom Differential-Drive Action

Instead of Isaac Lab's built-in `NonHolonomicActionCfg` (which uses dummy
joints), this framework uses a **`DifferentialDriveAction`** that directly
controls the two *real* wheel joints via velocity targets:

```
v_left  = (v − ω·d/2) / R
v_right = (v + ω·d/2) / R
```

This preserves realistic wheel–ground contact physics, important for
sim-to-real transfer.

## Customisation

- **Change obstacle layout**: edit the `AssetBaseCfg` entries in the scene
  class of `stage2_static_env_cfg.py` or `stage3_dynamic_env_cfg.py`.
- **Tune rewards**: adjust `weight` values in `Stage*RewardsCfg`.
- **Swap RL algorithm**: replace the RSL-RL runner in `run_stage*.py` with
  any Gymnasium-compatible trainer (stable-baselines3, rl_games, SKRL, …).
- **Add more dynamic obstacles**: duplicate the `RigidObjectCfg` entries and
  the corresponding `EventTerm` reset blocks.
