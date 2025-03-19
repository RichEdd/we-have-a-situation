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
    """Available action categories."""
    NEGOTIATION = "Negotiation"
    TACTICAL = "Tactical"
    SPECIAL = "Special"

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
    """Represents an action that can be taken in the game."""
    
    def __init__(self, name, category, action_points, description, success_chance=0.8):
        self.name = name
        self.category = category
        self.action_points = action_points
        self.description = description
        self.success_chance = success_chance
        self.is_special = False
        self.special_level = 0
        self.requirements = []
        self.effects = []
        self.failure_effects = []
    
    def add_requirement(self, req):
        """Add a requirement for this action."""
        self.requirements.append(req)
    
    def add_effect(self, effect):
        """Add a success effect for this action."""
        self.effects.append(effect)
    
    def add_failure_effect(self, effect):
        """Add a failure effect for this action."""
        self.failure_effects.append(effect)
    
    def set_special(self, level=1):
        """Mark this action as a special ability with given level."""
        self.is_special = True
        self.special_level = level
    
    def check_requirements(self, game_state):
        """Check if all requirements are met."""
        return all(req.check(game_state) for req in self.requirements)
    
    def apply_effects(self, game_state, success=True):
        """Apply the effects of this action."""
        effects = self.effects if success else self.failure_effects
        for effect in effects:
            effect.apply(game_state)
        return [str(effect) for effect in effects]

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
        
        # Tactical information
        self.tactical_info = [
            "Negotiator in position",
            "Building perimeter secured",
            "Awaiting tactical team deployment"
        ]
        
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
    
    def add_history_entry(self, entry: Dict):
        """Add an entry to the game history."""
        self.game_history.append(entry)
        
        # If the entry has dialogue text, add it to dialogue history
        if 'dialogue_text' in entry:
            self.dialogue_history.append({
                'turn': self.turn,
                'speaker': self.player_faction.value,
                'text': entry['dialogue_text'],
                'success': entry.get('success', True)
            })
    
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

    def end_turn(self):
        """Process end of turn effects."""
        self.turn += 1
        
        # Reset action points and add any bonus
        self.action_points = 3 + self.next_turn_extra_ap
        self.next_turn_extra_ap = 0
        
        # Update time-sensitive values
        self.hostage_deadline -= 1
        
        # Update tension based on deadline
        if self.hostage_deadline <= 2:
            self.tension_level = min(1.0, self.tension_level + 0.1)
        
        # Random events based on state
        if random.random() < 0.3:  # 30% chance each turn
            if self.tension_level > 0.7:
                # High tension event
                self.tactical_info.append("Hostage takers are becoming more agitated")
                self.hostage_taker_aggression += 0.1
            elif self.trust_level > 0.7:
                # High trust event
                self.tactical_info.append("Negotiations are progressing well")
                self.hostage_taker_morale -= 0.1
        
        # Trim tactical info to keep only recent messages
        if len(self.tactical_info) > 5:
            self.tactical_info = self.tactical_info[-5:]
        
        # Check for game over conditions
        self.check_game_over()

class DialogueSystem:
    def __init__(self):
        self.dialogue_options = {
            ActionCategory.NEGOTIATION: [
                GameAction(
                    "Open Communication",
                    ActionCategory.NEGOTIATION,
                    1,
                    "Attempt to establish initial contact with hostage takers",
                    0.9
                ),
                GameAction(
                    "Empathize",
                    ActionCategory.NEGOTIATION,
                    1,
                    "Show understanding of their situation to build trust",
                    0.8
                ),
                GameAction(
                    "Gather Information",
                    ActionCategory.NEGOTIATION,
                    2,
                    "Ask questions to learn more about their demands and situation",
                    0.7
                )
            ],
            ActionCategory.TACTICAL: [
                GameAction(
                    "Deploy Units",
                    ActionCategory.TACTICAL,
                    2,
                    "Position additional units around the perimeter",
                    0.9
                ),
                GameAction(
                    "Request Equipment",
                    ActionCategory.TACTICAL,
                    2,
                    "Call for specialized equipment",
                    0.8
                ),
                GameAction(
                    "Medical Standby",
                    ActionCategory.TACTICAL,
                    1,
                    "Position medical teams nearby",
                    1.0
                ),
                GameAction(
                    "Position Snipers",
                    ActionCategory.TACTICAL,
                    3,
                    "Set up sniper positions for tactical advantage",
                    0.7
                ),
                GameAction(
                    "Deploy Breach Team",
                    ActionCategory.TACTICAL,
                    3,
                    "Position breach team for potential entry",
                    0.8
                ),
                GameAction(
                    "Show of Force",
                    ActionCategory.TACTICAL,
                    2,
                    "Demonstrate tactical capabilities",
                    0.6
                )
            ],
            ActionCategory.SPECIAL: [
                GameAction(
                    "Rapid Response",
                    ActionCategory.SPECIAL,
                    3,
                    "Deploy elite tactical unit for immediate action",
                    0.8
                ),
                GameAction(
                    "Psychological Operations",
                    ActionCategory.SPECIAL,
                    2,
                    "Use behavioral analysts to predict and influence hostage taker actions",
                    0.7
                ),
                GameAction(
                    "Critical Incident Response",
                    ActionCategory.SPECIAL,
                    4,
                    "Activate full crisis response protocol",
                    0.6
                )
            ]
        }
        
        # Add effects to actions
        for actions in self.dialogue_options.values():
            for action in actions:
                if action.category == ActionCategory.NEGOTIATION:
                    action.add_effect(GameEffect("trust", 1))
                    action.add_failure_effect(GameEffect("tension", 1))
                elif action.category == ActionCategory.TACTICAL:
                    action.add_effect(GameEffect("tactical_readiness", 1))
                    action.add_failure_effect(GameEffect("tension", 2))
                elif action.category == ActionCategory.SPECIAL:
                    action.add_effect(GameEffect("trust", 2))
                    action.add_effect(GameEffect("tension", -1))
                    action.add_failure_effect(GameEffect("tension", 3))
                    action.set_special()

class ActionSystem:
    """Manages game actions and their execution."""
    
    def __init__(self):
        self.actions = {
            ActionCategory.NEGOTIATION: [],
            ActionCategory.TACTICAL: [],
            ActionCategory.SPECIAL: []
        }
        self._setup_actions()
    
    def _setup_actions(self):
        """Initialize all available actions."""
        # Negotiation actions
        self.add_action(GameAction(
            "Negotiate",
            ActionCategory.NEGOTIATION,
            2,
            "Attempt to negotiate with the hostage takers.",
            0.8
        ))
        
        self.add_action(GameAction(
            "Show Empathy",
            ActionCategory.NEGOTIATION,
            1,
            "Show understanding for the hostage takers' position.",
            0.9
        ))
        
        self.add_action(GameAction(
            "Gather Information",
            ActionCategory.NEGOTIATION,
            2,
            "Ask questions to learn more about their demands.",
            0.7
        ))
        
        # Tactical actions
        self.add_action(GameAction(
            "Deploy Units",
            ActionCategory.TACTICAL,
            2,
            "Position additional units around the perimeter.",
            0.8
        ))
        
        self.add_action(GameAction(
            "Position Snipers",
            ActionCategory.TACTICAL,
            3,
            "Set up sniper positions for tactical advantage.",
            0.7
        ))
        
        self.add_action(GameAction(
            "Deploy Breach Team",
            ActionCategory.TACTICAL,
            3,
            "Position breach team for potential entry.",
            0.8
        ))
        
        # Special abilities
        defuse = GameAction(
            "Defuse Crisis",
            ActionCategory.SPECIAL,
            4,
            "Attempt to completely defuse the situation.",
            0.6
        )
        defuse.set_special(2)
        self.add_action(defuse)
        
        rapid_trust = GameAction(
            "Rapid Trust Building",
            ActionCategory.SPECIAL,
            3,
            "Quickly establish trust through advanced negotiation techniques.",
            0.7
        )
        rapid_trust.set_special(1)
        self.add_action(rapid_trust)
    
    def add_action(self, action):
        """Add an action to the available actions."""
        self.actions[action.category].append(action)
    
    def get_available_actions(self, game_state):
        """Get all currently available actions."""
        available = {}
        for category, actions in self.actions.items():
            available[category] = [
                action for action in actions
                if not (action.is_special and action.name in game_state.used_special_abilities)
            ]
        return available
    
    def perform_action(self, action, game_state):
        """Attempt to perform an action and return the result."""
        # Check if we have enough action points
        if game_state.action_points < action.action_points:
            return {'success': False, 'reason': 'Not enough action points'}
        
        # Determine success
        success = random.random() < action.success_chance
        
        # Apply effects based on success
        if success:
            # Update trust and tension
            if action.category == ActionCategory.NEGOTIATION:
                game_state.trust_level = min(1.0, game_state.trust_level + 0.1)
            elif action.category == ActionCategory.TACTICAL:
                game_state.tension_level = min(1.0, game_state.tension_level + 0.1)
            elif action.category == ActionCategory.SPECIAL:
                game_state.trust_level = min(1.0, game_state.trust_level + 0.2)
                game_state.tension_level = max(0.0, game_state.tension_level - 0.1)
        else:
            # Failed action increases tension
            game_state.tension_level = min(1.0, game_state.tension_level + 0.2)
        
        return {
            'success': success,
            'effects': []  # We'll handle effects through game state updates
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

class GameEffect:
    """Represents an effect that can be applied to the game state."""
    
    def __init__(self, resource, amount=1):
        self.resource = resource
        self.amount = amount
    
    def apply(self, game_state):
        """Apply this effect to the game state."""
        game_state.update_resource(self.resource, self.amount)
    
    def __str__(self):
        """Get a string representation of this effect."""
        return f"{self.resource} {'increased' if self.amount > 0 else 'decreased'} by {abs(self.amount)}" 