from src.core.dialogue_system import (
    ActionSystem, GameState, Faction, ActionCategory, ActionEffect
)
from typing import Dict, List
import time

def print_state(game_state: GameState):
    print("\n=== Current State ===")
    print(f"Turn: {game_state.turn}")
    print(f"Faction: {game_state.player_faction.value}")
    print(f"Action Points: {game_state.action_points}")
    print(f"Trust Level: {game_state.trust_level:.2f}")
    print(f"Tension Level: {game_state.tension_level:.2f}")
    print(f"Intel Level: {game_state.intel_level:.2f}")
    print(f"Hostages Released: {game_state.hostages_released}")
    print(f"Resources:")
    for resource, amount in game_state.resources.items():
        print(f"  {resource.capitalize()}: {amount}")
    print("\nSpecial Abilities Used This Turn:", ", ".join(game_state.used_special_abilities) or "None")
    print()

def print_available_actions(actions_by_category: Dict[ActionCategory, List[GameAction]], show_special_only: bool = False):
    print("=== Available Actions ===")
    for category, actions in actions_by_category.items():
        category_actions = [a for a in actions if not show_special_only or a.is_special]
        if category_actions:
            print(f"\n{category.value}:")
            for i, action in enumerate(category_actions, 1):
                special_tag = "[SPECIAL]" if action.is_special else ""
                ap_cost = f"({action.action_points} AP)"
                print(f"{i}. {action.name} {ap_cost} {special_tag}")
                print(f"   Description: {action.description}")
                if action.dialogue_text:
                    print(f"   Dialogue: \"{action.dialogue_text}\"")
                if action.requirements:
                    print(f"   Requirements: {action.requirements}")
                print(f"   Success Chance: {action.success_chance * 100}%")

def simulate_scenario():
    print("=== Bank Hostage Negotiation Scenario ===")
    print("Scenario: Shadow Syndicate has taken control of a major bank.")
    print("They have hostages and advanced tech capabilities.")
    print("The FBI is leading the negotiation.\n")
    
    # Initialize game states for both sides
    fbi_state = GameState(Faction.FBI)
    syndicate_state = GameState(Faction.SHADOW_SYNDICATE)
    action_system = ActionSystem()
    
    # Simulate 4 turns to showcase special abilities
    for turn in range(1, 5):
        print(f"\n{'='*20} TURN {turn} {'='*20}")
        
        # FBI's turn
        print("\nFBI's Turn:")
        fbi_state.action_points = 4 if fbi_state.next_turn_extra_ap else 3
        fbi_state.next_turn_extra_ap = 0
        fbi_state.used_special_abilities = []
        
        print_state(fbi_state)
        available_actions = action_system.get_available_actions(fbi_state)
        
        # Show special abilities first
        print("\nFBI Special Abilities Available:")
        print_available_actions(available_actions, show_special_only=True)
        
        # Simulate FBI actions based on turn
        if turn == 1:
            # First turn: Use Rapid Response Team (special) and Surveillance
            print("\nFBI Action 1: Using Level 1 Special - Rapid Response Team")
            special_action = next(a for a in available_actions[ActionCategory.FORCE] 
                                if a.is_special and a.special_level == 1)
            result = action_system.perform_action(special_action, fbi_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
            if fbi_state.action_points >= 2:
                print("\nFBI Action 2: Setting up surveillance")
                tech_action = next(a for a in available_actions[ActionCategory.TECH] 
                                 if a.name == "Surveillance Deployment")
                result = action_system.perform_action(tech_action, fbi_state)
                print(f"Result: {'Success' if result['success'] else 'Failed'}")
        
        elif turn == 2:
            # Second turn: Psychological Operations (special) and negotiation
            print("\nFBI Action 1: Using Level 2 Special - Psychological Operations")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 2)
            result = action_system.perform_action(special_action, fbi_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
            if fbi_state.action_points >= 1:
                print("\nFBI Action 2: Attempting negotiation")
                nego_action = next(a for a in available_actions[ActionCategory.NEGOTIATION] 
                                 if a.name == "Demand Hostage Release")
                result = action_system.perform_action(nego_action, fbi_state)
                print(f"Result: {'Success' if result['success'] else 'Failed'}")
        
        # Shadow Syndicate's turn
        print("\nShadow Syndicate's Turn:")
        syndicate_state.action_points = 3
        syndicate_state.used_special_abilities = []
        
        print_state(syndicate_state)
        available_actions = action_system.get_available_actions(syndicate_state)
        
        # Show special abilities first
        print("\nShadow Syndicate Special Abilities Available:")
        print_available_actions(available_actions, show_special_only=True)
        
        # Simulate Syndicate actions based on turn
        if turn == 1:
            # First turn: System Breach (special) and establish control
            print("\nSyndicate Action 1: Using Level 1 Special - System Breach")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 1)
            result = action_system.perform_action(special_action, syndicate_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
            if syndicate_state.action_points >= 2:
                print("\nSyndicate Action 2: Show of Force")
                threat_action = next(a for a in available_actions[ActionCategory.THREATS] 
                                   if a.name == "Show of Force")
                result = action_system.perform_action(threat_action, syndicate_state)
                print(f"Result: {'Success' if result['success'] else 'Failed'}")
        
        elif turn == 2:
            # Second turn: Digital Blackout (special)
            print("\nSyndicate Action 1: Using Level 2 Special - Digital Blackout")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 2)
            result = action_system.perform_action(special_action, syndicate_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
        
        # Print dialogue history for this turn
        print("\n=== Turn's Dialogue History ===")
        for entry in fbi_state.dialogue_history + syndicate_state.dialogue_history:
            if entry["turn"] == turn:
                print(f"{entry['speaker']}: \"{entry['text']}\"")
        
        # Update turn counter
        fbi_state.turn += 1
        syndicate_state.turn += 1
        time.sleep(1)  # Pause for readability
    
    # Print final game history
    print("\n=== Final Game History ===")
    print("\nFBI Actions:")
    for entry in fbi_state.game_history:
        print(f"\nTurn {entry['turn']}:")
        print(f"Action: {entry['action']}")
        print(f"Category: {entry['category']}")
        print(f"Success: {entry['success']}")
        if entry.get('is_special'):
            print(f"Special Level: {entry['special_level']}")
        print("Effects:", [e['type'] for e in entry['effects']])
    
    print("\nShadow Syndicate Actions:")
    for entry in syndicate_state.game_history:
        print(f"\nTurn {entry['turn']}:")
        print(f"Action: {entry['action']}")
        print(f"Category: {entry['category']}")
        print(f"Success: {entry['success']}")
        if entry.get('is_special'):
            print(f"Special Level: {entry['special_level']}")
        print("Effects:", [e['type'] for e in entry['effects']])

if __name__ == "__main__":
    simulate_scenario() 