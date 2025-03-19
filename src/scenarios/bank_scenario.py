from typing import List, Dict
from .base_scenario import Scenario, LocationType, EnvironmentFeature, LocationProperties
from core.dialogue_system import DialogueType, DialogueEffect, DialogueOption

class BankScenario(Scenario):
    def __init__(self):
        location = LocationProperties(
            type=LocationType.BANK,
            size="medium",
            features=[
                EnvironmentFeature.SECURITY_CAMERAS,
                EnvironmentFeature.MULTIPLE_EXITS,
                EnvironmentFeature.CIVILIANS_NEARBY,
                EnvironmentFeature.COVER_SPOTS,
                EnvironmentFeature.COMMUNICATION_SYSTEMS
            ],
            civilian_density=7,
            security_level=8,
            response_time=5
        )
        super().__init__("The Last Withdrawal", location)
        self._setup_scenario()
    
    def _setup_scenario(self):
        # Setup negotiator objectives
        self.add_objective("negotiator", {
            "type": "primary",
            "description": "Ensure all hostages are released safely",
            "success_conditions": ["all_hostages_safe"],
            "reward": 100
        })
        self.add_objective("negotiator", {
            "type": "secondary",
            "description": "Gather intelligence about the hostage takers",
            "success_conditions": ["intel_gathered"],
            "reward": 50
        })
        
        # Setup hostage taker objectives
        self.add_objective("hostage_taker", {
            "type": "primary",
            "description": "Secure $500,000 and escape",
            "success_conditions": ["money_secured", "successful_escape"],
            "reward": 100
        })
        self.add_objective("hostage_taker", {
            "type": "secondary",
            "description": "Keep your true identity hidden",
            "success_conditions": ["identity_protected"],
            "reward": 50
        })
        
        # Add special conditions
        self.add_special_condition({
            "type": "time_pressure",
            "description": "Police SWAT team will arrive in 10 turns",
            "trigger_turn": 10,
            "effect": "increase_tension"
        })
        self.add_special_condition({
            "type": "hostage_health",
            "description": "Elderly hostage needs medication within 5 turns",
            "trigger_turn": 5,
            "effect": "critical_situation"
        })
    
    def get_negotiator_options(self, game_state: dict) -> List[DialogueOption]:
        """Get context-sensitive dialogue options for the negotiator."""
        options = []
        
        # Basic dialogue options
        options.extend([
            DialogueOption(
                text="Let's start by establishing some trust. How can we work together to resolve this peacefully?",
                type=DialogueType.EMPATHY,
                effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
                requirements={},
                success_chance=0.8
            ),
            DialogueOption(
                text="The building is surrounded. Let's focus on getting everyone out safely.",
                type=DialogueType.INFORMATION,
                effects=[DialogueEffect.TENSION_INCREASE],
                requirements={},
                success_chance=0.7
            )
        ])
        
        # Situational options based on game state
        if game_state.get("elderly_hostage_critical", False):
            options.append(
                DialogueOption(
                    text="One of the hostages needs medical attention. Let me send in some medication.",
                    type=DialogueType.REASON,
                    effects=[DialogueEffect.TRUST_INCREASE],
                    requirements={},
                    success_chance=0.9
                )
            )
        
        if game_state.get("trust_level", 0) > 0.6:
            options.append(
                DialogueOption(
                    text="You've shown good faith. I can guarantee leniency if we end this now.",
                    type=DialogueType.REASON,
                    effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
                    requirements={"trust_level": ">0.6"},
                    success_chance=0.85
                )
            )
        
        return options
    
    def get_hostage_taker_options(self, game_state: dict) -> List[DialogueOption]:
        """Get context-sensitive dialogue options for the hostage taker."""
        options = []
        
        # Basic dialogue options
        options.extend([
            DialogueOption(
                text="I want a helicopter on the roof and safe passage, or things get ugly.",
                type=DialogueType.DEMAND,
                effects=[DialogueEffect.TENSION_INCREASE],
                requirements={},
                success_chance=0.4
            ),
            DialogueOption(
                text="Show me you're serious by pulling back the police.",
                type=DialogueType.DEMAND,
                effects=[DialogueEffect.TENSION_INCREASE],
                requirements={},
                success_chance=0.5
            )
        ])
        
        # Situational options
        if game_state.get("hostages_count", 0) > 2:
            options.append(
                DialogueOption(
                    text="I'll release one hostage as a sign of good faith.",
                    type=DialogueType.REASON,
                    effects=[DialogueEffect.TRUST_INCREASE, DialogueEffect.TENSION_DECREASE],
                    requirements={"hostages_count": ">2"},
                    success_chance=0.9
                )
            )
        
        if game_state.get("tension_level", 0) > 0.7:
            options.append(
                DialogueOption(
                    text="Don't test me! *fires warning shot*",
                    type=DialogueType.THREAT,
                    effects=[DialogueEffect.TENSION_INCREASE, DialogueEffect.TRUST_DECREASE],
                    requirements={"tension_level": ">0.7"},
                    success_chance=0.3
                )
            )
        
        return options
    
    def get_initial_state(self) -> dict:
        """Get the initial state configuration for this scenario."""
        base_state = super().get_initial_state()
        
        # Add scenario-specific state
        base_state.update({
            "hostages": [
                {
                    "id": 1,
                    "type": "bank_manager",
                    "status": "captured",
                    "health": 100,
                    "stress": 80,
                    "special": "knows_vault_combination"
                },
                {
                    "id": 2,
                    "type": "elderly_customer",
                    "status": "captured",
                    "health": 70,
                    "stress": 90,
                    "special": "needs_medication"
                },
                {
                    "id": 3,
                    "type": "security_guard",
                    "status": "captured",
                    "health": 90,
                    "stress": 60,
                    "special": "trained_professional"
                },
                {
                    "id": 4,
                    "type": "bank_teller",
                    "status": "captured",
                    "health": 100,
                    "stress": 75,
                    "special": "knows_layout"
                },
                {
                    "id": 5,
                    "type": "civilian",
                    "status": "captured",
                    "health": 100,
                    "stress": 70,
                    "special": None
                }
            ],
            "environment": {
                "time_of_day": "morning",
                "weather": "clear",
                "police_presence": 5,
                "media_attention": 7,
                "civilian_crowd": 8,
                "vault_status": "locked",
                "power_status": "on",
                "communication_status": "operational"
            },
            "special_items": {
                "vault_combination": False,
                "security_footage": True,
                "hostage_medication": False,
                "police_blueprints": True
            }
        })
        
        return base_state 