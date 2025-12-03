# Grid Combat Environment - Architecture Map

Short orientation for contributors: what lives where and how a turn flows.

## Top-Level Pieces
- `env/`: Simulation engine (core types, entities, mechanics, `Scenario`, `GridCombatEnv`).
- `agents/`: Agent base class, registry/factory, built-ins (random, greedy). Registry auto-discovers agent modules on first use.
- `runtime/frame.py`: Turn snapshot with serialization for UI/API.
- `runtime/runner.py`: Orchestrates a game; wires `Scenario` + agents into `GridCombatEnv` and emits `Frame`s.
- `infra/`: Shared paths (`infra/paths.py`) and logging setup (`infra/logger.py`).
- `api/app.py`: FastAPI surface exposing `/start`, `/step`, `/status`.
- `ui/ops_deck.html`: Static control panel that calls the API and renders frames.
- `main.py`: Local launcher that configures logging and runs API + UI together.

## How a Turn Moves
1. Client posts a scenario (and optional saved `world`) to `POST /start`; API builds a `Scenario` and a global `GameRunner`.
2. `POST /step` asks the runner to advance one turn; runner gathers actions from each agent, calls `env.step()`, and returns a serialized `Frame` (pre-step world + observations + action metadata).
3. UI polls `/status` and calls `/step` to drive the match, rendering directly from the `Frame` payload.

## Runner in Brief (`runtime/runner.py`)
- Holds a `GridCombatEnv` plus prepared agents from `scenario.agents`.
- `step()`: clone world with fresh observations → ask agents for actions → call `env.step()` → stash terminal world when done → return a `Frame` of the pre-step world.
- `run()` loops until done; `get_final_frame()` returns the terminal world without actions.

## Core Engine Notes (`env/`)
- `GridCombatEnv`: turn sequencing: tick cooldowns → movement → sensors → combat → victory checks → return `(state, rewards, done, StepInfo)`.
- `Scenario`: single source of truth for grid size, rules, entities, seed, and agent specs; `from_dict`/`to_dict` support API use.
- `WorldState`: mutable game state; `SensorSystem.refresh_all_observations()` keeps fog-of-war in sync on snapshots.
- Mechanics are stateless modules under `env/mechanics`; entities live under `env/entities`; foundational types under `env/core`; spatial structures under `env/world`.

## Agents
- Register via `@register_agent("key")` inside `agents/<your_agent>.py`; registry auto-discovers modules.
- `AgentSpec` in scenarios names the agent (`type` key or full import path) and init params; factory resolves and instantiates via the registry.

## API Surface (FastAPI)
- `POST /start`: `{ "scenario": {...}, "world": {...}|null }` → create runner.
- `POST /step`: `{ "injections": {...}|null }` → advance one turn, return `Frame`.
- `GET /status`: heartbeat (`active`, `turn`, `step`, `done`).

## Logging & Paths
- Logging configured once in `main.py` via `infra.logger.configure_logging()`; per-module loggers via `get_logger(__name__)` log to console + `storage/logs/backend.log`.
- Common paths (project root, storage, UI entrypoint) live in `infra/paths.py`.
