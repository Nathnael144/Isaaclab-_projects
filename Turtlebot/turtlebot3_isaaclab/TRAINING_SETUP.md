# TurtleBot3 Stage 2 — Training Setup Documentation

This document describes the trained PPO model, reward design, robot configuration, and environment setup for the Isaac Lab TurtleBot3 Stage 2 (static obstacle) navigation task.

---

## 1. Training Script and Model

**File:** `train2.py`

### 1.1 Overview

- **Algorithm:** PPO (Proximal Policy Optimization) via RSL-RL.
- **Purpose:** Train a TurtleBot3 to navigate to a goal in a static arena while avoiding fixed obstacles (walls and pillars).

### 1.2 Policy Architecture

- **Class:** `ActorCritic` (RSL-RL).
- **Actor hidden dimensions:** `[128, 128]`
- **Critic hidden dimensions:** `[128, 128]`
- **Activation:** `elu`
- **Initial policy noise (exploration):** `init_noise_std=0.5`

### 1.3 PPO Hyperparameters

| Parameter | Value |
|-----------|--------|
| `value_loss_coef` | 1.0 |
| `use_clipped_value_loss` | True |
| `clip_param` | 0.2 |
| `entropy_coef` | 0.01 |
| `num_learning_epochs` | 5 |
| `num_mini_batches` | 4 |
| `learning_rate` | 3e-4 |
| `schedule` | adaptive |
| `desired_kl` | 0.01 |
| `gamma` | 0.99 |
| `lam` (GAE) | 0.95 |
| `max_grad_norm` | 1.0 |

### 1.4 Runner Setup

- **Steps per env per iteration:** 24
- **Save interval:** every 100 iterations
- **Log interval:** 10
- **Observation groups:** `policy` and `critic` both use the `"policy"` observation group.

### 1.5 Checkpointing

- **Resume training:** Use `--checkpoint <path>` (e.g. `logs/train2/model_final.pt`).
- **Final model:** Saved automatically after training as `logs/train2/model_final.pt`.

### 1.6 Running Training

```bash
# From IsaacLab repo root
./isaaclab.sh -p Turtlebot/turtlebot3_isaaclab/train2.py --num_envs 2000 --max_iters 10000 --device cuda:0 --log_dir Turtlebot/turtlebot3_isaaclab/logs/train2

# Headless
./isaaclab.sh -p Turtlebot/turtlebot3_isaaclab/train2.py --num_envs 2000 --max_iters 2000 --headless --log_dir Turtlebot/turtlebot3_isaaclab/logs/train2

# Resume from checkpoint
./isaaclab.sh -p Turtlebot/turtlebot3_isaaclab/train2.py --checkpoint logs/train2/model_final.pt --num_envs 2000 --max_iters 5000 --headless --log_dir Turtlebot/turtlebot3_isaaclab/logs/train2
```

---

## 2. Robot Configuration

**File:** `config/robot_cfg.py`

### 2.1 USD and Physical Constants

- **USD path:** `turtlebot3/turtlebot3_description/urdf/turtlebot3_burger/turtlebot3_burger.usd`
- **Wheel radius:** 0.033 m  
- **Track width:** 0.16 m  
- **Max linear velocity (spec):** 0.22 m/s  
- **Max angular velocity (spec):** 2.84 rad/s  

### 2.2 Physics (Articulation)

- **Rigid body:** enabled; high max linear/angular velocity limits for stability.
- **Articulation solver:**  
  - `solver_position_iteration_count`: 4  
  - `solver_velocity_iteration_count`: 1 (for more stable wheel dynamics)
- **Self-collisions:** disabled.

### 2.3 Actuators (Wheels)

- **Type:** `ImplicitActuatorCfg` (velocity control).
- **Joints:** `a__namespace_wheel_left_joint`, `a__namespace_wheel_right_joint`
- **Effort limit (sim):** 10.0  
- **Velocity limit (sim):** 30.0 rad/s  
- **Stiffness:** 0.0 (pure velocity control)  
- **Damping:** 1.5 (allows wheels to reach target velocity faster than higher damping)

### 2.4 Initial State

- **Position:** (0, 0, 0.05) m (slightly above ground).
- **Joint positions:** 0.0 for both wheel joints.

---

## 3. Environment Configuration

**File:** `stages/stage2_static_env_cfg.py`

### 3.1 Simulation Timing

- **Simulation dt:** 1/120 s  
- **Decimation:** 4 (policy runs at 30 Hz)  
- **Episode length:** 26.6 s (~800 policy steps, aligned with DQN-style 800 steps)

### 3.2 Scene

#### 3.2.1 Arena

- **Ground:** 100×100 m plane.
- **Walls:** Four kinematic walls forming a 6×6 m arena:
  - North/South: 6×0.1×0.5 m at y = ±3 m  
  - East/West: 0.1×6×0.5 m at x = ±3 m  

#### 3.2.2 Static Obstacles

- **Pillar A:** cylinder r=0.15 m, at (1.0, 1.0)  
- **Pillar B:** cylinder r=0.15 m, at (-1.0, -0.5)  
- **Pillar C:** cylinder r=0.2 m, at (0.5, -1.5)  
- **Pillar D:** cylinder r=0.15 m, at (-2.0, 1.5)  
- **Pillar E:** cylinder r=0.15 m, at (2.0, -1.2)  
- **Pillar F:** cylinder r=0.15 m, at (0.0, 2.2)  
- **Pillar G:** cylinder r=0.15 m, at (-2.5, -2.0)  
- **Inner wall:** cuboid 2×0.1×0.5 m at (-0.5, 1.0)  

All obstacles are kinematic and participate in LiDAR and contact.

#### 3.2.3 Sensors

- **LiDAR (RayCaster):**
  - Mount: base_link, offset z=0.172 m  
  - Pattern: 360° horizontal, 5° resolution → 72 rays  
  - Max range: 3.5 m  
  - Update period: 1/30 s  
  - Meshes: ground, four walls, PillarA–G, InnerWall  

- **Contact sensor:** on robot base_link, every sim step (for collision detection).

### 3.3 Actions

**Class:** `Stage2ActionsCfg` → `DifferentialDriveActionCfg`

| Parameter | Value | Description |
|-----------|--------|-------------|
| `fixed_linear_vel` | 0.50 m/s | Constant forward speed; policy controls only turning. |
| `scale` | (0.7,) | Angular velocity: raw action [-1, 1] → [-0.7, 0.7] rad/s. |
| `offset` | (0.0,) | No offset. |
| `smooth_alpha` | 0.1 | Strong smoothing (EMA) for smoother acceleration and less twitch. |
| `wheel_radius` | 0.033 m | |
| `track_width` | 0.16 m | |

### 3.4 Observations

**Group:** `policy` (and `critic`), concatenated into a single vector.

| Term | Shape | Description |
|------|--------|-------------|
| `heading` | 1 | Angle to goal in robot frame. |
| `distance` | 1 | Distance to goal. |
| `obs_min_range` | 1 | Minimum LiDAR range (obstacle proximity). |
| `obs_angle` | 1 | Angle to closest obstacle. |
| `lidar` | 72 | LiDAR scan (from pattern above). |

**Total policy observation dimension:** 76.

---

## 4. Rewards

**Class:** `Stage2RewardsCfg`

| Term | Weight | Description |
|------|--------|-------------|
| `goal_distance` | **0.0** | Disabled (DQN-style: no dense goal-distance shaping). |
| `goal_reached` | **+100.0** | Bonus when within 0.2 m of goal. |
| `collision` | **-100.0** | Penalty when contact force exceeds threshold (terminal-like failure). |
| `distance_progress` | **50.0** | Reward for decreasing distance to goal (progress shaping). |
| `heading` | **1.0** | Reward for aligning heading with goal (kept low to avoid spinning in place). |
| `time_penalty` | **-0.001** | Per-step penalty to encourage faster completion. |
| `action_rate` | **-0.1** | Penalty on rapid steering changes (smoother actions). |
| `angular_vel` | **-0.5** | Penalty on large yaw rate (discourage spinning). |

- **Goal reached:** threshold 0.2 m.  
- **Collision:** uses contact sensor; threshold 0.5 (force-based).

---

## 5. Terminations

**Class:** `Stage2TerminationsCfg`

| Term | Description |
|------|-------------|
| `time_out` | Episode length (26.6 s) reached. |
| `goal_reached` | Robot within 0.2 m of goal. |
| `collision` | Contact sensor above threshold (0.5). |
| `robot_flipped` | Tilt beyond limit (e.g. 0.8 rad). |
| `out_of_bounds` | Outside x ∈ [-3.5, 3.5], y ∈ [-3.5, 3.5]. |

---

## 6. Events (Resets)

**Class:** `Stage2EventsCfg`

| Event | Mode | Description |
|-------|------|-------------|
| `reset_robot` | reset | Reset robot root state: position (0, 0), yaw 0, zero velocity. |
| `reset_goal` | reset | Resample goal and update green goal marker for each env. |

Goal resampling and marker update run on every episode reset (success, failure, or timeout).

---

## 7. Evaluation and Playback

**File:** `run_stage2.py`

- **Evaluation:** Load `model_final.pt` (or another checkpoint) and run the policy in the same Stage 2 env.
- **Policy input:** Full observation `TensorDict` (e.g. `policy.act_inference(obs)`), not just `obs["policy"]`.
- **Actor/Critic:** Must use `[128, 128]` hidden dims to match the saved checkpoint.

Example:

```bash
./isaaclab.sh -p Turtlebot/turtlebot3_isaaclab/run_stage2.py --mode eval --checkpoint Turtlebot/turtlebot3_isaaclab/logs/train2/model_final.pt
```

---

## 8. Design Notes (Summary)

- **Rewards** align with a DQN-style setup: +100 / -100 for goal and collision, small time penalty, no dense goal-distance term; shaping via `distance_progress` and `heading`; `action_rate` and `angular_vel` encourage smooth, non-spinning behavior.
- **Robot** uses fixed 0.5 m/s forward speed and limited angular range (±0.7 rad/s) with strong smoothing (`smooth_alpha=0.1`) for stable, responsive motion.
- **Environment** is a 6×6 m arena with 7 pillars and one inner wall, LiDAR and contact sensors, and goal resets every episode.

For behavior tuning (e.g. less zigzag, faster vs. safer), adjust in `stage2_static_env_cfg.py`: reward weights (`distance_progress`, `heading`, `action_rate`, `angular_vel`), action `scale`/`smooth_alpha`, and `fixed_linear_vel`.
