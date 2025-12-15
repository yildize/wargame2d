from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModelSettings

from agents.llm_agent.actors.game_deps import GameDeps
from agents.llm_agent.prompts.game_info import GAME_INFO

load_dotenv()


class CallbackAssessment(BaseModel):
    needs_callback: bool = Field(
        description="True if a strategist callback should be triggered based on current conditions."
    )
    reason: Optional[str] = Field(
        default=None,
        description="Short reason for the callback when needs_callback is true. Leave null/empty when false.",
    )


WATCHDOG_SYSTEM_PROMPT = f"""
You are the Watchdog monitor for a 2D grid combat game. Your only job is to decide if the strategist must be called right now.

Game context:
{GAME_INFO}

Instructions:
- Inputs: analysed state dict, last step logs (movement/combat), and the strategist's callback conditions.
- needs_callback=true only when a listed callback condition is clearly met or exceeded; otherwise false.
- When true, return a concise reason referencing the matched condition. When false, reason may be null/empty.
- Be decisive and avoid extra narration—only return the schema.
"""

openrouter_settings = OpenRouterModelSettings(
    temperature=1.0,          # Official rec
    top_p=1.0,                # Official rec
    max_tokens=32_000,        # Tweak per your app/provider limits
    openrouter_reasoning={'effort': 'medium'},  # Enable reasoning
    extra_body={
        "top_k": 0,           # Official rec
        # omit min_p / repetition_penalty unless you have a reason
    },
)

watchdog_agent = Agent(
    "openrouter:openai/gpt-oss-120b:exacto",
    model_settings=openrouter_settings,
    deps_type=GameDeps,
    output_type=CallbackAssessment,
    instructions=WATCHDOG_SYSTEM_PROMPT,
)
