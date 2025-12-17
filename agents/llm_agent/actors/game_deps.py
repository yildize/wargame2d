from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING, Dict, List


if TYPE_CHECKING:
    # Imported only for type checking to avoid circular import at runtime
    from env import StepInfo
    from agents.llm_agent.actors.strategist_compact import StrategyOutput
    from agents.llm_agent.actors.analyst_compact import AnalystCompactOutput


@dataclass
class GameDeps:
    team_name: Optional[str] = None
    current_turn_number: int = 0
    strategy_plan: Optional[StrategyOutput] = None
    just_replanned: bool = False

    current_state: Optional[str] = None
    current_state_dict: Optional[dict[str, Any]] = None

    analyst_key_facts: Dict[int, List[str]] = field(default_factory=dict)
    analyst_last_analysis: Optional[str] = None
    analyst_history: List["AnalystCompactOutput"] = field(default_factory=list)
    visible_history: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    max_history_turns: int = 5

    # multi_phase_strategy: Optional[str] = None
    # current_phase_strategy: Optional[str] = None
    # entity_roles: Optional[dict[int, str]] = None
    # callback_conditions: Optional[list[str]] = None
    # callback_conditions_set_turn: Optional[int] = None
    #
    # game_state: dict[int, Any] = field(default_factory=dict)
    # step_info_list: list["StepInfo"] = field(default_factory=list)
