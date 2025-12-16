import random
from typing import Dict, Any, Optional, TYPE_CHECKING, List, Set

from env.core.actions import Action
from env.core.types import ActionType, MoveDir, Team
from env.world import WorldState

from agents.base_agent import BaseAgent
from agents.team_intel import TeamIntel
from agents.registry import register_agent
from agents.llm_agent.helpers.compact_state_formatter import CompactStateFormatter

if TYPE_CHECKING:
    from env.environment import StepInfo


@register_agent("llm_compact")
class LLMCompactAgent(BaseAgent):
    """
    Lightweight agent focused on producing a concise, human-readable state view.

    For now it issues safe fallback actions (WAIT when possible) while emitting
    the compact state in metadata so the LLM flow can be built incrementally.
    """

    def __init__(
        self,
        team: Team,
        name: str = None,
        seed: Optional[int] = None,
        **_: Any,
    ):
        super().__init__(team, name)
        self.rng = random.Random(seed)
        self.state_formatter = CompactStateFormatter()
        self._enemy_memory: Dict[int, Dict[str, Any]] = {}
        self._casualties: Dict[str, List[Dict[str, Any]]] = {"friendly": [], "enemy": []}
        self._recorded_kill_ids: Set[int] = set()

    def get_actions(
        self,
        state: Dict[str, Any],
        step_info: Optional["StepInfo"] = None,
        **kwargs: Any,
    ) -> tuple[Dict[int, Action], Dict[str, Any]]:
        world: WorldState = state["world"]
        intel: TeamIntel = TeamIntel.build(world, self.team)
        actions: Dict[int, Action] = {}
        allowed_actions: Dict[int, List[Action]] = {}

        visible_enemy_ids = self._update_enemy_memory(intel, world.turn)
        missing_enemies = self._collect_missing_enemies(visible_enemy_ids, world.turn)
        self._update_casualties(step_info, world)

        for entity in intel.friendlies:
            if not entity.alive:
                continue
            allowed = entity.get_allowed_actions(world)
            if not allowed:
                continue
            allowed_actions[entity.id] = allowed
            actions[entity.id] = self._pick_fallback_action(allowed)

        state_dict = self.state_formatter.build_state(
            world=world,
            intel=intel,
            allowed_actions=allowed_actions,
            turn=world.turn,
            team=self.team,
            missing_enemies=missing_enemies,
            casualties=self._casualties,
        )
        state_text = self.state_formatter.build_state_string(
            world=world,
            intel=intel,
            allowed_actions=allowed_actions,
            turn=world.turn,
            team=self.team,
            missing_enemies=missing_enemies,
            casualties=self._casualties,
        )

        metadata = {
            "compact_state": state_dict,
            "compact_state_text": state_text,
            "note": "State-only pass; actions are safe fallbacks.",
        }

        print(state_text)
        print("\n" + "=" * 80 + "\n")
        return actions, metadata

    def _update_enemy_memory(self, intel: TeamIntel, turn: int) -> Set[int]:
        visible_ids: Set[int] = set()
        for enemy in intel.visible_enemies:
            visible_ids.add(enemy.id)
            self._enemy_memory[enemy.id] = {
                "id": enemy.id,
                "team": enemy.team.name if hasattr(enemy.team, "name") else str(enemy.team),
                "type": enemy.kind.name if hasattr(enemy.kind, "name") else str(enemy.kind),
                "last_seen_position": {"x": enemy.position[0], "y": enemy.position[1]},
                "last_seen_turn": turn,
            }
        return visible_ids

    def _collect_missing_enemies(self, visible_ids: Set[int], turn: int) -> List[Dict[str, Any]]:
        missing: List[Dict[str, Any]] = []
        for enemy_id, entry in self._enemy_memory.items():
            if enemy_id in visible_ids:
                continue
            last_seen_turn = entry.get("last_seen_turn", turn)
            turns_since_seen = max(turn - last_seen_turn, 0)
            missing.append({**entry, "turns_since_seen": turns_since_seen})
        return missing

    def _update_casualties(self, step_info: Optional["StepInfo"], world: WorldState) -> None:
        """
        Record deaths with killer info and death location/turn.
        """
        if step_info is None:
            return

        combat = getattr(step_info, "combat", None)
        if combat is None:
            return

        killed_ids = getattr(combat, "killed_entity_ids", []) or []
        if not killed_ids:
            return

        killed_on_turn = max(world.turn - 1, 0)
        # Build lookup for killer -> target from combat_results
        killers: Dict[int, int] = {}
        for result in getattr(combat, "combat_results", []) or []:
            if getattr(result, "target_killed", False) and getattr(result, "target_id", None) is not None:
                killers[result.target_id] = getattr(result, "attacker_id", None)

        for entity_id in killed_ids:
            if entity_id in self._recorded_kill_ids:
                continue
            entity = world.get_entity(entity_id)
            if entity is None:
                continue
            entry: Dict[str, Any] = {
                "id": entity.id,
                "team": entity.team.name if hasattr(entity.team, "name") else str(entity.team),
                "type": entity.kind.name if hasattr(entity.kind, "name") else str(entity.kind),
                "death_position": {"x": entity.pos[0], "y": entity.pos[1]},
                "killed_on_turn": killed_on_turn,
            }
            killer_id = killers.get(entity_id)
            if killer_id is not None:
                killer_ent = world.get_entity(killer_id)
                if killer_ent:
                    entry["killed_by"] = {
                        "id": killer_ent.id,
                        "team": killer_ent.team.name if hasattr(killer_ent.team, "name") else str(killer_ent.team),
                        "type": killer_ent.kind.name if hasattr(killer_ent.kind, "name") else str(killer_ent.kind),
                    }
                else:
                    entry["killed_by"] = {"id": killer_id}

            if entity.team == self.team:
                self._casualties["friendly"].append(entry)
            else:
                self._casualties["enemy"].append(entry)
            self._recorded_kill_ids.add(entity_id)

    @staticmethod
    def _pick_fallback_action(allowed: List[Action]) -> Action:
        wait_action = next((a for a in allowed if a.type == ActionType.WAIT), None)
        if wait_action:
            return wait_action
        # Prefer a MOVE with minimal displacement for safety if no WAIT.
        move_action = next((a for a in allowed if a.type == ActionType.MOVE), None)
        if move_action:
            return move_action
        return allowed[0]
