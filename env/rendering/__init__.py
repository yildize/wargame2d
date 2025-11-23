"""
Rendering toolkit for the Grid Combat Environment.

This package provides a lightweight web-based renderer that exposes
the game state over HTTP/WebSocket and ships a simple HTML client for
live viewing or replay.
"""

from .render_state import RenderStateBuilder
from .web_renderer import WebRenderer

__all__ = ["RenderStateBuilder", "WebRenderer"]
