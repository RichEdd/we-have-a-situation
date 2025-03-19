from typing import List, Dict, Optional
from enum import Enum, auto
import random

class Faction(Enum):
    FBI = "Federal Bureau of Investigation"
    CIA = "Central Intelligence Agency"
    LOCAL_PD = "Local Police Department"

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
        self.intel_level = 0.0
        
        # Resources
        self.resources = {
            'manpower': 10,
            'equipment': 5,
            'intel': 0,
        }
        
        # Hostage situation
        self.total_hostages = 8
        self.hostages_released = 0
        self.hostages_wounded = 0
        self.hostages_killed = 0
        
        # Tactical advantages
        self.tactical_positions = {
            'perimeter': True,
            'negotiation_point': True,
            'command_post': True,
            'sniper_positions': False,
            'breach_points': False,
            'surveillance': False,
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
        self.dialogue_history: List[Dict] = []
        self.game_history: List[Dict] = []
        
        # Special conditions
        self.communications_disabled = False
        self.power_cut = False
        self.media_presence = True
        
        # Hostage taker state
        self.hostage_taker_morale = 0.7
        self.hostage_taker_aggression = 0.3
        self.demands_urgency = 0.4
        
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
    
    def get_objectives(self) -> List[Dict]:
        """Get the current objectives."""
        return self._objectives
    
    def add_dialogue(self, speaker: str, text: str, success: bool = True):
        """Add a dialogue entry to the history."""
        self.dialogue_history.append({
            'speaker': speaker,
            'text': text,
            'success': success
        })
    
    def add_history_entry(self, entry: Dict):
        """Add an entry to the game history."""
        self.game_history.append(entry)
    
    def modify_trust(self, amount: float):
        """Modify the trust level."""
        self.trust_level = max(0.0, min(1.0, self.trust_level + amount))
    
    def modify_tension(self, amount: float):
        """Modify the tension level."""
        self.tension_level = max(0.0, min(1.0, self.tension_level + amount))
    
    def modify_intel(self, amount: float):
        """Modify the intel level."""
        self.intel_level = max(0.0, min(1.0, self.intel_level + amount))
    
    def modify_resource(self, resource: str, amount: int):
        """Modify a resource amount."""
        if resource in self.resources:
            self.resources[resource] = max(0, self.resources[resource] + amount)
    
    def set_tactical_position(self, position: str, active: bool):
        """Set the status of a tactical position."""
        if position in self.tactical_positions:
            self.tactical_positions[position] = active
    
    def complete_objective(self, index: int):
        """Mark an objective as complete."""
        if 0 <= index < len(self._objectives):
            self._objectives[index]['complete'] = True
    
    def fail_objective(self, index: int):
        """Mark an objective as failed."""
        if 0 <= index < len(self._objectives):
            self._objectives[index]['failed'] = True
    
    def end_turn(self):
        """End the current turn."""
        self.turn += 1
        self.action_points = 3  # Reset action points
    
    def update_state_after_action(self, action_name: str, category: str, success: bool):
        """Update game state after an action is performed."""
        # Update tactical positions
        if action_name == "Position Snipers" and success:
            self.tactical_positions['sniper_positions'] = True
        elif action_name == "Surveillance Deployment" and success:
            self.tactical_positions['surveillance'] = True
        elif action_name == "Deploy Breach Team" and success:
            self.tactical_positions['breach_points'] = True
        
        # Update hostage situation based on trust/tension
        if self.tension_level >= 0.8 and random.random() < 0.3:
            self.hostages_wounded += 1
            
        # Update deadline
        if category == "NEGOTIATION" and success:
            self.hostage_deadline += 1  # Buying time through negotiation
        
        # Update hostage taker state
        if success:
            if category == "FORCE":
                self.hostage_taker_morale -= 0.1
                self.hostage_taker_aggression += 0.2
            elif category == "NEGOTIATION":
                if self.trust_level > 0.6:
                    self.hostage_taker_morale -= 0.05
                    self.demands_urgency -= 0.1
        
        # Check for game over
        self.check_game_over() 