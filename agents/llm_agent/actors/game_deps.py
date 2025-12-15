from dataclasses import dataclass, field
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # Imported only for type checking to avoid circular import at runtime
    from env import StepInfo


@dataclass
class GameDeps:
    current_turn_number: int = 0
    just_replanned: bool = False
    current_state_dict: Optional[dict[str, Any]] = None
    analysed_state_dict: Optional[dict[str, Any]] = None

    multi_phase_strategy: Optional[str] = None
    current_phase_strategy: Optional[str] = None
    entity_roles: Optional[dict[int, str]] = None
    callback_conditions: Optional[list[str]] = None
    callback_conditions_set_turn: Optional[int] = None

    game_state: dict[int, Any] = field(default_factory=dict)
    step_info_list: list["StepInfo"] = field(default_factory=list)
