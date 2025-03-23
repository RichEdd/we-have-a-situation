from enum import Enum, auto
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random

class Faction(Enum):
    # Law Enforcement Factions
    FBI = "Federal Bureau of Investigation"
    CIA = "Central Intelligence Agency"
    LOCAL_PD = "Local Police Department"
    
    # Criminal Factions
    SHADOW_SYNDICATE = "Shadow Syndicate"  # Tech-savvy international crime organization
    RED_DRAGON_TRIAD = "Red Dragon Triad"  # Traditional organized crime group
    LIBERATION_FRONT = "Liberation Front"   # Political extremist organization

class ActionCategory(Enum):
    DIALOGUE = "Dialogue"
    RESOURCES = "Resources"
    FORCE = "Force"
    TECH = "Tech"
    NEGOTIATION = "Negotiation"
    THREATS = "Threats"

class DialogueType(Enum):
    DEMAND = "demand"
    THREAT = "threat"
    EMPATHY = "empathy"
    REASON = "reason"
    DECEPTION = "deception"
    INFORMATION = "information"
    NEGOTIATION = "negotiation"
    CONCESSION = "concession"

class ActionEffect(Enum):
    STRESS_INCREASE = "stress_increase"
    STRESS_DECREASE = "stress_decrease"
    TRUST_INCREASE = "trust_increase"
    TRUST_DECREASE = "trust_decrease"
    MORALE_INCREASE = "morale_increase"
    MORALE_DECREASE = "morale_decrease"
    TENSION_INCREASE = "tension_increase"
    TENSION_DECREASE = "tension_decrease"
    HOSTAGE_RELEASE = "hostage_release"
    DEMAND_ACCEPTED = "demand_accepted"
    INTEL_GAINED = "intel_gained"
    THREAT_ESCALATION = "threat_escalation"
    RESOURCE_GAIN = "resource_gain"
    RESOURCE_LOSS = "resource_loss"
    TACTICAL_ADVANTAGE = "tactical_advantage"
    TACTICAL_DISADVANTAGE = "tactical_disadvantage"
    EXTRA_ACTION_POINTS = "extra_action_points"
    DISABLE_COMMUNICATIONS = "disable_communications"
    MASS_PANIC = "mass_panic"
    INSIDER_INTEL = "insider_intel"
    MEDIA_MANIPULATION = "media_manipulation"
    CYBER_ADVANTAGE = "cyber_advantage"

@dataclass
class GameAction:
    def __init__(self, name: str, category: ActionCategory, action_points: int,
                 description: str, success_chance: float = 0.8):
        self.name = name
        self.category = category
        self.action_points = action_points
        self.description = description
        self.success_chance = success_chance
        self.effects = []
    
    def perform(self, game_state) -> bool:
        """Perform the action and return whether it was successful."""
        success = random.random() < self.success_chance
        
        # Update game state based on action
        game_state.update_state_after_action(self.name, self.category.value, success)
        
        return success
    
    def get_effects(self) -> List[Dict]:
        """Get the effects of this action."""
        return self.effects

class GameState:
    def __init__(self, player_faction: Faction):
        self.player_faction = player_faction
        self.turn = 1
        self.action_points = 3
        self.used_special_abilities = []
        self.next_turn_extra_ap = 0
        
        # Core metrics
        self.trust_level = 0.5
        self.tension_level = 0.5
        self.intel_level = 0.2
        
        # Resources
        self.resources = {
            'personnel': 5,
            'equipment': 3,
            'intel': 2,
            'medical': 2
        }
        
        # Hostage situation
        self.total_hostages = 8
        self.hostages_released = 0
        self.hostages_wounded = 0
        self.hostages_killed = 0
        
        # Tactical advantages
        self.tactical_positions = {
            'snipers': False,
            'breach_team': False,
            'surveillance': False,
            'negotiator': True,  # Start with negotiator in position
        }
        
        # Time pressure
        self.max_turns = 15
        self.hostage_deadline = 10  # Turns until first hostage execution
        
        # Demands tracking
        self.demands = {
            'money': 1000000,
            'transport': False,
            'prisoner_release': False
        }
        self.demands_met = {
            'money': 0,
            'transport': False,
            'prisoner_release': False
        }
        
        # Game state tracking
        self.game_over = False
        self.victory = False
        self.defeat_reason = None
        
        # History
        self.dialogue_history = []
        self.game_history = []
        
        # Special conditions
        self.communications_disabled = False
        self.power_cut = False
        self.media_presence = True
        
        # Hostage taker state
        self.hostage_taker_morale = 0.7
        self.hostage_taker_aggression = 0.3
        self.demands_urgency = 0.4
    
    def check_game_over(self) -> bool:
        """Check if game is over and determine victory/defeat."""
        # Victory conditions
        if self.hostages_released == self.total_hostages:
            self.game_over = True
            self.victory = True
            return True
            
        if (self.trust_level > 0.8 and self.tension_level < 0.3 and 
            self.hostage_taker_morale < 0.3):
            # Peaceful surrender
            self.game_over = True
            self.victory = True
            return True
        
        # Defeat conditions
        if self.hostages_killed > 0:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Hostages killed"
            return True
            
        if self.tension_level >= 1.0:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Situation escalated out of control"
            return True
            
        if self.turn >= self.max_turns:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Time ran out"
            return True
            
        if self.hostage_deadline <= 0 and self.demands_met['money'] < self.demands['money']:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Failed to meet demands before deadline"
            return True
        
        return False
    
    def get_objectives(self) -> List[Dict[str, any]]:
        """Get current mission objectives and their status."""
        objectives = [
            {
                'text': f"Rescue hostages ({self.hostages_released}/{self.total_hostages})",
                'complete': self.hostages_released == self.total_hostages,
                'failed': self.hostages_killed > 0,
                'priority': 1
            },
            {
                'text': f"Maintain control (Tension: {int(self.tension_level*100)}%)",
                'complete': self.tension_level < 0.3,
                'failed': self.tension_level >= 0.8,
                'priority': 2
            },
            {
                'text': f"Build trust (Trust: {int(self.trust_level*100)}%)",
                'complete': self.trust_level > 0.7,
                'failed': self.trust_level <= 0.2,
                'priority': 3
            }
        ]
        
        # Add time-sensitive objectives
        if self.hostage_deadline > 0:
            objectives.append({
                'text': f"Meet demands ({self.hostage_deadline} turns remaining)",
                'complete': self.demands_met['money'] >= self.demands['money'],
                'failed': self.hostage_deadline <= 0,
                'priority': 4
            })
        
        # Add tactical objectives based on state
        if not self.tactical_positions['surveillance']:
            objectives.append({
                'text': "Establish surveillance",
                'complete': self.tactical_positions['surveillance'],
                'failed': False,
                'priority': 5
            })
        
        return objectives
    
    def update_state_after_action(self, action: GameAction, success: bool):
        """Update game state after an action is performed."""
        # Update tactical positions
        if action.name == "Position Snipers" and success:
            self.tactical_positions['snipers'] = True
        elif action.name == "Surveillance Deployment" and success:
            self.tactical_positions['surveillance'] = True
        elif action.name == "Deploy Breach Team" and success:
            self.tactical_positions['breach_team'] = True
        
        # Update hostage situation based on trust/tension
        if self.tension_level >= 0.8 and random.random() < 0.3:
            self.hostages_wounded += 1
            
        # Update deadline
        if action.category == ActionCategory.NEGOTIATION and success:
            self.hostage_deadline += 1  # Buying time through negotiation
        
        # Update hostage taker state
        if success:
            if action.category == ActionCategory.FORCE:
                self.hostage_taker_morale -= 0.1
                self.hostage_taker_aggression += 0.2
            elif action.category == ActionCategory.NEGOTIATION:
                if self.trust_level > 0.6:
                    self.hostage_taker_morale -= 0.05
                    self.demands_urgency -= 0.1
        
        # Check for game over
        self.check_game_over()

class DialogueSystem:
    def __init__(self):
        self.dialogue_options = {
            ActionCategory.DIALOGUE: [
                GameAction(
                    "Open Communication",
                    ActionCategory.DIALOGUE,
                    1,
                    "Attempt to establish initial contact with hostage takers",
                    0.9
                ),
                GameAction(
                    "Empathize",
                    ActionCategory.DIALOGUE,
                    1,
                    "Show understanding of their situation to build trust",
                    0.8
                ),
                GameAction(
                    "Gather Information",
                    ActionCategory.DIALOGUE,
                    2,
                    "Ask questions to learn more about their demands and situation",
                    0.7
                ),
                GameAction(
                    "Assert Authority",
                    ActionCategory.DIALOGUE,
                    2,
                    "Establish control over the conversation",
                    0.6
                )
            ],
            ActionCategory.RESOURCES: [
                GameAction(
                    "Deploy Units",
                    ActionCategory.RESOURCES,
                    2,
                    "Position additional units around the perimeter",
                    0.9
                ),
                GameAction(
                    "Request Equipment",
                    ActionCategory.RESOURCES,
                    2,
                    "Call for specialized equipment",
                    0.8
                ),
                GameAction(
                    "Medical Standby",
                    ActionCategory.RESOURCES,
                    1,
                    "Position medical teams nearby",
                    1.0
                ),
                GameAction(
                    "Allocate Resources",
                    ActionCategory.RESOURCES,
                    2,
                    "Redistribute available resources for better efficiency",
                    0.85
                )
            ],
            ActionCategory.FORCE: [
                GameAction(
                    "Position Snipers",
                    ActionCategory.FORCE,
                    3,
                    "Set up sniper positions for tactical advantage",
                    0.7
                ),
                GameAction(
                    "Deploy Breach Team",
                    ActionCategory.FORCE,
                    3,
                    "Position breach team for potential entry",
                    0.8
                ),
                GameAction(
                    "Show of Force",
                    ActionCategory.FORCE,
                    2,
                    "Demonstrate tactical capabilities",
                    0.6
                ),
                GameAction(
                    "Tactical Positioning",
                    ActionCategory.FORCE,
                    2,
                    "Optimize unit positions for maximum coverage",
                    0.75
                )
            ],
            ActionCategory.TECH: [
                GameAction(
                    "Surveillance Deployment",
                    ActionCategory.TECH,
                    2,
                    "Set up surveillance equipment",
                    0.9
                ),
                GameAction(
                    "Communications Intercept",
                    ActionCategory.TECH,
                    2,
                    "Attempt to intercept their communications",
                    0.7
                ),
                GameAction(
                    "Thermal Imaging",
                    ActionCategory.TECH,
                    1,
                    "Use thermal cameras to gather intel",
                    0.8
                ),
                GameAction(
                    "Network Analysis",
                    ActionCategory.TECH,
                    2,
                    "Analyze digital communications patterns",
                    0.75
                )
            ],
            ActionCategory.NEGOTIATION: [
                GameAction(
                    "Make Offer",
                    ActionCategory.NEGOTIATION,
                    2,
                    "Present a negotiated offer",
                    0.7
                ),
                GameAction(
                    "Request Good Faith",
                    ActionCategory.NEGOTIATION,
                    2,
                    "Ask for a show of good faith",
                    0.6
                ),
                GameAction(
                    "Propose Timeline",
                    ActionCategory.NEGOTIATION,
                    1,
                    "Establish a timeline for resolution",
                    0.8
                ),
                GameAction(
                    "Demand Concession",
                    ActionCategory.NEGOTIATION,
                    2,
                    "Firmly request specific concessions",
                    0.65
                )
            ],
            ActionCategory.THREATS: [
                GameAction(
                    "Verbal Warning",
                    ActionCategory.THREATS,
                    1,
                    "Issue a warning about consequences",
                    0.5
                ),
                GameAction(
                    "Demonstrate Resolve",
                    ActionCategory.THREATS,
                    2,
                    "Show willingness to take action",
                    0.6
                ),
                GameAction(
                    "Ultimatum",
                    ActionCategory.THREATS,
                    3,
                    "Present final terms",
                    0.4
                ),
                GameAction(
                    "Pressure Tactics",
                    ActionCategory.THREATS,
                    2,
                    "Apply psychological pressure to force compliance",
                    0.55
                )
            ]
        }

class ActionSystem:
    def __init__(self):
        self.dialogue_system = DialogueSystem()
    
    def get_available_actions(self, param):
        """Get available actions based on input parameter."""
        # Check if the parameter is an ActionCategory
        if isinstance(param, ActionCategory):
            return self.dialogue_system.dialogue_options.get(param, [])
        
        # Otherwise assume it's a GameState
        elif hasattr(param, 'action_points'):
            game_state = param
            available_actions = {category: [] for category in ActionCategory}
            
            # Add dialogue actions that the player can afford
            for category, action_list in self.dialogue_system.dialogue_options.items():
                available_actions[category] = []
                for action in action_list:
                    if action.action_points <= game_state.action_points:
                        available_actions[category].append(action)
            
            return available_actions
        
        # Fallback to empty list
        return []

    def _initialize_actions(self) -> Dict[ActionCategory, List[GameAction]]:
        actions = {category: [] for category in ActionCategory}
        
        # Dialogue Actions (1 AP)
        actions[ActionCategory.DIALOGUE].extend([
            GameAction(
                name="Empathetic Appeal",
                description="Show understanding and compassion to build trust",
                category=ActionCategory.DIALOGUE,
                action_points=1,
                effects=[ActionEffect.TRUST_INCREASE, ActionEffect.TENSION_DECREASE],
                requirements={},
                success_chance=0.8,
                dialogue_text="I understand this is a difficult situation. Let's work together."
            ),
            GameAction(
                name="Aggressive Stance",
                description="Take a hard line to show authority",
                category=ActionCategory.DIALOGUE,
                action_points=1,
                effects=[ActionEffect.TENSION_INCREASE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={},
                success_chance=0.6,
                dialogue_text="Don't test our patience. You're only making this worse."
            ),
        ])
        
        # Resource Actions (1-2 AP)
        actions[ActionCategory.RESOURCES].extend([
            GameAction(
                name="Deploy Medical Team",
                description="Position medical personnel for potential casualties",
                category=ActionCategory.RESOURCES,
                action_points=2,
                effects=[ActionEffect.TRUST_INCREASE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"medical": 2},
                success_chance=0.9
            ),
            GameAction(
                name="Request Backup",
                description="Call for additional personnel",
                category=ActionCategory.RESOURCES,
                action_points=1,
                effects=[ActionEffect.RESOURCE_GAIN, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 5},
                success_chance=0.95
            ),
        ])
        
        # Force Actions (2-3 AP)
        actions[ActionCategory.FORCE].extend([
            GameAction(
                name="Position Snipers",
                description="Deploy tactical shooters to key positions",
                category=ActionCategory.FORCE,
                action_points=2,
                effects=[ActionEffect.TACTICAL_ADVANTAGE, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 3},
                success_chance=0.85,
                faction_specific=[Faction.FBI, Faction.LOCAL_PD]
            ),
            GameAction(
                name="Breach and Clear",
                description="Forceful entry to end the situation",
                category=ActionCategory.FORCE,
                action_points=3,
                effects=[ActionEffect.TENSION_INCREASE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"personnel": 8, "equipment": 4},
                success_chance=0.7
            ),
        ])
        
        # Tech Actions (1-2 AP)
        actions[ActionCategory.TECH].extend([
            GameAction(
                name="Surveillance Deployment",
                description="Set up electronic surveillance",
                category=ActionCategory.TECH,
                action_points=2,
                effects=[ActionEffect.INTEL_GAINED, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"equipment": 2},
                success_chance=0.9
            ),
            GameAction(
                name="Communications Intercept",
                description="Monitor communications",
                category=ActionCategory.TECH,
                action_points=1,
                effects=[ActionEffect.INTEL_GAINED],
                requirements={"equipment": 1},
                success_chance=0.8,
                faction_specific=[Faction.FBI, Faction.CIA]
            ),
        ])
        
        # Negotiation Actions (1-3 AP)
        actions[ActionCategory.NEGOTIATION].extend([
            GameAction(
                name="Offer Deal",
                description="Propose terms for resolution",
                category=ActionCategory.NEGOTIATION,
                action_points=2,
                effects=[ActionEffect.TRUST_INCREASE, ActionEffect.TENSION_DECREASE],
                requirements={},
                success_chance=0.75,
                dialogue_text="We're prepared to offer you a deal. Let's discuss terms."
            ),
            GameAction(
                name="Demand Hostage Release",
                description="Push for hostage release",
                category=ActionCategory.NEGOTIATION,
                action_points=1,
                effects=[ActionEffect.HOSTAGE_RELEASE, ActionEffect.TENSION_INCREASE],
                requirements={},
                success_chance=0.6,
                dialogue_text="Release a hostage as a show of good faith."
            ),
        ])
        
        # Threat Actions (2-3 AP)
        actions[ActionCategory.THREATS].extend([
            GameAction(
                name="Show of Force",
                description="Demonstrate available firepower",
                category=ActionCategory.THREATS,
                action_points=2,
                effects=[ActionEffect.TENSION_INCREASE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"personnel": 5, "equipment": 2},
                success_chance=0.7,
                dialogue_text="Look outside. You're surrounded by our tactical teams."
            ),
            GameAction(
                name="Ultimate Threat",
                description="Final warning before force",
                category=ActionCategory.THREATS,
                action_points=3,
                effects=[ActionEffect.TENSION_INCREASE, ActionEffect.TRUST_DECREASE],
                requirements={},
                success_chance=0.5,
                dialogue_text="This is your last chance. Surrender now or face the consequences."
            ),
        ])
        
        # Add faction-specific special abilities
        self._add_fbi_specials(actions)
        self._add_cia_specials(actions)
        self._add_local_pd_specials(actions)
        self._add_shadow_syndicate_specials(actions)
        self._add_red_dragon_triad_specials(actions)
        self._add_liberation_front_specials(actions)
        
        return actions
    
    def perform_action(self, action: GameAction, game_state: GameState) -> Dict:
        """Perform an action and return the results."""
        # Check if special ability has already been used this turn
        if action.is_special and action.name in game_state.used_special_abilities:
            return {
                "action": action.name,
                "category": action.category.value,
                "success": False,
                "effects": [],
                "turn": game_state.turn,
                "error": "Special ability already used this turn"
            }

        success = random.random() < action.success_chance
        effects_applied = []
        
        # Apply effects if successful
        if success:
            for effect in action.effects:
                effect_result = self._apply_effect(effect, game_state)
                effects_applied.append(effect_result)
                
                # Handle CIA level 3 special ability
                if action.is_special and action.special_level == 3 and game_state.player_faction == Faction.CIA:
                    if effect == ActionEffect.EXTRA_ACTION_POINTS:
                        game_state.next_turn_extra_ap = 1  # Will grant 4 AP next turn
        
        # Deduct action points
        game_state.action_points -= action.action_points
        
        # Track used special ability
        if action.is_special:
            game_state.used_special_abilities.append(action.name)
        
        # Record in appropriate history
        result = {
            "action": action.name,
            "category": action.category.value,
            "success": success,
            "effects": effects_applied,
            "turn": game_state.turn,
            "is_special": action.is_special,
            "special_level": action.special_level
        }
        
        if action.dialogue_text:
            game_state.dialogue_history.append({
                "turn": game_state.turn,
                "speaker": game_state.player_faction.value,
                "text": action.dialogue_text,
                "success": success
            })
        
        game_state.game_history.append(result)
        return result
    
    def _apply_effect(self, effect: ActionEffect, game_state: GameState) -> Dict:
        """Apply an effect to the game state."""
        effect_magnitude = 0.1
        
        if effect in [ActionEffect.TRUST_INCREASE, ActionEffect.TRUST_DECREASE]:
            game_state.trust_level = max(0.0, min(1.0, 
                game_state.trust_level + (effect_magnitude if effect == ActionEffect.TRUST_INCREASE else -effect_magnitude)))
        elif effect in [ActionEffect.TENSION_INCREASE, ActionEffect.TENSION_DECREASE]:
            game_state.tension_level = max(0.0, min(1.0,
                game_state.tension_level + (effect_magnitude if effect == ActionEffect.TENSION_INCREASE else -effect_magnitude)))
        elif effect == ActionEffect.RESOURCE_GAIN:
            for resource in game_state.resources:
                game_state.resources[resource] += 1
        elif effect == ActionEffect.RESOURCE_LOSS:
            for resource in game_state.resources:
                game_state.resources[resource] = max(0, game_state.resources[resource] - 1)
        elif effect == ActionEffect.EXTRA_ACTION_POINTS:
            game_state.next_turn_extra_ap = 1
        
        return {
            "type": effect.value,
            "magnitude": effect_magnitude
        }

    def _add_fbi_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # FBI Special Abilities
        actions[ActionCategory.FORCE].extend([
            GameAction(
                name="Rapid Response Team",
                description="Deploy elite FBI tactical unit for immediate action",
                category=ActionCategory.FORCE,
                action_points=1,
                effects=[ActionEffect.TACTICAL_ADVANTAGE, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 3},
                success_chance=0.9,
                faction_specific=[Faction.FBI],
                is_special=True,
                special_level=1
            ),
            GameAction(
                name="Psychological Operations",
                description="Use FBI behavioral analysts to predict and influence hostage taker actions",
                category=ActionCategory.TECH,
                action_points=2,
                effects=[ActionEffect.INTEL_GAINED, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"intel": 2},
                success_chance=0.85,
                faction_specific=[Faction.FBI],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="Critical Incident Response",
                description="Activate full FBI crisis response protocol",
                category=ActionCategory.FORCE,
                action_points=3,
                effects=[ActionEffect.TACTICAL_ADVANTAGE, ActionEffect.RESOURCE_GAIN, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 5, "equipment": 3},
                success_chance=0.8,
                faction_specific=[Faction.FBI],
                is_special=True,
                special_level=3
            )
        ])

    def _add_cia_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # CIA Special Abilities
        actions[ActionCategory.TECH].extend([
            GameAction(
                name="Covert Intelligence",
                description="Access classified intel about the situation",
                category=ActionCategory.TECH,
                action_points=1,
                effects=[ActionEffect.INTEL_GAINED, ActionEffect.INSIDER_INTEL],
                requirements={},
                success_chance=0.9,
                faction_specific=[Faction.CIA],
                is_special=True,
                special_level=1
            ),
            GameAction(
                name="Media Blackout",
                description="Control media coverage and information flow",
                category=ActionCategory.TECH,
                action_points=2,
                effects=[ActionEffect.MEDIA_MANIPULATION, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"equipment": 2},
                success_chance=0.85,
                faction_specific=[Faction.CIA],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="Shadow Protocol",
                description="Activate deep cover assets (Grants 4 AP next turn)",
                category=ActionCategory.TECH,
                action_points=3,
                effects=[ActionEffect.EXTRA_ACTION_POINTS, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={},
                success_chance=0.8,
                faction_specific=[Faction.CIA],
                is_special=True,
                special_level=3
            )
        ])

    def _add_local_pd_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # Local PD Special Abilities
        actions[ActionCategory.RESOURCES].extend([
            GameAction(
                name="Local Knowledge",
                description="Use intimate knowledge of the area and community",
                category=ActionCategory.RESOURCES,
                action_points=1,
                effects=[ActionEffect.INTEL_GAINED, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={},
                success_chance=0.9,
                faction_specific=[Faction.LOCAL_PD],
                is_special=True,
                special_level=1
            ),
            GameAction(
                name="Community Outreach",
                description="Leverage local connections for additional support",
                category=ActionCategory.RESOURCES,
                action_points=2,
                effects=[ActionEffect.RESOURCE_GAIN, ActionEffect.TRUST_INCREASE],
                requirements={"personnel": 2},
                success_chance=0.85,
                faction_specific=[Faction.LOCAL_PD],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="City-Wide Lockdown",
                description="Implement full city security protocols",
                category=ActionCategory.FORCE,
                action_points=3,
                effects=[ActionEffect.TACTICAL_ADVANTAGE, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 6},
                success_chance=0.8,
                faction_specific=[Faction.LOCAL_PD],
                is_special=True,
                special_level=3
            )
        ])

    def _add_shadow_syndicate_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # Shadow Syndicate Special Abilities
        actions[ActionCategory.TECH].extend([
            GameAction(
                name="System Breach",
                description="Hack into local security systems",
                category=ActionCategory.TECH,
                action_points=1,
                effects=[ActionEffect.CYBER_ADVANTAGE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"equipment": 1},
                success_chance=0.9,
                faction_specific=[Faction.SHADOW_SYNDICATE],
                is_special=True,
                special_level=1
            ),
            GameAction(
                name="Digital Blackout",
                description="Disable communications in the area",
                category=ActionCategory.TECH,
                action_points=2,
                effects=[ActionEffect.DISABLE_COMMUNICATIONS, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"equipment": 2},
                success_chance=0.85,
                faction_specific=[Faction.SHADOW_SYNDICATE],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="Ghost Protocol",
                description="Activate sleeper agents in key positions",
                category=ActionCategory.TECH,
                action_points=3,
                effects=[ActionEffect.INSIDER_INTEL, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"intel": 3},
                success_chance=0.8,
                faction_specific=[Faction.SHADOW_SYNDICATE],
                is_special=True,
                special_level=3
            )
        ])

    def _add_red_dragon_triad_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # Red Dragon Triad Special Abilities
        actions[ActionCategory.FORCE].extend([
            GameAction(
                name="Intimidation Tactics",
                description="Use reputation to increase pressure",
                category=ActionCategory.FORCE,
                action_points=1,
                effects=[ActionEffect.TENSION_INCREASE, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={},
                success_chance=0.9,
                faction_specific=[Faction.RED_DRAGON_TRIAD],
                is_special=True,
                special_level=1
            ),
            GameAction(
                name="Underground Network",
                description="Utilize criminal contacts for support",
                category=ActionCategory.RESOURCES,
                action_points=2,
                effects=[ActionEffect.RESOURCE_GAIN, ActionEffect.INTEL_GAINED],
                requirements={"intel": 2},
                success_chance=0.85,
                faction_specific=[Faction.RED_DRAGON_TRIAD],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="Triad Enforcers",
                description="Call in elite enforcers",
                category=ActionCategory.FORCE,
                action_points=3,
                effects=[ActionEffect.TACTICAL_ADVANTAGE, ActionEffect.TENSION_INCREASE],
                requirements={"personnel": 4},
                success_chance=0.8,
                faction_specific=[Faction.RED_DRAGON_TRIAD],
                is_special=True,
                special_level=3
            )
        ])

    def _add_liberation_front_specials(self, actions: Dict[ActionCategory, List[GameAction]]):
        # Liberation Front Special Abilities
        actions[ActionCategory.THREATS].extend([
            GameAction(
                name="Ideological Speech",
                description="Appeal to political ideals to gain support",
                category=ActionCategory.DIALOGUE,
                action_points=1,
                effects=[ActionEffect.MORALE_INCREASE, ActionEffect.TRUST_DECREASE],
                requirements={},
                success_chance=0.9,
                faction_specific=[Faction.LIBERATION_FRONT],
                is_special=True,
                special_level=1,
                dialogue_text="Our cause is just! The people will support us!"
            ),
            GameAction(
                name="Media Statement",
                description="Release propaganda to influence public opinion",
                category=ActionCategory.TECH,
                action_points=2,
                effects=[ActionEffect.MEDIA_MANIPULATION, ActionEffect.TENSION_INCREASE],
                requirements={"equipment": 1},
                success_chance=0.85,
                faction_specific=[Faction.LIBERATION_FRONT],
                is_special=True,
                special_level=2
            ),
            GameAction(
                name="Mass Uprising",
                description="Trigger widespread civil unrest",
                category=ActionCategory.FORCE,
                action_points=3,
                effects=[ActionEffect.MASS_PANIC, ActionEffect.TACTICAL_ADVANTAGE],
                requirements={"intel": 3, "personnel": 5},
                success_chance=0.8,
                faction_specific=[Faction.LIBERATION_FRONT],
                is_special=True,
                special_level=3
            )
        ]) 