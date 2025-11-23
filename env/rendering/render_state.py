"""
Helper utilities for converting game state into render-friendly payloads.

The browser client and API expect plain JSON data. The builder in this
module translates the internal world objects and action map into a
serializable dict that can be streamed over REST/WebSocket.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..core.actions import Action
from ..core.types import Team
from ..world.world import WorldState


class RenderStateBuilder:
    """Build JSON-serializable render state snapshots."""

    @staticmethod
    def build(state: Dict[str, Any], actions: Dict[int, Action]) -> Dict[str, Any]:
        """
        Convert the environment state and action map into a JSON-friendly dict.

        Args:
            state: Environment state dict returned by GridCombatEnv
            actions: Mapping of entity_id -> Action for the current turn

        Returns:
            Dictionary ready to send to the browser
        """
        if "world" not in state:
            raise ValueError("State missing 'world' key required for rendering")

        world: WorldState = state["world"]
        config = state.get("config", {})

        return {
            "turn": world.turn,
            "grid": {
                "width": world.grid.width,
                "height": world.grid.height,
            },
            "game_over": world.game_over,
            "winner": world.winner.name if world.winner else None,
            "game_over_reason": world.game_over_reason,
            "tracking": {
                "turns_without_shooting": world.turns_without_shooting,
                "turns_without_movement": world.turns_without_movement,
            },
            "config": config,
            "entities": RenderStateBuilder._serialize_entities(world),
            "observations": RenderStateBuilder._serialize_observations(world),
            "actions": RenderStateBuilder._serialize_actions(actions),
        }

    @staticmethod
    def _serialize_entities(world: WorldState) -> List[Dict[str, Any]]:
        """Serialize all entities (including dead ones) for the frontend."""
        serialized: List[Dict[str, Any]] = []

        for entity in world.get_all_entities():
            data: Dict[str, Any] = {
                "id": entity.id,
                "team": entity.team.name,
                "kind": entity.kind.value,
                "type": entity.__class__.__name__,
                "name": entity.name,
                "position": list(entity.pos),
                "alive": entity.alive,
                "is_alive": entity.alive,  # Friendly alias for JS
                "can_move": entity.can_move,
                "can_shoot": entity.can_shoot,
                "radar_range": getattr(entity, "radar_range", 0),
                "active_radar": entity.get_active_radar_range(),
                "missiles": getattr(entity, "missiles", None),
                "missile_max_range": getattr(entity, "missile_max_range", None),
            }

            # SAM-specific fields (optional)
            data["radar_on"] = getattr(entity, "on", None)
            data["cooldown_remaining"] = getattr(entity, "_cooldown", None)

            serialized.append(data)

        return serialized

    @staticmethod
    def _serialize_observations(world: WorldState) -> Dict[str, Any]:
        """Serialize per-team observations to support fog-of-war rendering."""
        observations: Dict[str, Any] = {}

        for team in Team:
            view = world.get_team_view(team)
            obs_list = view.get_all_observations()

            positions = {
                tuple(obs.position) for obs in obs_list
            }
            # Ensure team always sees their own occupied positions
            for entity in world.get_team_entities(team, alive_only=True):
                positions.add(entity.pos)

            observations[team.name.lower()] = {
                "entities": [obs.to_dict() for obs in obs_list],
                "visible_positions": [list(pos) for pos in sorted(positions)],
                "friendly_ids": sorted(view.get_friendly_ids()),
                "visible_enemy_ids": sorted(view.get_enemy_ids(team)),
            }

        return observations

    @staticmethod
    def _serialize_actions(actions: Dict[int, Action]) -> List[Dict[str, Any]]:
        """Serialize action map to a list for easy iteration client-side."""
        serialized: List[Dict[str, Any]] = []
        for entity_id, action in actions.items():
            serialized.append(
                {
                    "entity_id": entity_id,
                    "type": action.type.name,
                    "params": action.to_dict().get("params", {}),
                    "label": str(action),
                }
            )
        return serialized
