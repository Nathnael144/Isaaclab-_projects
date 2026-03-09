# Copyright (c) 2026, TurtleBot3 Isaac Lab Project
# SPDX-License-Identifier: MIT
"""MDP sub-package: custom actions, observations, rewards, and terminations."""

from .actions import *  # noqa: F401, F403
from .observations import *  # noqa: F401, F403
from .rewards import *  # noqa: F401, F403
from .terminations import *  # noqa: F401, F403


# Minimal `time_out` fallback compatible with IsaacLab's API.
# Returns a boolean tensor (size = num envs) indicating whether each
# environment has timed out. This simple implementation never times out
# (all False) and is intended for smoke tests; replace with a proper
# implementation if you need episode-length-based termination.
try:
	import torch

	def time_out(env, *a, **k):
		try:
			n = int(getattr(env, "num_envs", env.scene.num_envs))
		except Exception:
			n = 1
		return torch.zeros(n, dtype=torch.bool, device=getattr(env, "device", "cpu"))
except Exception:
	# If torch isn't available in this environment, provide a Python list
	# of False values as a fallback (least-preferred).
	def time_out(env, *a, **k):
		try:
			n = int(getattr(env, "num_envs", env.scene.num_envs))
		except Exception:
			n = 1
		return [False] * n
