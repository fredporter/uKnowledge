"""uKnowledge package.

Provides register_routes(app) for uCore extension registry consumption,
and setup(app) as an optional entrypoint for manifest-driven discovery.
"""

from __future__ import annotations

import logging

log = logging.getLogger("uknowledge")

from .routes import register_routes  # noqa: E402

__all__ = ["register_routes", "setup"]


def setup(app) -> None:
    """Run extension lifecycle setup; routes use the manifest registrar."""
    del app
    log.info("uKnowledge extension lifecycle setup complete")
