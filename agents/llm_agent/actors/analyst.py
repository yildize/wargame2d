from typing import Annotated, List, Literal, Optional, Union

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field

from agents.llm_agent.actors.game_deps import GameDeps
from agents.llm_agent.prompts.tactics import TACTICAL_GUIDE


ANALYST_TASK = (
    "Provide a concise battlefield analysis for the commander. Cover: "
    "1) threats to AWACS or exposed units and safe repositioning ideas, "
    "2) high-value targets and feasible strikes this turn, "
    "3) radar/visibility gaps plus missing contacts with last-seen details, "
    "4) recommended team intent for the next turn. Keep it under 120 words."
)


class Position(BaseModel):
    x: int = Field(description="X coordinate on the grid.")
    y: int = Field(description="Y coordinate on the grid.")


class MoveAction(BaseModel):
    type: Literal["MOVE"] = Field(
        default="MOVE",
        description="Discriminator for movement actions.",
    )
    direction: Literal["UP", "DOWN", "LEFT", "RIGHT"] = Field(
        description="Cardinal direction for the move.",
        examples=["UP", "DOWN", "LEFT", "RIGHT"],
    )
    destination: Optional[Position] = Field(
        default=None,
        description="Destination after the move if known (x,y).",
    )


class ShootAction(BaseModel):
    type: Literal["SHOOT"] = Field(default="SHOOT", description="Fire a weapon at a target unit.")
    target: int = Field(description="Target unit id to engage.")


class WaitAction(BaseModel):
    type: Literal["WAIT"] = Field(default="WAIT", description="Hold position and take no action this turn.")


class ToggleAction(BaseModel):
    type: Literal["TOGGLE"] = Field(default="TOGGLE", description="Toggle a system on/off. Use only for SAM units.")
    on: bool = Field(
        description="True to activate SAM radar/weapon system, False to go dark/stealth. Only valid for SAM entities."
    )


Action = Annotated[
    Union[MoveAction, ShootAction, ToggleAction, WaitAction],
    Field(discriminator="type"),
]


class ActionAnalysis(BaseModel):
    action: Action = Field(description="Specific action being considered for the unit.")
    implication: str = Field(description="Expected tactical effect or tradeoff of this action.")


class UnitInsight(BaseModel):
    unit_id: int = Field(description="Identifier for the unit in the current game_state.")
    role: str = Field(description="Role or mission context of the unit.")
    key_considerations: List[str] = Field(
        description="Bullet points on threats, resources, positioning, or timing relevant to this unit."
    )
    action_analysis: List[ActionAnalysis] = Field(
        description="Action options for the unit with their implications. Include all feasible options, even 'WAIT'."
    )


class GameAnalysis(BaseModel):
    unit_insights: List[UnitInsight] = Field(
        description="Unit-level analysis items. Start with the most threatened or impactful units."
    )
    critical_alerts: List[str] = Field(
        description="Ordered list of urgent risks that demand commander attention, prefixed with severity."
    )
    opportunities: List[str] = Field(
        description="Offensive or positional openings the team can exploit, prefixed with severity."
    )
    constraints: List[str] = Field(
        description="Key limitations such as ammo, detection gaps, terrain edges, or coordination risks."
    )
    spatial_status: str = Field(
        description="Short narrative of formation posture, positioning relative to enemies, and maneuver space."
    )
    situation_summary: str = Field(
        description="Overall tactical snapshot combining threats, openings, and intent for the next turn."
    )


analyst_agent = Agent(
    "openai:gpt-5-mini",
    deps_type=GameDeps,
    output_type=GameAnalysis,
    instructions="You are an AI game analyst for your team in a grid-based air combat simulation."
)

@analyst_agent.instructions
def full_prompt(ctx: RunContext[GameDeps]) -> str:

    return f"""
### TASK
{ANALYST_TASK}

### TACTICAL GUIDE (REFERENCE ONLY)
{TACTICAL_GUIDE}

### OUTPUT FORMAT
Return JSON that matches the GameAnalysis schema:
- unit_insights: ordered list of UnitInsight objects with key considerations and action analyses per unit.
- critical_alerts: most urgent issues first, each prefixed with severity (e.g., HIGH/MEDIUM/LOW).
- opportunities: actionable openings, prefixed with severity.
- constraints: limiting factors or coordination risks that affect options.
- spatial_status: brief posture and positioning narrative.
- situation_summary: concise commander-ready summary tying alerts and intent together.
- Actions must use these types only (discriminator is 'type'):
  - MOVE: direction in [UP, DOWN, LEFT, RIGHT], optional destination.
  - SHOOT: target is enemy unit id.
  - TOGGLE: on=true/false, only for SAM units (activates/deactivates radar/weapon system).
  - WAIT: hold position.

### GAME STATE 
{ctx.deps.game_state}

### RECENT STEPS
{ctx.deps.step_info_list}
"""
