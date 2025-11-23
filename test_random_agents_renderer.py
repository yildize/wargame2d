"""
End-to-end rendering demo with random agents.

Running normally (``python test_random_agents_renderer.py``) will launch the
live viewer, pit two RandomAgents against each other, and stream turns to the
UI in real time. The unittest entrypoint runs a short headless smoke test to
ensure rendering keeps up with gameplay.
"""

import time
import unittest
from typing import Dict

from agents.random_agent import RandomAgent
from env import GridCombatEnv, Scenario, WebRenderer, create_mixed_scenario
from env.core import Team
from env.core.actions import Action


def make_minimal_scenario() -> Scenario:
    return create_mixed_scenario()


class TestRandomAgentsRender(unittest.TestCase):
    def setUp(self) -> None:
        self.env = GridCombatEnv(verbose=False)
        scenario = make_minimal_scenario()
        self.state = self.env.reset(scenario=scenario.to_dict())
        self.blue = RandomAgent(Team.BLUE, seed=1)
        self.red = RandomAgent(Team.RED, seed=2)

    def test_random_agents_stream_frames(self) -> None:
        renderer = WebRenderer(port=5052, live=False, auto_open=False)
        max_turns = 6

        for _ in range(max_turns):
            actions = self._build_actions()
            renderer.capture(self.state, actions)
            self.state, _, done, _ = self.env.step(actions)
            if done:
                break

        self.assertGreaterEqual(len(renderer.history), 1)
        self.assertLessEqual(len(renderer.history), max_turns)
        last_frame = renderer.history[-1]
        self.assertIn("actions", last_frame)
        self.assertGreaterEqual(len(last_frame["actions"]), 1)

    def _build_actions(self) -> Dict[int, Action]:
        blue_actions = self.blue.get_actions(self.state)
        red_actions = self.red.get_actions(self.state)
        return {**blue_actions, **red_actions}


if __name__ == "__main__":
    print("Starting live random-agent demo at http://localhost:5056 ...")
    env = GridCombatEnv(verbose=False)
    scenario = make_minimal_scenario()
    state = env.reset(scenario=scenario.to_dict())
    blue = RandomAgent(Team.BLUE, name="Blue RNG", seed=3)
    red = RandomAgent(Team.RED, name="Red RNG", seed=4)
    renderer = WebRenderer(port=5056, live=True, auto_open=True)

    max_turns = 150
    while max_turns > 0:
        actions = {**blue.get_actions(state), **red.get_actions(state)}
        renderer.capture(state, actions)
        state, _, done, _ = env.step(actions)
        time.sleep(0.35)
        max_turns -= 1
        if done:
            print("Game finished early; streaming stops.")
            break

    print("Finished streaming random-agent turns.")
