import json
from typing import List, Literal, Optional

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from pydantic_ai.models.openrouter import OpenRouterModelSettings

from agents.llm_agent.actors.game_deps import GameDeps
from agents.llm_agent.prompts.game_info import GAME_INFO
from agents.llm_agent.prompts.analyst import ANALYST_SYSTEM_PROMPT, ANALYST_USER_PROMPT_TEMPLATE

load_dotenv()


class Position(BaseModel):
    x: int = Field(description="X coordinate on the grid.")
    y: int = Field(description="Y coordinate on the grid.")


class Action(BaseModel):
    """
    Flat action schema for simpler LLM outputs. Type is an enum; other fields are conditional by type.
    """

    type: Literal["MOVE", "SHOOT", "TOGGLE", "WAIT"] = Field(
        description="Action keyword. Allowed: MOVE | SHOOT | TOGGLE | WAIT.",
        examples=["MOVE", "SHOOT", "TOGGLE", "WAIT"],
    )
    direction: Optional[Literal["UP", "DOWN", "LEFT", "RIGHT"]] = Field(
        default=None,
        description="MOVE only: direction to move one cell.",
        examples=["UP", "DOWN", "LEFT", "RIGHT"],
    )
    destination: Optional[Position] = Field(
        default=None,
        description="MOVE only: destination after moving (x,y).",
    )
    target: Optional[int] = Field(
        default=None,
        description="SHOOT only: enemy unit id to target.",
    )
    on: Optional[bool] = Field(
        default=None,
        description="TOGGLE only: true to activate SAM radar/weapon system, false to go dark/stealth (SAM units only).",
    )

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
    spatial_status: str = Field(
        description="Short narrative of formation posture, positioning relative to enemies, and maneuver space."
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
    situation_summary: str = Field(
        description="Overall tactical snapshot combining threats, openings, and intent for the next turn."
    )

# Use OpenRouterModelSettings for reasoning
# openrouter_settings = OpenRouterModelSettings(
#     temperature=0.7,
#     top_p=0.8,
#     max_tokens=32_000,
#     openrouter_reasoning={'effort': 'high'},  # This is the key!
#     extra_body={
#         "top_k": 20,
#         "min_p": 0,
#         "repetition_penalty": 1.05,
#     }
# )

openrouter_settings = OpenRouterModelSettings(
    # temperature=1.0,
    # top_p=1.0,
    max_tokens=1024 * 32,
    openrouter_reasoning={"effort": "low"},
)
analyst_agent = Agent(
    "openrouter:deepseek/deepseek-v3.1-terminus:exacto",
    model_settings=openrouter_settings,
    deps_type=GameDeps,
    output_type=GameAnalysis,
)

@analyst_agent.instructions
def full_prompt() -> str:
    return ANALYST_SYSTEM_PROMPT.format(GAME_INFO=GAME_INFO)
