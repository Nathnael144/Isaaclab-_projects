"""Command helpers for the table cleaning task.

The environment uses a physical target marker (a small sphere) that is randomized
on reset. This module exists to keep task-specific command/target utilities colocated.
"""

from __future__ import annotations

# Currently unused; target sampling is handled via reset events on the target asset.

