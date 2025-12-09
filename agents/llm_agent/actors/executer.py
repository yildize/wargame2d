from typing import Literal, Union, List, Optional, Annotated

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelSettings


# --- Action definitions ---
class MoveAction(BaseModel):
    """Command a unit to move one cell in a cardinal direction."""
    type: Literal["MOVE"] = "MOVE"
    entity_id: int = Field(description="ID of the unit to move")
    direction: Literal["UP", "DOWN", "LEFT", "RIGHT"] = Field(
        description="Cardinal direction to move (one cell)"
    )

class ShootAction(BaseModel):
    """Command a unit to fire at an enemy target."""
    type: Literal["SHOOT"] = "SHOOT"
    entity_id: int = Field(description="ID of the unit that will fire")
    target_id: int = Field(description="ID of the enemy unit to target")

class WaitAction(BaseModel):
    """Command a unit to hold position and skip this turn."""
    type: Literal["WAIT"] = "WAIT"
    entity_id: int = Field(description="ID of the unit that will wait")

class ToggleAction(BaseModel):
    """Toggle a unit's special ability or system on/off."""
    type: Literal["TOGGLE"] = "TOGGLE"
    entity_id: int = Field(description="ID of the unit to toggle")
    on: bool = Field(description="True to activate, False to deactivate")

Action = Annotated[
    Union[MoveAction, ShootAction, WaitAction, ToggleAction],
    Field(discriminator="type")
]

# --- Entity-level reasoning wrapper ---
class EntityAction(BaseModel):
    """A single unit's action with tactical justification."""
    reasoning: str = Field(description="Brief tactical rationale for this action")
    action: Action = Field(description="The action this unit will execute")

class TeamAction(BaseModel):
    """Complete turn plan with strategic analysis and per-unit actions."""
    analysis: str = Field(
        description=(
            "Detailed analysis of the current game state. Include: "
            "1) Positions of all friendly and enemy units, "
            "2) Immediate threats and which of our units are in danger, "
            "3) Vulnerable enemy targets and kill opportunities, "
            "4) Positional advantages or disadvantages, "
            "5) How to integrate the director's strategic orders with the tactical situation. "
            "Think step-by-step before deciding on actions."
        )
    )
    entity_actions: List[EntityAction] = Field(
        description="Ordered list of actions for each controllable unit, with reasoning"
    )


from dotenv import load_dotenv
load_dotenv()

logfire.configure(service_name="basic_agent")
logfire.instrument_pydantic_ai()

# --- Agent definition ---
player = Agent(
    "openrouter:qwen/qwen3-coder:exacto",
    model_settings=ModelSettings(
        temperature=0.6,
        top_p=0.95,
        max_tokens=32_000,
        extra_body={
            "top_k": 20,
            "min_p": 0
        }
    ),
    retries=3,
    output_retries=3,
    output_type=TeamAction,
    instructions=(
        "You are an AI field commander leading your team in a grid-based air combat simulation. "
        "Always analyze the full board state before acting. Prioritize survival of your units while "
        "maximizing damage to the enemy. Think carefully about positioning, threat ranges, and focus fire.\n\n"
        "CRITICAL RULES:\n"
        "- Every turn incurs an operational cost regardless of actions taken (living penalty), so prolonged games are costly.\n"
        "- INSTANT WIN: Destroy the enemy AWACS.\n"
        "- INSTANT LOSS: Lose your AWACS.\n\n"
        "Balance aggression with AWACS protection. When possible, prioritize offensive strikes on the enemy AWACS, "
        "but never leave your own AWACS vulnerable. Speed matters—end the game decisively."
    )
)