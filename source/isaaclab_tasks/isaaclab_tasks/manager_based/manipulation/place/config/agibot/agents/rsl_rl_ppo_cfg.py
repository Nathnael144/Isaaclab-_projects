"""RSL-RL PPO runner config for Agibot place tasks."""

from __future__ import annotations

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg
from isaaclab_rl.rsl_rl import RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg
from isaaclab.utils import configclass


@configclass
class PlaceAgibotPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    """A reasonable default PPO setup for state-based place tasks."""

    # Experiment
    experiment_name = "place_agibot"

    # Rollout
    num_steps_per_env = 24
    max_iterations = 2000
    save_interval = 200

    # Observations groups: use policy for both actor+critic
    obs_groups = {"policy": ["policy"], "critic": ["policy"]}

    # Policy
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=1.0,
        actor_hidden_dims=[256, 256, 128],
        critic_hidden_dims=[256, 256, 128],
        activation="elu",
    )

    # PPO algorithm
    algorithm = RslRlPpoAlgorithmCfg(
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.01,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=3e-4,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
    )

