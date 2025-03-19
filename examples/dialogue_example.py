from src.core.dialogue_system import DialogueSystem, DialogueType, DialogueEffect, DialogueOption

def print_state(dialogue_system):
    print(f"\nCurrent State:")
    print(f"Trust Level: {dialogue_system.trust_level:.2f}")
    print(f"Tension Level: {dialogue_system.tension_level:.2f}")
    print(f"Intel Level: {dialogue_system.intel_level:.2f}")
    print(f"Hostages Released: {dialogue_system.hostages_released}")
    print(f"Demands Met: {dialogue_system.demands_met}\n")

def main():
    # Initialize the dialogue system
    dialogue_system = DialogueSystem()
    
    # Set up initial game state
    game_state = {
        "current_turn": 1,
        "elderly_hostage_critical": True,
        "hostages_count": 5,
        "role": "negotiator"
    }
    
    print("=== Bank Hostage Negotiation Example ===")
    print_state(dialogue_system)
    
    # Example dialogue sequence
    dialogues = [
        DialogueOption(
            text="I understand this is a difficult situation. Let's work together to find a solution.",
            type=DialogueType.EMPATHY,
            effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
            requirements={},
            success_chance=0.8
        ),
        DialogueOption(
            text="We need immediate medical attention for the elderly hostage. Their life could depend on it.",
            type=DialogueType.REASON,
            effects=[DialogueEffect.HOSTAGE_RELEASE],
            requirements={"elderly_hostage_critical": True},
            success_chance=0.7
        ),
        DialogueOption(
            text="The building is surrounded. There's no escape, but we can negotiate terms.",
            type=DialogueType.THREAT,
            effects=[DialogueEffect.TENSION_INCREASE, DialogueEffect.TRUST_DECREASE],
            requirements={},
            success_chance=0.6
        ),
        DialogueOption(
            text="If you release another hostage, I can guarantee your demands will be heard.",
            type=DialogueType.NEGOTIATION,
            effects=[DialogueEffect.HOSTAGE_RELEASE, DialogueEffect.TRUST_INCREASE],
            requirements={"hostages_count": ">1"},
            success_chance=0.75
        )
    ]
    
    # Process each dialogue option
    for i, option in enumerate(dialogues, 1):
        print(f"\nTurn {i}:")
        print(f"Negotiator: {option.text}")
        
        result = dialogue_system.process_dialogue(option, game_state)
        print(f"Response: {result['response']}")
        
        if result['success']:
            print("The approach was successful!")
        else:
            print("The approach was not successful.")
        
        print_state(dialogue_system)
        game_state["current_turn"] += 1
    
    # Print final dialogue history
    print("\n=== Dialogue History ===")
    for entry in dialogue_system.dialogue_history:
        print(f"\nTurn {entry['turn']}:")
        print(f"Text: {entry['text']}")
        print(f"Type: {entry['type']}")
        print(f"Success: {entry['success']}")
        print(f"Response: {entry['response']}")

if __name__ == "__main__":
    main() 