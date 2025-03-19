import unittest
from src.core.dialogue_system import DialogueSystem, DialogueType, DialogueEffect, DialogueOption

class TestDialogueSystem(unittest.TestCase):
    def setUp(self):
        self.dialogue_system = DialogueSystem()
        self.base_game_state = {
            "current_turn": 1,
            "elderly_hostage_critical": True,
            "hostages_count": 5
        }
    
    def test_basic_dialogue_options(self):
        # Test negotiator options
        negotiator_state = {**self.base_game_state, "role": "negotiator"}
        options = self.dialogue_system._get_basic_options(negotiator_state)
        self.assertTrue(any(opt.type == DialogueType.EMPATHY for opt in options))
        self.assertTrue(any(opt.type == DialogueType.THREAT for opt in options))
        
        # Test hostage taker options
        hostage_taker_state = {**self.base_game_state, "role": "hostage_taker"}
        options = self.dialogue_system._get_basic_options(hostage_taker_state)
        self.assertTrue(any(opt.type == DialogueType.DEMAND for opt in options))
        self.assertTrue(any(opt.type == DialogueType.REASON for opt in options))
    
    def test_dialogue_success_calculation(self):
        option = DialogueOption(
            text="Test option",
            type=DialogueType.EMPATHY,
            effects=[DialogueEffect.TRUST_INCREASE],
            requirements={},
            success_chance=0.5
        )
        
        # Test success calculation with high trust
        self.dialogue_system.trust_level = 0.9
        success_count = sum(1 for _ in range(100) 
                          if self.dialogue_system._calculate_success(option, self.base_game_state))
        self.assertGreater(success_count, 50)  # Should succeed more often with high trust
        
        # Test success calculation with high tension
        self.dialogue_system.trust_level = 0.5
        self.dialogue_system.tension_level = 0.9
        option.type = DialogueType.THREAT
        success_count = sum(1 for _ in range(100) 
                          if self.dialogue_system._calculate_success(option, self.base_game_state))
        self.assertLess(success_count, 50)  # Should fail more often with high tension
    
    def test_dialogue_effects(self):
        # Test trust increase
        initial_trust = self.dialogue_system.trust_level
        self.dialogue_system._apply_effect(DialogueEffect.TRUST_INCREASE, self.base_game_state)
        self.assertGreater(self.dialogue_system.trust_level, initial_trust)
        
        # Test tension increase with threat escalation
        initial_tension = self.dialogue_system.tension_level
        self.dialogue_system._apply_effect(DialogueEffect.THREAT_ESCALATION, self.base_game_state)
        self.assertGreater(self.dialogue_system.tension_level, initial_tension)
        self.assertLess(self.dialogue_system.trust_level, initial_trust)
    
    def test_dialogue_processing(self):
        option = DialogueOption(
            text="I understand you're in a difficult situation.",
            type=DialogueType.EMPATHY,
            effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
            requirements={},
            success_chance=0.8
        )
        
        result = self.dialogue_system.process_dialogue(option, self.base_game_state)
        
        self.assertIn("success", result)
        self.assertIn("effects", result)
        self.assertIn("response", result)
        self.assertIn("dialogue_history", result)
        self.assertIn("state_changes", result)
        
        # Check dialogue history
        self.assertEqual(len(self.dialogue_system.dialogue_history), 1)
        entry = self.dialogue_system.dialogue_history[0]
        self.assertEqual(entry["text"], option.text)
        self.assertEqual(entry["type"], option.type.value)
        self.assertEqual(entry["turn"], 1)
    
    def test_response_generation(self):
        option = DialogueOption(
            text="Test threat",
            type=DialogueType.THREAT,
            effects=[],
            requirements={},
            success_chance=0.5
        )
        
        # Test multiple responses for the same type
        responses = set()
        for _ in range(10):
            response = self.dialogue_system._generate_response(option, True, self.base_game_state)
            responses.add(response)
        
        # Should get multiple different responses
        self.assertGreater(len(responses), 1)
    
    def test_special_conditions(self):
        option = DialogueOption(
            text="Let's focus on getting medical attention for the elderly hostage.",
            type=DialogueType.REASON,
            effects=[DialogueEffect.HOSTAGE_RELEASE],
            requirements={},
            success_chance=0.6
        )
        
        # Test with elderly hostage critical condition
        success_count = sum(1 for _ in range(100) 
                          if self.dialogue_system._calculate_success(option, self.base_game_state))
        
        # Test without elderly hostage critical condition
        normal_state = {**self.base_game_state, "elderly_hostage_critical": False}
        normal_success_count = sum(1 for _ in range(100) 
                                 if self.dialogue_system._calculate_success(option, normal_state))
        
        self.assertGreater(success_count, normal_success_count)

if __name__ == '__main__':
    unittest.main() 