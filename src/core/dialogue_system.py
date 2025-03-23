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
                 description: str, success_chance: float = 0.8, on_cooldown: bool = False,
                 effects: List = None, requirements: Dict = None, faction_specific: List = None,
                 is_special: bool = False, special_level: int = 0, dialogue_text: str = None):
        self.name = name
        self.category = category
        self.action_points = action_points
        self.description = description
        self.base_success_chance = success_chance  # Renamed to base_success_chance
        self.success_chance = success_chance  # Current calculated success chance
        self.effects = effects or []
        self.consequences = []  # New field for tracking physical/environmental consequences
        self.resource_cost = {}  # New field for tracking resource costs
        self.personnel_cost = {}  # New field for tracking personnel costs
        self.critical_threshold = 0.05  # For critical success/failure (top/bottom 5%)
        self.on_cooldown = on_cooldown
        self.requirements = requirements or {}
        self.faction_specific = faction_specific or []
        self.is_special = is_special
        self.special_level = special_level
        self.dialogue_text = dialogue_text
    
    def update_success_chance(self, game_state) -> None:
        """Update the success chance based on game state."""
        if not hasattr(game_state, 'get_dynamic_success_chance'):
            self.success_chance = self.base_success_chance
            return
            
        # Use the game state to calculate dynamic success chance
        self.success_chance = game_state.get_dynamic_success_chance(
            self.category.value, self.base_success_chance)
    
    def perform(self, game_state) -> Dict:
        """Perform the action and return result details."""
        # Update success chance based on current game state
        self.update_success_chance(game_state)
        
        # Get random roll for success determination
        roll = random.random()
        success = roll < self.success_chance
        
        # Determine if this is a critical success/failure
        critical_success = success and roll < (self.success_chance * self.critical_threshold)
        critical_failure = not success and roll > (1 - self.critical_threshold)
        partial_success = success and roll > (self.success_chance - 0.1)
        
        # Put action on cooldown if needed (for powerful actions)
        if self.action_points >= 3 or critical_success or critical_failure:
            game_state.add_action_cooldown(self.name, 3)  # 3 turn cooldown
        
        # Update game state based on action
        game_state.update_state_after_action(self.name, self.category.value, success)
        
        # Apply resource and personnel costs
        self._apply_costs(game_state)
        
        # Apply consequences based on success/failure and critical status
        consequence_results = self._apply_consequences(game_state, success, critical_success, critical_failure)
        
        # Return detailed results
        return {
            'action_name': self.name,
            'category': self.category.value,
            'success': success,
            'critical_success': critical_success,
            'critical_failure': critical_failure,
            'partial_success': partial_success,
            'roll': roll,
            'target': self.success_chance,
            'consequences': consequence_results
        }
    
    def _apply_costs(self, game_state) -> None:
        """Apply resource and personnel costs of the action."""
        # Apply resource costs
        for resource, amount in self.resource_cost.items():
            game_state.modify_player_resource(resource, -amount)
            
        # Apply personnel costs
        for personnel, amount in self.personnel_cost.items():
            game_state.modify_player_personnel(personnel, -amount)
    
    def _apply_consequences(self, game_state, success: bool, critical_success: bool, critical_failure: bool) -> List[str]:
        """Apply action consequences and return descriptions."""
        consequences = []
        
        # No consequences defined for this action
        if not self.consequences:
            return consequences
            
        # Apply each defined consequence based on success/failure
        for consequence in self.consequences:
            applied = False
            description = ""
            
            # Check probability of this consequence occurring
            probability = consequence.get('probability', 1.0)
            if random.random() > probability:
                continue
            
            # Different logic based on consequence type
            if consequence['type'] == 'environmental':
                if success or (critical_failure and consequence.get('on_critical_failure', False)):
                    condition = consequence['condition']
                    value = consequence['value']
                    prev_value = game_state.environment.get(condition, None)
                    game_state.update_environment(condition, value)
                    description = consequence.get('description', f"Environment changed: {condition} is now {value}")
                    applied = True
                    
            elif consequence['type'] == 'hostage':
                if success or (critical_failure and consequence.get('on_critical_failure', False)):
                    # Handle hostage effects (release, wound, kill)
                    effect = consequence['effect']
                    count = consequence.get('count', 1)
                    
                    # Find applicable hostages
                    applicable_hostages = [h for h in game_state.hostages_status 
                                          if h['status'] == consequence.get('required_status', 'captured')]
                    
                    # Apply to random hostages up to count
                    for _ in range(min(count, len(applicable_hostages))):
                        if not applicable_hostages:
                            break
                            
                        hostage = random.choice(applicable_hostages)
                        applicable_hostages.remove(hostage)
                        
                        if effect == 'release':
                            game_state.update_hostage_status(hostage['id'], {'status': 'released'})
                            description = f"Hostage {hostage['name']} was released"
                        elif effect == 'wound':
                            game_state.update_hostage_status(hostage['id'], 
                                                           {'status': 'wounded', 'health': max(hostage['health'] - 50, 10)})
                            description = f"Hostage {hostage['name']} was wounded"
                        elif effect == 'kill':
                            game_state.update_hostage_status(hostage['id'], {'status': 'killed', 'health': 0})
                            description = f"Hostage {hostage['name']} was killed"
                        
                        applied = True
                        
            elif consequence['type'] == 'ai_personnel':
                if success:
                    # Handle effects on AI personnel
                    personnel_type = consequence['personnel_type']
                    amount = consequence['amount']
                    game_state.modify_ai_personnel(personnel_type, amount)
                    if amount < 0:
                        description = f"Enemy lost {-amount} {personnel_type}"
                    else:
                        description = f"Enemy gained {amount} {personnel_type}"
                    applied = True
            
            elif consequence['type'] == 'resource':
                if success:
                    # Modify player resources
                    resource_type = consequence['resource_type']
                    amount = consequence['amount']
                    
                    # Apply critical success/failure scaling
                    if critical_success:
                        amount = int(amount * 1.5)
                    elif critical_failure:
                        amount = int(amount * 0.5)
                        
                    game_state.modify_player_resource(resource_type, amount)
                    
                    if amount > 0:
                        description = f"Gained {amount} {resource_type}"
                    else:
                        description = f"Lost {-amount} {resource_type}"
                    applied = True
                    
            elif consequence['type'] == 'ai_resource':
                if success:
                    # Modify AI resources
                    resource_type = consequence['resource_type']
                    amount = consequence['amount']
                    
                    # Apply critical success/failure scaling
                    if critical_success:
                        amount = int(amount * 1.5)
                    elif critical_failure:
                        amount = int(amount * 0.5)
                        
                    game_state.modify_ai_resource(resource_type, amount)
                    
                    if amount < 0:
                        description = f"Reduced enemy {resource_type} by {-amount}"
                    else:
                        description = f"Enemy gained {amount} {resource_type}"
                    applied = True
            
            elif consequence['type'] == 'tactical':
                if success:
                    # Set tactical position
                    position = consequence['position']
                    value = consequence['value']
                    game_state.set_tactical_position(position, value)
                    description = f"Secured tactical position: {position}"
                    applied = True
            
            elif consequence['type'] == 'deadline':
                if success:
                    # Modify deadline
                    amount = consequence['amount']
                    game_state.hostage_deadline += amount
                    if amount > 0:
                        description = f"Extended deadline by {amount} turns"
                    else:
                        description = f"Deadline reduced by {-amount} turns"
                    applied = True
            
            elif consequence['type'] == 'public':
                if success:
                    # Modify public perception or media control
                    public_type = consequence['public_type']
                    amount = consequence['amount']
                    
                    if public_type == 'media_control':
                        current = game_state.player_resources.get('media_control', 0)
                        game_state.player_resources['media_control'] = max(0, min(100, current + amount))
                        description = f"Media control {'+' if amount > 0 else ''}{amount}%"
                    elif public_type == 'public_support':
                        current = game_state.player_resources.get('public_support', 0)
                        game_state.player_resources['public_support'] = max(0, min(10, current + amount))
                        description = f"Public support {'+' if amount > 0 else ''}{amount}"
                    elif public_type == 'political_influence':
                        current = game_state.player_resources.get('political_influence', 0)
                        game_state.player_resources['political_influence'] = max(0, min(10, current + amount))
                        description = f"Political influence {'+' if amount > 0 else ''}{amount}"
                    applied = True
            
            if applied and description:
                # Scale effects based on critical status
                if critical_success and 'critical_success_modifier' in consequence:
                    description += " (Critical Success!)"
                elif critical_failure and 'critical_failure_modifier' in consequence:
                    description += " (Critical Failure!)"
                
                consequences.append(description)
                
        return consequences
    
    def get_effects(self) -> List[Dict]:
        """Get the effects of this action."""
        return self.effects
        
    def add_consequence(self, consequence_type: str, **kwargs) -> None:
        """Add a consequence to this action."""
        consequence = {'type': consequence_type, **kwargs}
        self.consequences.append(consequence)
        
    def add_resource_cost(self, resource: str, amount: int) -> None:
        """Add a resource cost to this action."""
        self.resource_cost[resource] = amount
        
    def add_personnel_cost(self, personnel: str, amount: int) -> None:
        """Add a personnel cost to this action."""
        self.personnel_cost[personnel] = amount

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
        self.dialogue_options = self._initialize_actions()
        
        # Add faction-specific special abilities
        self._add_fbi_specials(self.dialogue_options)
        self._add_cia_specials(self.dialogue_options)
        self._add_local_pd_specials(self.dialogue_options)
        
        # Add criminal faction abilities
        self._add_shadow_syndicate_specials(self.dialogue_options)
        self._add_red_dragon_triad_specials(self.dialogue_options)
        self._add_liberation_front_specials(self.dialogue_options)
        
        # Initialize turn counters for gradual point scaling
        self.turn_thresholds = {
            'early_game': 5,   # Turns 1-5
            'mid_game': 12,    # Turns 6-12
            'late_game': 15    # Turns 13+
        }
        
    def get_available_actions(self, param):
        """Get available actions based on category or game state."""
        # Handle parameter that could be either an ActionCategory or a GameState
        if isinstance(param, ActionCategory):
            # Return actions for this category
            category = param
            if category in self.dialogue_options:
                # Filter out actions that are on cooldown
                return [action for action in self.dialogue_options[category] 
                        if not (hasattr(action, 'on_cooldown') and action.on_cooldown)]
            return []
        else:
            # Assume it's a GameState
            game_state = param
            
            # Check for cooldowns
            for category in self.dialogue_options:
                for action in self.dialogue_options[category]:
                    action.on_cooldown = game_state.is_action_on_cooldown(action.name)
                    # Update success chance based on current game state
                    action.update_success_chance(game_state)
            
            # Get actions for this game state based on faction
            faction = game_state.player_faction
            result = {}
            
            # Copy the actions for each category, filtering based on cooldown
            for category in self.dialogue_options:
                result[category] = [
                    action for action in self.dialogue_options[category]
                    if not action.on_cooldown
                ]
            
            return result

    def _initialize_actions(self) -> Dict[ActionCategory, List[GameAction]]:
        actions = {category: [] for category in ActionCategory}
        
        # Dialogue Actions (1 AP)
        dialogue_action1 = GameAction(
            name="Open Communication",
            description="Establish contact with hostage takers",
            category=ActionCategory.DIALOGUE,
            action_points=1,
            success_chance=0.85
        )
        dialogue_action1.add_consequence('resource', resource_type='intelligence', amount=1)
        dialogue_action1.add_consequence('public', public_type='media_control', amount=5)
        
        dialogue_action2 = GameAction(
            name="Empathize", 
            description="Show understanding to build rapport",
            category=ActionCategory.DIALOGUE,
            action_points=1,
            success_chance=0.80
        )
        dialogue_action2.add_consequence('resource', resource_type='negotiation_leverage', amount=1)
        
        dialogue_action3 = GameAction(
            name="Gather Information",
            description="Ask questions to learn more about their situation",
            category=ActionCategory.DIALOGUE,
            action_points=2,
            success_chance=0.75
        )
        dialogue_action3.add_consequence('resource', resource_type='intelligence', amount=2)
        dialogue_action3.add_consequence('ai_resource', resource_type='concealment', amount=-1)
        
        dialogue_action4 = GameAction(
            name="Assert Authority",
            description="Take control of the conversation",
            category=ActionCategory.DIALOGUE,
            action_points=2,
            success_chance=0.65
        )
        dialogue_action4.add_resource_cost('negotiation_leverage', 1)
        dialogue_action4.add_consequence('public', public_type='media_control', amount=10)
        dialogue_action4.add_consequence('ai_resource', resource_type='leverage', amount=-1)
        
        actions[ActionCategory.DIALOGUE].extend([
            dialogue_action1, dialogue_action2, dialogue_action3, dialogue_action4
        ])
        
        # Resources Actions (1-2 AP)
        resource_action1 = GameAction(
            name="Deploy Units",
            description="Position additional units around the perimeter",
            category=ActionCategory.RESOURCES,
            action_points=2,
            success_chance=0.90
        )
        resource_action1.add_resource_cost('manpower', 2)
        resource_action1.add_consequence('resource', resource_type='security_perimeter', amount=10)
        resource_action1.add_consequence('ai_resource', resource_type='exits_controlled', amount=-1, probability=0.3)
        
        resource_action2 = GameAction(
            name="Request Equipment",
            description="Call for specialized equipment",
            category=ActionCategory.RESOURCES,
            action_points=2,
            success_chance=0.85
        )
        resource_action2.add_consequence('resource', resource_type='tactical_gear', amount=2)
        resource_action2.add_consequence('resource', resource_type='communications_equipment', amount=1)
        
        resource_action3 = GameAction(
            name="Medical Standby",
            description="Position medical teams nearby",
            category=ActionCategory.RESOURCES,
            action_points=1,
            success_chance=0.95
        )
        resource_action3.add_resource_cost('medical', 1)
        resource_action3.add_consequence('resource', resource_type='medical', amount=2)
        
        resource_action4 = GameAction(
            name="Allocate Resources",
            description="Redistribute available resources for better efficiency",
            category=ActionCategory.RESOURCES,
            action_points=2,
            success_chance=0.80
        )
        resource_action4.add_resource_cost('money', 500000)
        resource_action4.add_consequence('resource', resource_type='equipment', amount=2)
        resource_action4.add_consequence('resource', resource_type='tactical_gear', amount=1)
        resource_action4.add_consequence('resource', resource_type='vehicles', amount=1)
        
        actions[ActionCategory.RESOURCES].extend([
            resource_action1, resource_action2, resource_action3, resource_action4
        ])
        
        # Force Actions (2-3 AP)
        force_action1 = GameAction(
            name="Position Snipers",
            description="Set up sniper positions for tactical advantage",
            category=ActionCategory.FORCE,
            action_points=3,
            success_chance=0.70
        )
        force_action1.add_personnel_cost('snipers', 2)
        force_action1.add_resource_cost('tactical_gear', 1)
        force_action1.add_consequence('tactical', position='sniper_positions', value=True)
        force_action1.add_consequence('ai_resource', resource_type='concealment', amount=-2)
        
        force_action2 = GameAction(
            name="Deploy Breach Team",
            description="Position breach team for potential entry",
            category=ActionCategory.FORCE,
            action_points=3,
            success_chance=0.75
        )
        force_action2.add_personnel_cost('tactical_units', 3)
        force_action2.add_resource_cost('tactical_gear', 2)
        force_action2.add_consequence('tactical', position='breach_points', value=True)
        force_action2.add_consequence('ai_resource', resource_type='exits_controlled', amount=-1)
        
        force_action3 = GameAction(
            name="Show of Force",
            description="Demonstrate tactical capabilities",
            category=ActionCategory.FORCE,
            action_points=2,
            success_chance=0.65
        )
        force_action3.add_resource_cost('tactical_gear', 1)
        force_action3.add_consequence('ai_resource', resource_type='leverage', amount=-1)
        force_action3.add_consequence('environmental', condition='power_status', value='partial', 
                                  on_critical_failure=True, probability=0.4)
        
        force_action4 = GameAction(
            name="Tactical Positioning",
            description="Optimize unit positions for maximum coverage",
            category=ActionCategory.FORCE,
            action_points=2,
            success_chance=0.80
        )
        force_action4.add_personnel_cost('tactical_units', 2)
        force_action4.add_consequence('resource', resource_type='security_perimeter', amount=15)
        force_action4.add_consequence('ai_resource', resource_type='concealment', amount=-1)
        
        actions[ActionCategory.FORCE].extend([
            force_action1, force_action2, force_action3, force_action4
        ])
        
        # Tech Actions (1-2 AP)
        tech_action1 = GameAction(
            name="Surveillance Deployment",
            description="Set up surveillance equipment",
            category=ActionCategory.TECH,
            action_points=2,
            success_chance=0.85
        )
        tech_action1.add_resource_cost('equipment', 1)
        tech_action1.add_resource_cost('communications_equipment', 1)
        tech_action1.add_consequence('resource', resource_type='surveillance_cameras', amount=3)
        tech_action1.add_consequence('tactical', position='surveillance', value=True)
        tech_action1.add_consequence('ai_resource', resource_type='concealment', amount=-2)
        
        tech_action2 = GameAction(
            name="Communications Intercept",
            description="Attempt to intercept their communications",
            category=ActionCategory.TECH,
            action_points=2,
            success_chance=0.70
        )
        tech_action2.add_resource_cost('communications_equipment', 2)
        tech_action2.add_consequence('resource', resource_type='intelligence', amount=3)
        tech_action2.add_consequence('ai_resource', resource_type='communications', amount=-1)
        
        tech_action3 = GameAction(
            name="Thermal Imaging",
            description="Use thermal cameras to gather intel",
            category=ActionCategory.TECH,
            action_points=1,
            success_chance=0.80
        )
        tech_action3.add_resource_cost('equipment', 1)
        tech_action3.add_consequence('resource', resource_type='intelligence', amount=2)
        tech_action3.add_consequence('ai_resource', resource_type='concealment', amount=-2)
        
        tech_action4 = GameAction(
            name="Network Analysis",
            description="Analyze digital communications patterns",
            category=ActionCategory.TECH,
            action_points=2,
            success_chance=0.75
        )
        tech_action4.add_personnel_cost('tech_specialists', 1)
        tech_action4.add_consequence('resource', resource_type='intelligence', amount=2)
        tech_action4.add_consequence('ai_resource', resource_type='information', amount=-1)
        
        actions[ActionCategory.TECH].extend([
            tech_action1, tech_action2, tech_action3, tech_action4
        ])
        
        # Negotiation Actions (1-2 AP)
        negotiation_action1 = GameAction(
            name="Make Offer",
            description="Present a negotiated offer",
            category=ActionCategory.NEGOTIATION,
            action_points=2,
            success_chance=0.70
        )
        negotiation_action1.add_resource_cost('negotiation_leverage', 1)
        negotiation_action1.add_resource_cost('money', 1000000)
        negotiation_action1.add_consequence('ai_resource', resource_type='money_demanded', amount=-2000000)
        negotiation_action1.add_consequence('hostage', effect='release', count=1, required_status='captured', probability=0.6)
        
        negotiation_action2 = GameAction(
            name="Request Good Faith",
            description="Ask for a show of good faith",
            category=ActionCategory.NEGOTIATION,
            action_points=2,
            success_chance=0.65
        )
        negotiation_action2.add_consequence('hostage', effect='release', count=1, required_status='captured', probability=0.5)
        
        negotiation_action3 = GameAction(
            name="Propose Timeline",
            description="Establish a timeline for resolution",
            category=ActionCategory.NEGOTIATION,
            action_points=1,
            success_chance=0.75
        )
        negotiation_action3.add_consequence('deadline', amount=2)  # Extend deadline by 2 turns
        
        negotiation_action4 = GameAction(
            name="Demand Concession",
            description="Firmly request specific concessions",
            category=ActionCategory.NEGOTIATION,
            action_points=2,
            success_chance=0.60
        )
        negotiation_action4.add_resource_cost('political_influence', 1)
        negotiation_action4.add_consequence('hostage', effect='release', count=1, required_status='captured', probability=0.4)
        negotiation_action4.add_consequence('ai_resource', resource_type='leverage', amount=-2)
        
        actions[ActionCategory.NEGOTIATION].extend([
            negotiation_action1, negotiation_action2, negotiation_action3, negotiation_action4
        ])
        
        # Threats Actions (1-3 AP)
        threats_action1 = GameAction(
            name="Verbal Warning",
            description="Issue a warning about consequences",
            category=ActionCategory.THREATS,
            action_points=1,
            success_chance=0.55
        )
        threats_action1.add_consequence('ai_resource', resource_type='leverage', amount=-1)
        
        threats_action2 = GameAction(
            name="Demonstrate Resolve",
            description="Show willingness to take action",
            category=ActionCategory.THREATS,
            action_points=2,
            success_chance=0.60
        )
        threats_action2.add_resource_cost('tactical_gear', 1)
        threats_action2.add_resource_cost('security_perimeter', 5)
        threats_action2.add_consequence('ai_resource', resource_type='leverage', amount=-2)
        
        threats_action3 = GameAction(
            name="Ultimatum",
            description="Present final terms",
            category=ActionCategory.THREATS,
            action_points=3,
            success_chance=0.50
        )
        threats_action3.add_resource_cost('political_influence', 1)
        threats_action3.add_resource_cost('negotiation_leverage', 2)
        threats_action3.add_consequence('hostage', effect='release', count=2, required_status='captured', probability=0.4)
        threats_action3.add_consequence('environmental', condition='power_status', value='off',
                                     on_critical_failure=True, probability=0.6)
        
        threats_action4 = GameAction(
            name="Pressure Tactics",
            description="Apply psychological pressure to force compliance",
            category=ActionCategory.THREATS,
            action_points=2,
            success_chance=0.65
        )
        threats_action4.add_resource_cost('intelligence', 1)
        threats_action4.add_consequence('ai_resource', resource_type='leverage', amount=-1)
        threats_action4.add_consequence('hostage', effect='release', count=1, required_status='captured', probability=0.3)
        
        actions[ActionCategory.THREATS].extend([
            threats_action1, threats_action2, threats_action3, threats_action4
        ])
        
        return actions
    
    def perform_action(self, game_state, action):
        """Perform an action and apply its effects."""
        # Check if we have enough action points
        if game_state.action_points < action.action_points:
            return {
                'success': False,
                'message': f"Not enough action points. Need {action.action_points}, have {game_state.action_points}."
            }
        
        # Check if action is on cooldown
        if game_state.is_action_on_cooldown(action.name):
            return {
                'success': False,
                'message': f"Action {action.name} is on cooldown."
            }
        
        # Perform the action
        result = action.perform(game_state)
        
        # Deduct action points
        game_state.action_points -= action.action_points
        
        # Get game stage for scaling effects
        game_stage = self._get_game_stage(game_state.turn)
        
        # Apply scaled effects based on success/failure and game stage
        if result['success']:
            effect_multiplier = 1.0
            
            # Apply scaling based on game stage
            if game_stage == 'early_game':
                effect_multiplier = 0.5  # 50% effect in early game
            elif game_stage == 'mid_game':
                effect_multiplier = 1.0  # 100% effect in mid game
            elif game_stage == 'late_game':
                effect_multiplier = 1.5  # 150% effect in late game
                
            # Apply critical success/failure scaling
            if result['critical_success']:
                effect_multiplier *= 1.5  # 50% more effect on critical success
            elif result['partial_success']:
                effect_multiplier *= 0.5  # 50% less effect on partial success
                
            # Apply effects based on action category
            category = action.category.value
            if category == "DIALOGUE":
                game_state.modify_trust(0.1 * effect_multiplier)
                game_state.modify_tension(-0.05 * effect_multiplier)
            elif category == "FORCE":
                game_state.modify_trust(-0.1 * effect_multiplier)
                game_state.modify_tension(0.15 * effect_multiplier)
            elif category == "TECH":
                game_state.modify_morale(0.15 * effect_multiplier)
                game_state.modify_tension(-0.1 * effect_multiplier)
            elif category == "NEGOTIATION":
                game_state.modify_trust(0.15 * effect_multiplier)
                game_state.modify_tension(-0.1 * effect_multiplier)
            elif category == "RESOURCES":
                game_state.modify_morale(0.1 * effect_multiplier)
            elif category == "THREATS":
                game_state.modify_trust(-0.1 * effect_multiplier)
                game_state.modify_tension(0.2 * effect_multiplier)
                
            # Apply the action's effects
            for effect in action.effects:
                effect_result = self._apply_effect(effect, game_state, effect_multiplier)
                if 'message' in effect_result:
                    result.setdefault('messages', []).append(effect_result['message'])
        else:
            # On failure, increase tension (more on critical failure)
            if result['critical_failure']:
                game_state.modify_tension(0.22)  # +50% tension on critical failure
                result['message'] = f"Critical failure on {action.name}!"
            else:
                game_state.modify_tension(0.15)
                result['message'] = f"Failed to perform {action.name}."
        
        return result
        
    def _get_game_stage(self, turn: int) -> str:
        """Determine the current game stage based on turn number."""
        if turn <= self.turn_thresholds['early_game']:
            return 'early_game'
        elif turn <= self.turn_thresholds['mid_game']:
            return 'mid_game'
        else:
            return 'late_game'
        
    def _apply_effect(self, effect: ActionEffect, game_state: GameState, multiplier: float = 1.0) -> Dict:
        """Apply an effect to the game state with optional multiplier."""
        result = {}
        
        if effect == ActionEffect.TRUST_INCREASE:
            game_state.modify_trust(0.1 * multiplier)
            result['message'] = f"Trust increased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.TRUST_DECREASE:
            game_state.modify_trust(-0.1 * multiplier)
            result['message'] = f"Trust decreased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.TENSION_INCREASE:
            game_state.modify_tension(0.1 * multiplier)
            result['message'] = f"Tension increased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.TENSION_DECREASE:
            game_state.modify_tension(-0.1 * multiplier)
            result['message'] = f"Tension decreased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.MORALE_INCREASE:
            game_state.modify_morale(0.1 * multiplier)
            result['message'] = f"Morale increased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.MORALE_DECREASE:
            game_state.modify_morale(-0.1 * multiplier)
            result['message'] = f"Morale decreased by {0.1 * multiplier:.2f}"
        elif effect == ActionEffect.HOSTAGE_RELEASE:
            # Try to release 1 hostage with scaling based on multiplier
            release_count = max(1, int(1 * multiplier))
            available_hostages = [h for h in game_state.hostages_status 
                                if h['status'] == 'captured']
            
            for _ in range(min(release_count, len(available_hostages))):
                if available_hostages:
                    hostage = random.choice(available_hostages)
                    game_state.update_hostage_status(hostage['id'], {'status': 'released'})
                    result['message'] = f"Hostage {hostage['name']} released"
                    available_hostages.remove(hostage)
        elif effect == ActionEffect.RESOURCE_GAIN:
            resource_type = 'intelligence'  # Default resource
            amount = int(1 * multiplier)
            game_state.modify_player_resource(resource_type, amount)
            result['message'] = f"Gained {amount} {resource_type}"
        elif effect == ActionEffect.TACTICAL_ADVANTAGE:
            # Enable a random tactical position that's not already active
            inactive_positions = [pos for pos, active in game_state.tactical_positions.items() 
                                if not active]
            if inactive_positions:
                position = random.choice(inactive_positions)
                game_state.set_tactical_position(position, True)
                result['message'] = f"Gained tactical advantage: {position}"
        elif effect == ActionEffect.EXTRA_ACTION_POINTS:
            extra_ap = max(1, int(1 * multiplier))
            game_state.next_turn_extra_ap += extra_ap
            result['message'] = f"Gained {extra_ap} extra action points for next turn"
        
        return result

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