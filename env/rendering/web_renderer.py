"""
Web renderer orchestrator.

This class wires together the render state builder and the Flask/SocketIO
API so callers can easily stream live game updates or replay saved games.
"""

from __future__ import annotations

import json
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.actions import Action
from .api import GameAPI
from .render_state import RenderStateBuilder


class WebRenderer:
    """Manage render history and coordinate the API server."""

    def __init__(self, port: int = 5000, live: bool = True, auto_open: bool = True):
        self.port = port
        self.live = live
        self.history: List[Dict[str, Any]] = []

        self.api = GameAPI(port=port)
        self.api.history = self.history  # Share reference

        self._server_thread: Optional[threading.Thread] = None

        if live:
            self._start_server(auto_open=auto_open)

    def capture(self, state: Dict[str, Any], actions: Dict[int, Action]) -> None:
        """
        Capture current state and optionally broadcast to clients.

        Args:
            state: Environment state dict returned by GridCombatEnv
            actions: Mapping of entity_id -> Action executed this turn
        """
        render_state = RenderStateBuilder.build(state, actions)
        self.history.append(render_state)

        if self.live:
            self.api.broadcast(render_state)

    def save(self, filename: str) -> None:
        """Persist current history to disk as JSON."""
        payload = {"version": "1.0", "turns": self.history}
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_replay(self, filename: str, auto_open: bool = True) -> None:
        """
        Load saved game for replay viewing.

        If the server was not running (live=False at init), this will
        start it so the browser can request data.
        """
        path = Path(filename)
        data = json.loads(path.read_text(encoding="utf-8"))

        self.history = data.get("turns", [])
        self.api.history = self.history
        self.api.current_state = self.history[-1] if self.history else None

        if not self._is_server_running():
            self._start_server(auto_open=auto_open)
        elif auto_open:
            self._open_browser()

    def clear(self) -> None:
        """Clear recorded history for a new episode."""
        self.history.clear()
        self.api.current_state = None

    def close(self) -> None:
        """
        Placeholder for graceful shutdown.

        Flask-SocketIO does not offer a simple programmatic stop in
        threading mode. Consumers should exit the process when finished.
        """
        return

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _start_server(self, auto_open: bool = True) -> None:
        """Start the API server in a background daemon thread."""
        if self._is_server_running():
            if auto_open:
                self._open_browser()
            return

        def run_server():
            self.api.run()

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()

        if auto_open:
            # Small delay to give the server time to start before opening.
            time.sleep(1.0)
            self._open_browser()

    def _open_browser(self) -> None:
        """Open the browser to the renderer UI."""
        webbrowser.open(f"http://localhost:{self.port}")

    def _is_server_running(self) -> bool:
        """Check if the server thread is active."""
        return self._server_thread is not None and self._server_thread.is_alive()

