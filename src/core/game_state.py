from typing import List, Dict, Optional
from enum import Enum, auto
import random

class Faction(Enum):
    FBI = "Federal Bureau of Investigation"
    CIA = "Central Intelligence Agency"
    LOCAL_PD = "Local Police Department"
    
    # Add enemy factions for AI opponents
    SHADOW_SYNDICATE = "Shadow Syndicate"
    RED_DRAGON_TRIAD = "Red Dragon Triad"
    LIBERATION_FRONT = "Liberation Front"

class GameState:
    def __init__(self, player_faction: Faction):
        self.player_faction = player_faction
        # Assign AI opponent based on player choice
        self.ai_faction = self._assign_ai_opponent(player_faction)
        
        self.turn = 1
        self.max_turns = 20  # Maximum number of turns before game over
        self.action_points = 3
        self.used_special_abilities = []
        self.next_turn_extra_ap = 0
        
        # Core metrics
        self.trust_level = 0.5
        self.tension_level = 0.3
        self.morale_level = 0.75  # Renamed from intel_level
        
        # Game history log for tracking events
        self.game_history = []
        # Add initial history entry
        self.add_history_entry(f"Situation begins. {player_faction.value} responds.")
        
        # Action cooldowns tracking
        self.action_cooldowns = {}
        
        # Enhanced resources for player
        self.player_resources = {
            'manpower': 10,
            'equipment': 5,
            'intelligence': 3,
            'medical': 4,
            'negotiation_leverage': 2,
            'public_support': 7,
            'surveillance_cameras': 6,
            'communications_equipment': 8,
            'tactical_gear': 5,
            'water_supplies': 10,
            'electrical_equipment': 4,
            'political_influence': 3,
            'money': 5000000,  # Budget in dollars
            'vehicles': 6,
            'security_perimeter': 80,  # Percentage secured
            'media_control': 60       # Percentage of media managed
        }
        
        # AI resources and personnel
        self.ai_resources = {
            'manpower': 8,
            'equipment': 4,
            'concealment': 7,
            'leverage': 5,
            'money_demanded': 1000000
        }
        
        self.ai_personnel = {
            'armed_members': 6,
            'negotiators': 2,
            'lookouts': 4,
            'technical_experts': 2
        }
        
        # Player personnel
        self.player_personnel = {
            'negotiators': 4,
            'tactical_team': 8,
            'medical_staff': 3,
            'tech_specialists': 3,
            'intelligence_officers': 4
        }
        
        # Hostage tracking
        self.total_hostages = 10
        self.hostages_released = 0
        self.hostages_killed = 0
        self.hostage_deadline = 10  # Turns until first hostage execution
        
        self.hostages_status = [
            {
                'id': i,
                'name': f"Hostage {i+1}",
                'status': 'captured',  # captured, released, killed
                'health': 100,
                'stress': 50
            }
            for i in range(self.total_hostages)
        ]
        
        # Tactical advantages
        self.tactical_positions = {
            'perimeter': True,
            'negotiation_point': True,
            'command_post': True,
            'sniper_positions': False,
            'breach_points': False,
            'surveillance': False,
        }
        
        # Environmental conditions
        self.environment = {
            'power_status': 'on',  # 'on', 'partial', 'off'
            'water_status': 'on',  # 'on', 'off'
            'fire_status': 'none', # 'none', 'minor', 'major'
            'structural_damage': 'none', # 'none', 'minor', 'major', 'critical'
            'gas_leak': False,
            'flooding': False
        }
        
        # Public reaction
        self.public_reaction = {
            'media_coverage': 0.3,   # 0.0 to 1.0
            'public_panic': 0.1,     # 0.0 to 1.0
            'political_pressure': 0.2 # 0.0 to 1.0
        }
        
        # Demands tracking
        self.demands = {
            'money': 1000000,
            'transport': False,
            'prisoner_release': False,
            'media_statement': False,
            'immunity': False
        }
        self.demands_met = {
            'money': 0,
            'transport': False,
            'prisoner_release': False,
            'media_statement': False,
            'immunity': False
        }
        
        # Action synergies
        self.last_action_category = None
        self.last_action_success = None
        
        # Game state tracking
        self.game_over = False
        self.victory = False
        self.defeat_reason = None
        
        # History
        self.dialogue_history: List[Dict] = []
        
        # Special conditions
        self.communications_disabled = False
        self.power_cut = False
        self.media_presence = True
        
        # Hostage taker state
        self.hostage_taker_morale = 0.7
        self.hostage_taker_aggression = 0.3
        self.demands_urgency = 0.4
        
        # AI turn tracking
        self.ai_opponent = None  # Will be initialized in init_ai_opponent
        self.ai_turn_active = False
        self.ai_last_turn_actions = []
        self.ai_action_history = []
        
        # Objectives
        self._objectives = [
            {
                'text': "Establish communication with hostage takers",
                'priority': 1,
                'complete': False,
                'failed': False
            },
            {
                'text': "Gather intelligence on the situation",
                'priority': 2,
                'complete': False,
                'failed': False
            },
            {
                'text': "Maintain public safety",
                'priority': 2,
                'complete': False,
                'failed': False
            }
        ]
        
        # AI objectives
        self.ai_objectives = [
            {
                'text': "Secure ransom payment",
                'priority': 1,
                'complete': False,
                'failed': False
            },
            {
                'text': "Ensure safe escape",
                'priority': 2,
                'complete': False,
                'failed': False
            },
            {
                'text': "Maintain control of hostages",
                'priority': 1,
                'complete': False,
                'failed': False
            }
        ]
    
    def _assign_ai_opponent(self, player_faction: Faction) -> Faction:
        """Assign an appropriate AI opponent based on player faction"""
        if player_faction == Faction.FBI:
            return Faction.LIBERATION_FRONT
        elif player_faction == Faction.CIA:
            return Faction.SHADOW_SYNDICATE
        else:  # LOCAL_PD
            return Faction.RED_DRAGON_TRIAD
    
    def init_ai_opponent(self):
        """Initialize the AI opponent - should be called after importing the ai_opponent module."""
        # This is called separately to avoid circular imports
        from .ai_opponent import AIOpponent
        self.ai_opponent = AIOpponent(self.ai_faction)
    
    def track_player_action(self, action_category: str):
        """Track player action for AI adaptation."""
        if self.ai_opponent:
            self.ai_opponent.track_player_action(action_category)
    
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
            
        # Major victory - AI resources depleted
        if self.ai_resources['manpower'] <= 0 and self.ai_personnel['armed_members'] <= 0:
            self.game_over = True
            self.victory = True
            return True
        
        # Defeat conditions
        if self.hostages_killed > 3:  # Changed from any hostage to more than 3
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Too many hostages killed"
            return True
            
        if self.tension_level >= 1.0:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Situation escalated out of control"
            return True
            
        if self.turn > self.max_turns:  # Changed from >= to > to allow the final turn to complete
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Time ran out"
            return True
            
        if self.hostage_deadline <= 0 and self.demands_met['money'] < self.demands['money']:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Failed to meet demands before deadline"
            return True
            
        # Major defeat - player critical resources depleted
        if self.player_resources['manpower'] <= 0 or self.player_personnel['negotiators'] <= 0:
            self.game_over = True
            self.victory = False
            self.defeat_reason = "Critical personnel lost"
            return True
        
        return False
    
    def get_dynamic_success_chance(self, action_category: str, base_chance: float) -> float:
        """Calculate dynamic success chance based on game state."""
        modified_chance = base_chance
        
        # Trust/Tension Impact
        if action_category in ["NEGOTIATE", "TACTICAL"] and self.trust_level > 0.7:
            modified_chance += 0.05  # +5% for high trust
        
        if action_category in ["FORCE", "SPECIAL"] and self.tension_level > 0.7:
            modified_chance -= 0.05  # -5% for high tension
        
        # Morale Impact
        if self.morale_level < 0.3 and action_category == "SPECIAL":
            modified_chance -= 0.1  # -10% for low morale
        elif self.morale_level > 0.7:
            modified_chance += 0.05  # +5% for high morale
        
        # Action synergies
        if self.last_action_category == "NEGOTIATE" and self.last_action_success and action_category == "NEGOTIATE":
            modified_chance += 0.1  # +10% for successful negotiation chain
        
        if self.last_action_category == "FORCE" and not self.last_action_success and action_category == "NEGOTIATE":
            modified_chance -= 0.1  # -10% for negotiating after failed force action
        
        # Environmental factors
        if self.environment['power_status'] != 'on' and action_category == "TECH":
            modified_chance -= 0.15  # -15% for tech actions during power outage
        
        if self.environment['fire_status'] != 'none' and action_category == "FORCE":
            modified_chance -= 0.1  # -10% for force actions during fire
        
        # Ensure chance stays within reasonable bounds
        return max(0.1, min(0.95, modified_chance))
    
    def get_objectives(self) -> List[Dict]:
        """Get the current objectives."""
        return self._objectives
    
    def get_ai_objectives(self) -> List[Dict]:
        """Get the AI's objectives."""
        return self.ai_objectives
    
    def add_dialogue(self, speaker: str, text: str, success: bool = True):
        """Add a dialogue entry to the history."""
        self.dialogue_history.append({
            'speaker': speaker,
            'text': text,
            'success': success
        })
    
    def add_history_entry(self, message, actor=None, action=None, success=None):
        """Add an entry to the game history log.
        
        Args:
            message: The text message describing the event
            actor: Who performed the action ('Player', 'AI', or 'System')
            action: Optional action name if this was an action
            success: Optional success flag if this was an action
        """
        entry = {
            'turn': self.turn,
            'message': message
        }
        
        if actor:
            entry['actor'] = actor
        if action:
            entry['action'] = action
        if success is not None:
            entry['success'] = success
            
        self.game_history.append(entry)
        
        # Keep history at a reasonable size
        if len(self.game_history) > 100:
            # Remove oldest entries
            self.game_history = self.game_history[-100:]
    
    def modify_trust(self, amount: float):
        """Modify trust level, keeping it between 0 and 1."""
        self.trust_level = max(0.0, min(1.0, self.trust_level + amount))
    
    def modify_tension(self, amount: float):
        """Modify tension level, keeping it between 0 and 1."""
        self.tension_level = max(0.0, min(1.0, self.tension_level + amount))
    
    def modify_morale(self, amount: float):
        """Modify morale level, keeping it between 0 and 1."""
        self.morale_level = max(0.0, min(1.0, self.morale_level + amount))
    
    def modify_player_resource(self, resource: str, amount: int):
        """Modify a player resource by the given amount."""
        if resource in self.player_resources:
            self.player_resources[resource] = max(0, self.player_resources[resource] + amount)
    
    def modify_ai_resource(self, resource: str, amount: int):
        """Modify an AI resource by the given amount."""
        if resource in self.ai_resources:
            self.ai_resources[resource] = max(0, self.ai_resources[resource] + amount)
    
    def modify_player_personnel(self, personnel_type: str, amount: int):
        """Modify player personnel count."""
        if personnel_type in self.player_personnel:
            self.player_personnel[personnel_type] = max(0, self.player_personnel[personnel_type] + amount)
    
    def modify_ai_personnel(self, personnel_type: str, amount: int):
        """Modify AI personnel count."""
        if personnel_type in self.ai_personnel:
            self.ai_personnel[personnel_type] = max(0, self.ai_personnel[personnel_type] + amount)
    
    def update_hostage_status(self, hostage_id: int, status_update: Dict):
        """Update a hostage's status with the given updates."""
        for hostage in self.hostages_status:
            if hostage['id'] == hostage_id:
                for key, value in status_update.items():
                    if key in hostage:
                        hostage[key] = value
                if 'status' in status_update:
                    if status_update['status'] == 'killed':
                        self.hostages_killed += 1
                    elif status_update['status'] == 'wounded':
                        self.hostages_wounded += 1
                    elif status_update['status'] == 'released':
                        self.hostages_released += 1
                break
    
    def update_environment(self, condition: str, value):
        """Update an environmental condition."""
        if condition in self.environment:
            self.environment[condition] = value
            
            # Update related resources based on environmental changes
            if condition == 'power_status':
                if value == 'off' and self.environment[condition] != 'off':
                    self.player_resources['surveillance_cameras'] = max(0, self.player_resources['surveillance_cameras'] - 4)
                    self.player_resources['communications_equipment'] = max(0, self.player_resources['communications_equipment'] - 2)
                    self.ai_resources['electrical_access'] = 0
                elif value == 'on' and self.environment[condition] != 'on':
                    self.player_resources['surveillance_cameras'] = min(10, self.player_resources['surveillance_cameras'] + 4)
                    self.player_resources['communications_equipment'] = min(10, self.player_resources['communications_equipment'] + 2)
                    self.ai_resources['electrical_access'] = 1
            elif condition == 'water_status':
                if value == 'off' and self.environment[condition] != 'off':
                    self.ai_resources['water_access'] = 0
                    # Reduce hostage health due to no water
                    for hostage in self.hostages_status:
                        if hostage['status'] == 'captured':
                            hostage['health'] = max(10, hostage['health'] - 10)
                elif value == 'on' and self.environment[condition] != 'on':
                    self.ai_resources['water_access'] = 1
            elif condition == 'fire_status':
                if value != 'none' and self.environment[condition] == 'none':
                    # Fire reduces concealment and may damage exits
                    self.ai_resources['concealment'] = max(0, self.ai_resources['concealment'] - 3)
                    if random.random() < 0.5:  # 50% chance to lose an exit
                        self.ai_resources['exits_controlled'] = max(0, self.ai_resources['exits_controlled'] - 1)
                        
                    # Fire increases stress for hostages
                    for hostage in self.hostages_status:
                        if hostage['status'] == 'captured':
                            hostage['stress'] = min(100, hostage['stress'] + 20)
    
    def set_tactical_position(self, position: str, active: bool):
        """Set the status of a tactical position."""
        if position in self.tactical_positions:
            self.tactical_positions[position] = active
    
    def complete_objective(self, index: int, is_ai: bool = False):
        """Mark an objective as complete."""
        target_objectives = self.ai_objectives if is_ai else self._objectives
        if 0 <= index < len(target_objectives):
            target_objectives[index]['complete'] = True
    
    def fail_objective(self, index: int, is_ai: bool = False):
        """Mark an objective as failed."""
        target_objectives = self.ai_objectives if is_ai else self._objectives
        if 0 <= index < len(target_objectives):
            target_objectives[index]['failed'] = True
    
    def add_action_cooldown(self, action_name: str, duration: int = 3):
        """Add a cooldown for a specific action."""
        self.action_cooldowns[action_name] = duration
    
    def update_cooldowns(self):
        """Update all action cooldowns at the end of turn."""
        cooldowns_to_remove = []
        for action, cooldown in self.action_cooldowns.items():
            self.action_cooldowns[action] = cooldown - 1
            if self.action_cooldowns[action] <= 0:
                cooldowns_to_remove.append(action)
        
        for action in cooldowns_to_remove:
            del self.action_cooldowns[action]
    
    def is_action_on_cooldown(self, action_name: str) -> bool:
        """Check if an action is currently on cooldown."""
        return action_name in self.action_cooldowns and self.action_cooldowns[action_name] > 0
    
    def process_ai_turn(self) -> List[Dict]:
        """Process the AI's turn."""
        if not self.ai_opponent:
            print("Initializing AI opponent...")  # Debug print
            self.init_ai_opponent()
            
        # Start AI turn
        self.ai_turn_active = True
        print(f"AI Turn Active: {self.ai_faction.value}")  # Debug print
        
        # Reset AI action points
        self.ai_opponent.action_points = 3
        print(f"Reset AI action points to {self.ai_opponent.action_points}")  # Debug print
        
        # AI takes actions
        ai_actions = self.ai_opponent.take_turn(self)
        print(f"AI Actions taken: {len(ai_actions)}")  # Debug print
        
        # Record AI actions
        self.ai_last_turn_actions = ai_actions
        self.ai_action_history.extend(ai_actions)
        
        # Add to game history
        for action in ai_actions:
            self.add_history_entry(
                message=f"{self.ai_faction.value} performed {action['action_name']}: {action['description']}",
                actor='AI',
                action=action['action_name'],
                success=action['success']
            )
            
            # Add dialogue for some actions
            if action['category'] in ["NEGOTIATION", "PSYCHOLOGICAL", "DEMANDS"]:
                speaker = self.ai_faction.value
                self.add_dialogue(
                    speaker=speaker,
                    text=action['description'],
                    success=action['success']
                )
        
        # End AI turn
        self.ai_turn_active = False
        print("AI turn ended")  # Debug print
        
        # Check for game over
        self.check_game_over()
        
        return ai_actions
    
    def end_turn(self):
        """End the current turn."""
        print("Starting end_turn in GameState")  # Debug print
        
        # Process AI turn first
        if not self.game_over:
            # Reset AI action points before their turn
            if self.ai_opponent:
                self.ai_opponent.action_points = 3  # Reset AI action points
                print("AI action points reset")  # Debug print
                
            # Process AI turn and store results
            self.ai_last_turn_actions = self.process_ai_turn()
            print(f"AI turn processed, got {len(self.ai_last_turn_actions)} actions")  # Debug print
            
        # Then advance to next turn
        self.turn += 1
        self.action_points = 3  # Reset player action points
        print(f"Advanced to turn {self.turn}, reset player AP to {self.action_points}")  # Debug print
        
        # Apply extra AP from special abilities
        if self.next_turn_extra_ap > 0:
            self.action_points += self.next_turn_extra_ap
            self.next_turn_extra_ap = 0
            print(f"Applied extra AP, new total: {self.action_points}")  # Debug print
        
        # Update cooldowns
        self.update_cooldowns()
        
        # Update hostage deadline
        self.hostage_deadline -= 1
        
        # Natural hostage deterioration per turn
        for hostage in self.hostages_status:
            if hostage['status'] == 'captured':
                # Stress increases naturally over time
                hostage['stress'] = min(100, hostage['stress'] + 5)
                
                # Very high stress can affect health
                if hostage['stress'] > 90 and random.random() < 0.2:  # 20% chance
                    hostage['health'] = max(10, hostage['health'] - 5)
        
        # Check for game over
        self.check_game_over()
        print("End turn completed in GameState")  # Debug print
    
    def update_state_after_action(self, action_name: str, category: str, success: bool):
        """Update game state after an action is performed."""
        # Track player action for AI adaptation
        self.track_player_action(category)
        
        # Store last action for synergy effects
        self.last_action_category = category
        self.last_action_success = success
        
        # Apply success/failure effects based on category
        if success:
            if category == "DIALOGUE":
                self.modify_trust(0.1)
                self.modify_tension(-0.05)
            elif category == "FORCE":
                self.modify_trust(-0.1)
                self.modify_tension(0.15)
            elif category == "TECH":
                self.modify_morale(0.15)
                self.modify_tension(-0.1)
            elif category == "NEGOTIATION":
                self.modify_trust(0.15)
                self.modify_tension(-0.1)
            elif category == "RESOURCES":
                self.modify_morale(0.1)
            elif category == "THREATS":
                self.modify_trust(-0.1)
                self.modify_tension(0.2)
        else:
            # On failure, always increase tension
            self.modify_tension(0.15)
        
        # Update tactical positions
        if action_name == "Position Snipers" and success:
            self.tactical_positions['sniper_positions'] = True
        elif action_name == "Surveillance Deployment" and success:
            self.tactical_positions['surveillance'] = True
        elif action_name == "Deploy Breach Team" and success:
            self.tactical_positions['breach_points'] = True
        
        # Update hostage situation based on trust/tension
        if self.tension_level >= 0.8 and random.random() < 0.3:
            # Find a non-wounded, non-killed hostage
            available_hostages = [h for h in self.hostages_status 
                                if h['status'] == 'captured' and h['health'] == 100]
            if available_hostages:
                hostage = random.choice(available_hostages)
                self.update_hostage_status(hostage['id'], {'health': 50, 'status': 'wounded'})
            
        # Update deadline
        if category == "NEGOTIATION" and success:
            self.hostage_deadline += 1  # Buying time through negotiation
        
        # Update hostage taker state
        if success:
            if category == "FORCE":
                self.hostage_taker_morale -= 0.1
                self.hostage_taker_aggression += 0.2
                
                # Potential loss of AI personnel
                if random.random() < 0.3:  # 30% chance
                    self.modify_ai_personnel("armed_members", -1)
                    
            elif category == "NEGOTIATION":
                if self.trust_level > 0.6:
                    self.hostage_taker_morale -= 0.05
                    self.demands_urgency -= 0.1
                    
                    # Potential hostage release
                    if random.random() < 0.2:  # 20% chance
                        available_hostages = [h for h in self.hostages_status 
                                            if h['status'] == 'captured']
                        if available_hostages:
                            hostage = random.choice(available_hostages)
                            self.update_hostage_status(hostage['id'], {'status': 'released'})
        else:
            # Failed actions may impact player resources
            if category == "FORCE" and random.random() < 0.4:  # 40% chance
                self.modify_player_personnel("tactical_team", -1)
        
        # Check for game over
        self.check_game_over() 