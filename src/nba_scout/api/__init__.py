"""HTTP API for the assistant.

The ASGI app lives at ``nba_scout.api.app:app`` (module path kept clean so it does
not shadow the ``app`` submodule).
"""

from .app import create_app

__all__ = ["create_app"]
