from src.core.dialogue_system import (
    ActionSystem, GameState, Faction, ActionCategory
)

def print_state(game_state: GameState):
    print("\n=== Current State ===")
    print(f"Turn: {game_state.turn}")
    print(f"Action Points: {game_state.action_points}")
    print(f"Trust Level: {game_state.trust_level:.2f}")
    print(f"Tension Level: {game_state.tension_level:.2f}")
    print(f"Resources:")
    for resource, amount in game_state.resources.items():
        print(f"  {resource.capitalize()}: {amount}")
    print()

def print_available_actions(actions_by_category):
    print("=== Available Actions ===")
    for category, actions in actions_by_category.items():
        if actions:
            print(f"\n{category.value}:")
            for i, action in enumerate(actions, 1):
                print(f"{i}. {action.name} ({action.action_points} AP)")
                print(f"   Description: {action.description}")
                if action.dialogue_text:
                    print(f"   Dialogue: \"{action.dialogue_text}\"")

def main():
    # Initialize the game with FBI as the player faction
    game_state = GameState(Faction.FBI)
    action_system = ActionSystem()
    
    print("=== Bank Hostage Negotiation Scenario ===")
    print(f"Playing as: {game_state.player_faction.value}")
    
    # Simulate 3 turns
    for turn in range(1, 4):
        print(f"\n=== Turn {turn} ===")
        game_state.action_points = 3  # Reset action points
        
        print_state(game_state)
        
        # Get available actions
        available_actions = action_system.get_available_actions(game_state)
        print_available_actions(available_actions)
        
        # Simulate choosing and performing actions
        # For demonstration, we'll choose one action from different categories each turn
        if turn == 1:
            # First turn: Start with dialogue and surveillance
            dialogue_action = next(iter(available_actions[ActionCategory.DIALOGUE]))
            print("\nPerforming action: Dialogue - ", dialogue_action.name)
            result = action_system.perform_action(dialogue_action, game_state)
            print("Result:", "Success" if result["success"] else "Failed")
            
            if game_state.action_points > 0:
                tech_action = next(iter(available_actions[ActionCategory.TECH]))
                print("\nPerforming action: Tech - ", tech_action.name)
                result = action_system.perform_action(tech_action, game_state)
                print("Result:", "Success" if result["success"] else "Failed")
        
        elif turn == 2:
            # Second turn: Try negotiation and resources
            negotiation_action = next(iter(available_actions[ActionCategory.NEGOTIATION]))
            print("\nPerforming action: Negotiation - ", negotiation_action.name)
            result = action_system.perform_action(negotiation_action, game_state)
            print("Result:", "Success" if result["success"] else "Failed")
            
            if game_state.action_points > 0:
                resource_action = next(iter(available_actions[ActionCategory.RESOURCES]))
                print("\nPerforming action: Resource - ", resource_action.name)
                result = action_system.perform_action(resource_action, game_state)
                print("Result:", "Success" if result["success"] else "Failed")
        
        else:
            # Third turn: Show of force
            threat_action = next(iter(available_actions[ActionCategory.THREATS]))
            print("\nPerforming action: Threat - ", threat_action.name)
            result = action_system.perform_action(threat_action, game_state)
            print("Result:", "Success" if result["success"] else "Failed")
        
        game_state.turn += 1
    
    # Print final dialogue history
    print("\n=== Dialogue History ===")
    for entry in game_state.dialogue_history:
        print(f"\nTurn {entry['turn']}:")
        print(f"Speaker: {entry['speaker']}")
        print(f"Text: \"{entry['text']}\"")
        print(f"Success: {entry['success']}")
    
    # Print final game history
    print("\n=== Game History ===")
    for entry in game_state.game_history:
        print(f"\nTurn {entry['turn']}:")
        print(f"Action: {entry['action']}")
        print(f"Category: {entry['category']}")
        print(f"Success: {entry['success']}")
        print("Effects:", [e['type'] for e in entry['effects']])

if __name__ == "__main__":
    main() 