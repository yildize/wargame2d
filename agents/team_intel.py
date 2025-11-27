from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set, TYPE_CHECKING

from env.core.types import EntityKind, GridPos, Team
from env.entities.base import Entity
from env.world.grid import Grid
from env.world.team_view import TeamView

if TYPE_CHECKING:
    from env.world.world import WorldState


@dataclass(frozen=True)
class VisibleEnemy:
    """
    Fog-limited snapshot of a currently observed enemy.
    """

    id: int
    team: Team
    position: GridPos
    kind: EntityKind
    has_fired_before: bool
    seen_by: Set[int]


@dataclass(frozen=True)
class TeamIntel:
    """
    Safe, per-team view of the world for agent decision-making.

    - friendlies: full Entity objects (all fields are fair for your own team)
    - visible_enemies: limited snapshots built from observations
    """

    grid: Grid
    friendlies: List[Entity]
    visible_enemies: List[VisibleEnemy]
    friendly_ids: Set[int]
    visible_enemy_ids: Set[int]

    def get_friendly(self, entity_id: int) -> Optional[Entity]:
        return next((e for e in self.friendlies if e.id == entity_id), None)

    def get_enemy(self, entity_id: int) -> Optional[VisibleEnemy]:
        return next((e for e in self.visible_enemies if e.id == entity_id), None)

    def enemies_in_range(self, entity: Entity, max_range: float) -> List[VisibleEnemy]:
        """Return visible enemies within range of a friendly entity."""
        return [
            enemy
            for enemy in self.visible_enemies
            if self.grid.distance(entity.pos, enemy.position) <= max_range
        ]

    @classmethod
    def build(cls, world: "WorldState", team: Team) -> "TeamIntel":
        """
        Construct a safe per-team intel view from the current world.
        """
        team_view: TeamView = world.get_team_view(team)
        friendlies = world.get_team_entities(team, alive_only=False)

        visible_enemies: List[VisibleEnemy] = []
        for obs in team_view.get_enemy_observations():
            visible_enemies.append(
                VisibleEnemy(
                    id=obs.entity_id,
                    team=obs.team,
                    position=obs.position,
                    kind=obs.kind,
                    has_fired_before=obs.has_fired_before,
                    seen_by=obs.seen_by,
                )
            )

        return cls(
            grid=world.grid,
            friendlies=friendlies,
            visible_enemies=visible_enemies,
            friendly_ids=team_view.get_friendly_ids(),
            visible_enemy_ids=team_view.get_enemy_ids(team),
        )
