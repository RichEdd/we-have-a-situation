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

def print_faction_abilities(faction: Faction, action_system: ActionSystem):
    print(f"\n=== {faction.value} Special Abilities ===")
    game_state = GameState(faction)
    available_actions = action_system.get_available_actions(game_state)
    
    for category in ActionCategory:
        special_actions = [a for a in available_actions.get(category, []) 
                         if a.is_special and a.faction_specific == [faction]]
        if special_actions:
            print(f"\n{category.value}:")
            for action in special_actions:
                print(f"\nLevel {action.special_level} - {action.name} ({action.action_points} AP)")
                print(f"Description: {action.description}")
                if action.dialogue_text:
                    print(f"Dialogue: \"{action.dialogue_text}\"")
                print(f"Requirements: {action.requirements}")
                print(f"Success Chance: {action.success_chance * 100}%")
                print(f"Effects: {[e.value for e in action.effects]}")

def simulate_turn(game_state: GameState, action_system: ActionSystem, turn: int):
    print(f"\n{'='*20} TURN {turn} {'='*20}")
    print(f"\n{game_state.player_faction.value}'s Turn:")
    
    # Reset action points (CIA might get 4 AP from previous turn's special ability)
    game_state.action_points = 4 if game_state.next_turn_extra_ap else 3
    game_state.next_turn_extra_ap = 0
    game_state.used_special_abilities = []
    
    print_state(game_state)
    available_actions = action_system.get_available_actions(game_state)
    
    # Demonstrate special ability usage based on faction
    if game_state.player_faction == Faction.FBI:
        if turn == 1:
            # FBI Turn 1: Rapid Response Team (Level 1)
            print("\nUsing Level 1 Special - Rapid Response Team")
            special_action = next(a for a in available_actions[ActionCategory.FORCE] 
                                if a.is_special and a.special_level == 1)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 2:
            # FBI Turn 2: Psychological Operations (Level 2)
            print("\nUsing Level 2 Special - Psychological Operations")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 2)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 3:
            # FBI Turn 3: Critical Incident Response (Level 3)
            print("\nUsing Level 3 Special - Critical Incident Response")
            special_action = next(a for a in available_actions[ActionCategory.FORCE] 
                                if a.is_special and a.special_level == 3)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
    
    elif game_state.player_faction == Faction.CIA:
        if turn == 1:
            # CIA Turn 1: Covert Intelligence (Level 1)
            print("\nUsing Level 1 Special - Covert Intelligence")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 1)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 2:
            # CIA Turn 2: Media Blackout (Level 2)
            print("\nUsing Level 2 Special - Media Blackout")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 2)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 3:
            # CIA Turn 3: Shadow Protocol (Level 3) - Grants 4 AP next turn
            print("\nUsing Level 3 Special - Shadow Protocol")
            special_action = next(a for a in available_actions[ActionCategory.TECH] 
                                if a.is_special and a.special_level == 3)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            if result['success']:
                print("Shadow Protocol activated - Will have 4 AP next turn!")
    
    elif game_state.player_faction == Faction.LOCAL_PD:
        if turn == 1:
            # Local PD Turn 1: Local Knowledge (Level 1)
            print("\nUsing Level 1 Special - Local Knowledge")
            special_action = next(a for a in available_actions[ActionCategory.RESOURCES] 
                                if a.is_special and a.special_level == 1)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 2:
            # Local PD Turn 2: Community Outreach (Level 2)
            print("\nUsing Level 2 Special - Community Outreach")
            special_action = next(a for a in available_actions[ActionCategory.RESOURCES] 
                                if a.is_special and a.special_level == 2)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
            
        elif turn == 3:
            # Local PD Turn 3: City-Wide Lockdown (Level 3)
            print("\nUsing Level 3 Special - City-Wide Lockdown")
            special_action = next(a for a in available_actions[ActionCategory.FORCE] 
                                if a.is_special and a.special_level == 3)
            result = action_system.perform_action(special_action, game_state)
            print(f"Result: {'Success' if result['success'] else 'Failed'}")
    
    # Use remaining AP for standard actions if available
    if game_state.action_points > 0:
        print(f"\nRemaining AP: {game_state.action_points}")
        print("Available for standard actions...")

def compare_factions():
    print("=== Law Enforcement Faction Comparison ===")
    action_system = ActionSystem()
    
    # Show each faction's special abilities
    for faction in [Faction.FBI, Faction.CIA, Faction.LOCAL_PD]:
        print_faction_abilities(faction, action_system)
        print("\n" + "="*50)
    
    # Demonstrate each faction in action
    print("\n=== Faction Gameplay Demonstrations ===")
    
    for faction in [Faction.FBI, Faction.CIA, Faction.LOCAL_PD]:
        print(f"\n\n{'#'*20} {faction.value} Demonstration {'#'*20}")
        game_state = GameState(faction)
        
        # Simulate 3 turns to show all special ability levels
        for turn in range(1, 4):
            simulate_turn(game_state, action_system, turn)
            game_state.turn += 1
            time.sleep(1)  # Pause for readability
        
        # Show final game history
        print(f"\n=== {faction.value} Action History ===")
        for entry in game_state.game_history:
            print(f"\nTurn {entry['turn']}:")
            print(f"Action: {entry['action']}")
            if entry.get('is_special'):
                print(f"Special Level: {entry['special_level']}")
            print("Effects:", [e['type'] for e in entry['effects']])
        
        print("\n" + "="*50)

if __name__ == "__main__":
    compare_factions() 