from core.game_engine import GameEngine, PlayerRole, PlayerAffiliation
from core.dialogue_system import DialogueSystem
from scenarios.base_scenario import create_bank_scenario
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

def display_game_state(console: Console, game_state: dict):
    """Display the current game state in a formatted way."""
    console.print("\n[bold blue]Current Game State[/bold blue]")
    
    # Display turn information
    console.print(f"\nTurn: {game_state.current_turn}")
    console.print(f"Current Player: {game_state.current_player_role.value}")
    
    # Display resources
    table = Table(title="Resources")
    table.add_column("Role")
    table.add_column("Resources")
    
    for role, player in game_state.players.items():
        resources_str = ", ".join(f"{k}: {v}" for k, v in player.resources.items())
        table.add_row(role.value, resources_str)
    
    console.print(table)

def display_dialogue_options(console: Console, options: list):
    """Display available dialogue options."""
    console.print("\n[bold green]Available Actions[/bold green]")
    
    for i, option in enumerate(options, 1):
        console.print(f"\n{i}. {option.text}")
        console.print(f"   Type: {option.type.value}")
        console.print(f"   Success Chance: {option.success_chance * 100}%")

def main():
    console = Console()
    
    # Initialize game components
    game_engine = GameEngine()
    dialogue_system = DialogueSystem()
    
    # Create and initialize a scenario
    scenario = create_bank_scenario()
    game_engine.initialize_game(scenario.get_initial_state())
    
    console.print("[bold]Welcome to We Have a Situation![/bold]")
    console.print("A turn-based hostage negotiation simulator")
    
    # Main game loop
    while True:
        # Display current game state
        display_game_state(console, game_engine.game_state)
        
        # Get current player's state
        current_player = game_engine.game_state.players[game_engine.current_player_role]
        
        # Get available dialogue options
        options = dialogue_system.get_available_options({
            "role": current_player.role.value,
            "resources": current_player.resources
        })
        
        # Display options
        display_dialogue_options(console, options)
        
        # Get player choice
        choice = Prompt.ask(
            "\nChoose your action",
            choices=[str(i) for i in range(1, len(options) + 1)]
        )
        
        # Process the chosen action
        chosen_option = options[int(choice) - 1]
        result = dialogue_system.process_dialogue(
            chosen_option,
            game_engine.game_state.__dict__
        )
        
        # Display results
        console.print("\n[bold yellow]Action Results[/bold yellow]")
        console.print(f"Success: {'[green]Yes[/green]' if result['success'] else '[red]No[/red]'}")
        
        console.print("\n[bold cyan]Response[/bold cyan]")
        console.print(result['response'])
        
        console.print("\n[bold magenta]Effects[/bold magenta]")
        for effect in result['effects']:
            console.print(f"- {effect['type']}")
            if 'new_tension' in effect:
                console.print(f"  Tension level: {effect['new_tension']:.2f}")
            if 'new_trust' in effect:
                console.print(f"  Trust level: {effect['new_trust']:.2f}")
        
        # Process turn in game engine
        game_engine.process_turn({"type": "dialogue", "option": chosen_option})
        
        # Check for game end conditions
        if game_engine._check_win_conditions():
            break
        
        # Wait for user to continue
        Prompt.ask("\nPress Enter to continue")

if __name__ == "__main__":
    main() 