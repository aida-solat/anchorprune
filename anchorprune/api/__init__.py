"""AnchorPrune FastAPI service (v0.4).

Importing this package requires the optional ``[api]`` dependencies
(``fastapi``, ``uvicorn``). The AnchorPrune core never imports this package, so a
plain ``import anchorprune`` works without FastAPI installed.
"""

from anchorprune.api.app import create_app

__all__ = ["create_app"]
