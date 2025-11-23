"""
Flask/SocketIO API for streaming game states to the browser.

This module is intentionally small: it only handles server concerns
(routes + events). The WebRenderer orchestrates state capture and calls
``broadcast`` to push updates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit


class GameAPI:
    """
    Flask application with REST endpoints and WebSocket events.

    The renderer owns the game history list and shares it with the API.
    """

    def __init__(self, port: int = 5000):
        static_dir = Path(__file__).resolve().parent / "static"
        self.app = Flask(
            __name__,
            static_folder=str(static_dir),
            static_url_path="",
        )
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode="threading",
        )
        self.port = port

        # Game state storage (managed by WebRenderer via shared reference)
        self.history: List[Dict] = []
        self.current_state: Optional[Dict] = None

        self._setup_routes(static_dir)
        self._setup_websocket()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    def _setup_routes(self, static_dir: Path) -> None:
        """Define REST API endpoints."""

        @self.app.route("/")
        def index():
            """Serve main HTML page."""
            return send_from_directory(static_dir, "index.html")

        @self.app.route("/api/history")
        def get_history():
            """Get full game history for replay."""
            return jsonify(
                {
                    "turns": self.history,
                    "total_turns": len(self.history),
                }
            )

        @self.app.route("/api/current")
        def get_current():
            """Get latest state if available."""
            if self.current_state:
                return jsonify(self.current_state)
            return jsonify({"error": "No state available"}), 404

        @self.app.route("/api/turn/<int:turn_number>")
        def get_turn(turn_number: int):
            """Get specific turn state."""
            if 0 <= turn_number < len(self.history):
                return jsonify(self.history[turn_number])
            return jsonify({"error": "Turn not found"}), 404

    # ------------------------------------------------------------------
    # WebSocket handlers
    # ------------------------------------------------------------------
    def _setup_websocket(self) -> None:
        """Define WebSocket handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            """Client connected - send current state if we have it."""
            if self.current_state:
                emit("state_update", self.current_state)

        @self.socketio.on("disconnect")
        def handle_disconnect():
            # No-op hook for now; useful for logging/debugging.
            return

        @self.socketio.on("request_history")
        def handle_history_request():
            """Client requests full history."""
            emit("history", {"turns": self.history})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def broadcast(self, state: Dict) -> None:
        """Broadcast a render state to all connected clients."""
        self.current_state = state
        self.socketio.emit("state_update", state)

    def run(self) -> None:
        """Start the Flask server (blocking call)."""
        self.socketio.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            debug=False,
            use_reloader=False,
        )

