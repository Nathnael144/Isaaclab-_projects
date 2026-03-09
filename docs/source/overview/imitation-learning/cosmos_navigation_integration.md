# Integrating Cosmos with Isaac-Navigation-Flat-Anymal-C for Sim-to-Real

This guide explains how to integrate **NVIDIA Cosmos** (visual augmentation) with the **Isaac-Navigation-Flat-Anymal-C** task in Isaac Lab and train again for improved sim-to-real deployment.

## Overview

- **Cosmos** in Isaac Lab is used to **augment demonstration videos** (lighting, textures, backgrounds) so visuomotor policies train on more diverse visuals and transfer better to the real world.
- The **existing Cosmos pipeline** is built for manipulation (Franka stacking): Mimic → HDF5 → MP4 → Cosmos Transfer1 → MP4 → HDF5 → Robomimic BC.
- **Navigation (Anymal-C)** is currently **state-based** (no cameras in the policy). To use Cosmos you need to add **vision** to the task and then run a similar pipeline.

---

## Two Paths

### Path A: Cosmos + Imitation (recommended if you want Cosmos)

1. Add a **Navigation task with camera(s)** so you can record video and train a visuomotor policy.
2. **Generate demonstrations** (see below).
3. Convert demos to **MP4** → run **Cosmos Transfer1** → convert back to **HDF5**.
4. **Train** a visuomotor policy (e.g. BC with Robomimic, or RL with a vision-capable backend).

### Path B: Visuomotor RL only (no Cosmos)

1. Add a Navigation task with camera and image observations.
2. Train with **RL** (e.g. RL Games with camera PPO) and use **domain randomization** for sim-to-real. No Cosmos.

Below we focus on **Path A** (Cosmos integration).

---

## Step 1: Add a Navigation task with camera

You need a new environment config that:

- Keeps the same Navigation dynamics (pose command, low-level policy, rewards).
- Adds at least one **camera** to the scene (e.g. forward-facing on the robot base).
- Adds **image** observations to the policy (and optionally segmentation/depth for Cosmos).

Cosmos works best with **RGB + depth + segmentation** (and optionally normals) so the model can preserve structure while changing appearance. So the new config should:

- Define a camera (e.g. `nav_cam`) with `data_types=["rgb", "semantic_segmentation", "normals", "distance_to_image_plane"]` if you want the full Cosmos workflow.
- Add observation terms for those (e.g. `nav_cam`, `nav_cam_segmentation`, `nav_cam_depth`, `nav_cam_normals`) in an observation group with `concatenate_terms=False` (like the Franka Cosmos env).

Reference implementation:  
`source/isaaclab_tasks/isaaclab_tasks/manager_based/manipulation/stack/config/franka/stack_ik_rel_visuomotor_cosmos_env_cfg.py`  
and scene/camera setup in that file and its parent.

**Implemented in Isaac Lab:** Use the provided visuomotor Cosmos config and tasks:

- **Config:** `source/isaaclab_tasks/isaaclab_tasks/manager_based/navigation/config/anymal_c/navigation_visuomotor_cosmos_env_cfg.py`
- **Tasks:** `Isaac-Navigation-Flat-Anymal-C-Visuomotor-Cosmos-v0` (train) and `Isaac-Navigation-Flat-Anymal-C-Visuomotor-Cosmos-Play-v0` (play).

These add a forward-facing `nav_cam` on the robot base with RGB + depth, and policy observations include `base_lin_vel`, `projected_gravity`, `pose_command`, `nav_cam`, and `nav_cam_depth`. Use these task IDs in the steps below where the doc refers to a “Navigation visuomotor” task.

---

## Step 2: Generate demonstrations

You need HDF5 files containing **camera frames + actions** (and optionally state) for each timestep.

**Option 2a – Use your trained state-based policy**

1. In the **visuomotor** Navigation env (with camera), run your **trained state-based policy** (e.g. from `Isaac-Navigation-Flat-Anymal-C-v0`) by feeding it the state obs and logging:
   - Camera images (under keys Cosmos expects, e.g. `nav_cam`, `nav_cam_depth`, `nav_cam_segmentation`, `nav_cam_normals`).
   - Actions (and optionally state obs).
2. Save rollouts in HDF5 with the same structure as the Franka Cosmos demos (e.g. `obs/<key>` and `actions`), so `hdf5_to_mp4.py` and `mp4_to_hdf5.py` can be used with `--input_keys` adapted to your keys (e.g. `nav_cam`, ...).

**Option 2b – Isaac Lab Mimic (if you add a Mimic-compatible env)**

- Implement a Mimic-compatible Navigation env (with the same camera modalities as above) and use:
  ```bash
  ./isaaclab.sh -p scripts/imitation_learning/isaaclab_mimic/generate_dataset.py \
    --task Isaac-Navigation-Flat-Anymal-C-Visuomotor-Cosmos-Mimic-v0 \
    --input_file ./datasets/annotated_nav_demos.hdf5 \
    --output_file ./datasets/mimic_nav_1k.hdf5 \
    ...
  ```
- This requires adding a corresponding env in `isaaclab_mimic` (e.g. under `envs/`) and registering it.

---

## Step 3: Cosmos pipeline (same as Franka)

Once you have HDF5 demos with camera keys (e.g. `nav_cam`, `nav_cam_depth`, `nav_cam_segmentation`, `nav_cam_normals`):

**3.1 HDF5 → MP4**

For the provided Navigation Cosmos env (which has `nav_cam` and `nav_cam_depth`):

```bash
python scripts/tools/hdf5_to_mp4.py \
  --input_file datasets/mimic_nav_1k.hdf5 \
  --output_dir datasets/mimic_nav_1k_mp4 \
  --input_keys nav_cam nav_cam_depth
```

Use the same `--video_height`, `--video_width`, `--framerate` as in the [augmented imitation doc](augmented_imitation.rst) if you use Cosmos Transfer1 as recommended.

**3.2 Run Cosmos Transfer1**

- Clone [cosmos-transfer1](https://github.com/nvidia-cosmos/cosmos-transfer1) and checkout the recommended commit (e.g. `e4055e39ee9c53165e85275bdab84ed20909714a`).
- Use the same setup as in [Running Cosmos](augmented_imitation.rst#running-cosmos) (negative prompt, sigma_max, control_weight, etc.).
- Point the model at your `datasets/mimic_nav_1k_mp4` (or equivalent) and write augmented videos to a folder (e.g. `datasets/cosmos_nav_1k_mp4`) with the **same naming convention** as the original demos so `mp4_to_hdf5.py` can match them.

**3.3 MP4 → HDF5**

```bash
python scripts/tools/mp4_to_hdf5.py \
  --input_file datasets/mimic_nav_1k.hdf5 \
  --videos_dir datasets/cosmos_nav_1k_mp4 \
  --output_file datasets/cosmos_nav_1k.hdf5
```

**3.4 (Optional) Merge original + augmented**

```bash
python scripts/tools/merge_hdf5_datasets.py \
  --input_files datasets/mimic_nav_1k.hdf5 datasets/cosmos_nav_1k.hdf5 \
  --output_file datasets/mimic_cosmos_nav.hdf5
```

---

## Step 4: Train again

**If using Robomimic (BC)**  
You need a Robomimic config for the Navigation visuomotor task (similar to `bc_rnn_image_cosmos.json` for Franka). Then:

```bash
./isaaclab.sh -p scripts/imitation_learning/robomimic/train.py \
  --task Isaac-Navigation-Flat-Anymal-C-Visuomotor-Cosmos-v0 \
  --algo bc \
  --dataset ./datasets/mimic_cosmos_nav.hdf5 \
  --name bc_nav_cosmos
```

You will need a Robomimic config for this task (e.g. image-based BC similar to the Franka Cosmos config).

**If using RL (e.g. RL Games with camera)**  
Register the visuomotor Navigation task with an RL Games camera PPO config (see e.g. `Isaac-Cartpole-RGB-v0` and `rl_games_camera_ppo_cfg.yaml`). Then train with that task; you can optionally mix in the Cosmos-augmented HDF5 as a prior or use it for initialization.

---

## Summary checklist

| Step | Action |
|------|--------|
| 1 | Add Navigation env config with camera(s) and image obs (and optional seg/depth/normals for Cosmos). Register task (e.g. `Isaac-Navigation-Flat-Anymal-C-Visuomotor-v0`). |
| 2 | Generate HDF5 demos (state-policy rollouts + camera, or Mimic with a Nav-Cosmos-Mimic env). |
| 3 | Run `hdf5_to_mp4.py` → Cosmos Transfer1 → `mp4_to_hdf5.py`; optionally `merge_hdf5_datasets.py`. |
| 4 | Train visuomotor policy (Robomimic BC or RL Games camera PPO) on the (merged) dataset. |
| 5 | For sim-to-real, use a student policy with only real-sensor obs (no base_lin_vel), export ONNX, deploy. |

The **existing Cosmos model and scripts** in Isaac Lab (Cosmos Transfer1, `hdf5_to_mp4.py`, `mp4_to_hdf5.py`, `merge_hdf5_datasets.py`, `cosmos_prompt_gen.py`) are reusable; the extra work is adding the **Navigation visuomotor task**, **demo generation** for that task, and a **training config** (Robomimic or RL Games) for it.
