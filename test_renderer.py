"""
Renderer smoke test and live demo.

Running normally (``python test_renderer.py``) will open the live web UI,
stream a short simulation, and leave the server running so you can
inspect the visuals. Run ``python -m unittest test_renderer.py`` for the
headless assertion-only smoke test.
"""

import json
import tempfile
import unittest
import time
from typing import Dict

from env import GridCombatEnv, Scenario, WebRenderer, create_mixed_scenario
from env.core import Team, MoveDir
from env.core.actions import Action
from env.entities import Aircraft


def make_minimal_scenario() -> Scenario:
    """Create a tiny scenario with one aircraft per team."""
    return create_mixed_scenario()


class TestWebRenderer(unittest.TestCase):
    def setUp(self) -> None:
        self.env = GridCombatEnv(verbose=False)
        scenario = make_minimal_scenario()
        self.state = self.env.reset(scenario=scenario.to_dict())

    def test_render_capture_and_save(self) -> None:
        renderer = WebRenderer(port=5051, live=False, auto_open=False)

        # Build a wait action for every alive entity
        actions = {entity.id: Action.wait() for entity in self.env.world.get_alive_entities()}

        renderer.capture(self.state, actions)
        self.assertEqual(len(renderer.history), 1)

        snapshot = renderer.history[0]
        self.assertIn("grid", snapshot)
        self.assertIn("entities", snapshot)
        self.assertIn("actions", snapshot)
        self.assertEqual(len(snapshot["actions"]), len(actions))

        # Save to disk and ensure JSON structure is preserved
        with tempfile.TemporaryDirectory() as tmpdir:
            path = f"{tmpdir}/game.json"
            renderer.save(path)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

        self.assertEqual(data["version"], "1.0")
        self.assertEqual(len(data["turns"]), len(renderer.history))


if __name__ == "__main__":
    # Live demo mode by default so running the file shows the UI.
    print("Starting live renderer demo at http://localhost:5055 ...")
    env = GridCombatEnv(verbose=False)
    scenario = make_minimal_scenario()
    state = env.reset(scenario=scenario.to_dict())

    renderer = WebRenderer(port=5055, live=True, auto_open=True)

    def build_actions() -> Dict[int, Action]:
        """Drift entities toward the top-right to visualize movement."""
        actions: Dict[int, Action] = {}
        grid = env.world.grid
        for entity in env.world.get_alive_entities():
            if entity.can_move:
                move_right = (entity.pos[0] + 1, entity.pos[1])
                move_up = (entity.pos[0], entity.pos[1] + 1)
                if grid.in_bounds(move_right):
                    actions[entity.id] = Action.move(MoveDir.RIGHT)
                    continue
                if grid.in_bounds(move_up):
                    actions[entity.id] = Action.move(MoveDir.UP)
                    continue
            actions[entity.id] = Action.wait()
        return actions

    max_turns = 100
    for step in range(max_turns):
        actions = build_actions()
        renderer.capture(state, actions)
        state, _, done, _ = env.step(actions)
        time.sleep(0.4)
        if done:
            break

    print("Live demo finished streaming turns.")
    print("Leave this process running to keep the viewer open.")
