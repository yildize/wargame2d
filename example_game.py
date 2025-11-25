from env.scenario import create_mixed_scenario
from env.core.types import Team
from agents import AgentSpec
from game_runner import run_single_game, run_multiple_games


def main():
    """Run example games."""
    
    print("Grid Combat Environment - Example Game Runner")
    print("=" * 80)
    
    # Create scenario
    scenario = create_mixed_scenario()
    print(f"Loaded scenario: {scenario}")
    blue_count = sum(1 for e in scenario.entities if e.team == Team.BLUE)
    red_count = sum(1 for e in scenario.entities if e.team == Team.RED)
    print(f"  Blue entities: {blue_count}")
    print(f"  Red entities: {red_count}")
    print()
    
    # Attach agent specs to the scenario
    scenario.agents = [
        AgentSpec(type="random", team=Team.BLUE, name="Blue Random", init_params={"seed": 42}),
        AgentSpec(type="random", team=Team.RED, name="Red Random", init_params={"seed": 43}),
    ]
    
    # =========================================================================
    # Example 1: Run a single game with verbose output
    # =========================================================================
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Single Game (Verbose)")
    print("=" * 80)
    
    state = run_single_game(
        scenario=scenario,
        verbose=True,
        max_turns=100  # Limit turns for demonstration
    )
    winner = state["world"].winner
    print(f"Winner: {winner.name if winner else 'DRAW'}")
    
    # =========================================================================
    # Example 2: Run multiple games and analyze statistics
    # =========================================================================
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Multiple Games (10 episodes)")
    print("=" * 80)
    
    results = run_multiple_games(
        scenario=scenario,
        num_games=10,
        verbose=False  # Don't print each turn
    )
    
    # Analyze results
    blue_wins = sum(1 for r in results if r["world"].winner == Team.BLUE)
    red_wins = sum(1 for r in results if r["world"].winner == Team.RED)
    draws = sum(1 for r in results if r["world"].winner is None)
    
    print("\nStatistics across 10 games:")
    print(f"  Blue wins: {blue_wins} ({blue_wins/len(results)*100:.1f}%)")
    print(f"  Red wins:  {red_wins} ({red_wins/len(results)*100:.1f}%)")
    print(f"  Draws:     {draws} ({draws/len(results)*100:.1f}%)")
    
    # Print individual results
    print("\nIndividual Game Results:")
    print(f"{'Game':<6} {'Winner':<10} {'Turns':<8}")
    print("-" * 80)
    for i, r in enumerate(results, 1):
        winner_str = r["world"].winner.name if r["world"].winner else "DRAW"
        print(f"{i:<6} {winner_str:<10} {r['world'].turn:<8}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
