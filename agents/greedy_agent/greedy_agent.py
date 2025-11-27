"""
Greedy agent placeholder that will select locally optimal actions.

Decision logic will be implemented later; this file defines the structure
and registration so the agent can be instantiated by config.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from env.core.actions import Action
from env.core.types import Team
from ..base_agent import BaseAgent
from ..registry import register_agent
from ..team_intel import TeamIntel

if TYPE_CHECKING:
    from env.environment import StepInfo
    from env.world import WorldState


@register_agent("greedy")
class GreedyAgent(BaseAgent):
    """
    Agent scaffold that will eventually pick the best available action
    for each entity based on local heuristics.
    """

    def __init__(
        self,
        team: Team,
        name: str | None = None,
        **_: Any,
    ):
        """
        Initialize the greedy agent.

        Args:
            team: Team to control
            name: Optional agent name (default: "GreedyAgent")
        """
        super().__init__(team, name)

    def get_actions(
        self,
        state: Dict[str, Any],
        step_info: Optional["StepInfo"] = None,
        **kwargs: Any,
    ) -> tuple[Dict[int, Action], Dict[str, Any]]:
        """
        Decide actions for each controlled entity.

        This method will be filled in with greedy heuristics that examine
        the visible world state via TeamIntel and choose actions that look
        best in the moment.
        """
        raise NotImplementedError("GreedyAgent.get_actions is not implemented yet")
