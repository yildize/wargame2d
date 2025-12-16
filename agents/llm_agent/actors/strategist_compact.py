from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModelSettings

from agents.llm_agent.actors.game_deps import GameDeps
from agents.llm_agent.prompts.game_info import GAME_INFO
from agents.llm_agent.prompts.tactics import TACTICAL_GUIDE

load_dotenv()


class PhaseOutline(BaseModel):
    name: str = Field(description="Short label for the phase (e.g., 'Phase 1: Secure radar net').")
    objective: str = Field(description="One-sentence objective for this phase; no per-unit actions.")
    success_markers: List[str] = Field(
        description="2-3 clear markers that mean this phase is achieved or should transition."
    )


class CurrentPhasePlan(BaseModel):
    phase: str = Field(description="Name/number of the active phase.")
    intent: str = Field(description="One sentence on the operational intent right now.")
    approach: List[str] = Field(
        description="3-6 concise bullets on how we intend to execute this phase (operational, not per-unit commands)."
    )
    risks: List[str] = Field(
        description="2-3 succinct risks or constraints to watch (e.g., 'SAM cooldown', 'low missiles on #7')."
    )


class UnitRole(BaseModel):
    entity_id: int = Field(description="Friendly unit id.")
    role: str = Field(description="One-sentence role for this unit aligned to the current phase.")
    posture: str = Field(
        description="One-word stance: 'OFFENSE', 'DEFENSE', 'SCOUT', 'ESCORT', or 'RESERVE'.",
    )


class CallbackCondition(BaseModel):
    condition: str = Field(description="Specific observable trigger to call strategist again.")


class StrategyOutput(BaseModel):
    multi_phase_outline: List[PhaseOutline] = Field(
        description="2-4 phase outline from now to victory; concise, no unit actions."
    )
    current_phase_plan: CurrentPhasePlan = Field(
        description="Current phase intent, approach, and key risks."
    )
    unit_roles: List[UnitRole] = Field(description="Role assignment per friendly unit for this phase.")
    callbacks: List[CallbackCondition] = Field(
        description="Observable triggers for a strategist callback; keep each tight."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence (0-1) that this plan will hold through the next few turns.",
    )


STRATEGIST_COMPACT_PROMPT = f"""
You are the Strategic Director for a 2D combat grid game. The user message contains the latest compact state snapshot and analysis.

Use the GAME INFO and TACTICAL GUIDE as doctrine.

## GAME INFO
{GAME_INFO}

## TACTICAL GUIDE
{TACTICAL_GUIDE}

## RULES FOR YOU
- Fog-of-war discipline: only reason about enemies we actually see or have last-known info for; do not invent hidden units.
- Stay strategic: no per-unit commands, no action strings—only roles and operational intent.
- Be concise: keep bullets short, avoid jargon.
- Callbacks must be observable events (kills, losses, ammo/cooldown states, phase milestones), not vague feelings.

## WHAT TO PRODUCE
- 2-4 phase outline to victory (no execution detail).
- Current phase plan: name, intent, 3-6 approach bullets, and 2-3 risks.
- Roles per friendly unit (one sentence) + posture tag.
- Callback conditions list.
- Confidence 0-1.

## RESPONSE FORMAT
Return a tool call to 'final_result' using StrategyOutput schema only. No prose outside the tool call.
"""


strategist_compact_agent = Agent(
    "openrouter:deepseek/deepseek-v3.1-terminus:exacto",
    model_settings=OpenRouterModelSettings(
        max_tokens=1024 * 32,
        openrouter_reasoning={"effort": "low"},
    ),
    deps_type=GameDeps,
    output_type=StrategyOutput,
    instructions=STRATEGIST_COMPACT_PROMPT,
    output_retries=3,
)
