import random
from typing import List, Dict, Optional, Tuple
from enum import Enum
from .dialogue_system import ActionCategory, Faction
from .game_state import GameState

class AIBehaviorType(Enum):
    AGGRESSIVE = "Aggressive"
    DEFENSIVE = "Defensive" 
    ERRATIC = "Erratic"
    CALCULATING = "Calculating"
    DESPERATE = "Desperate"

class AIAction:
    """Represents an action the AI can take."""
    def __init__(self, name: str, category: str, description: str, 
                 base_success_chance: float = 0.7, action_points: int = 1):
        self.name = name
        self.category = category
        self.description = description
        self.base_success_chance = base_success_chance
        self.success_chance = base_success_chance
        self.action_points = action_points
        self.effects = []
        self.consequences = []
        
    def is_valid(self, game_state: GameState) -> bool:
        """Check if this action is valid in the current game state."""
        # Base validity checks
        if self.action_points > game_state.ai_opponent.action_points:
            print(f"Not enough AP for {self.name}")  # Debug print
            return False
            
        # Category-specific checks
        if self.category == "FORCE":
            # Can't use force actions if no armed members
            if game_state.ai_resources['manpower'] <= 0 or game_state.ai_personnel['armed_members'] <= 0:
                print(f"No manpower/armed members for {self.name}")  # Debug print
                return False
                
            # Special case for Execute Hostage
            if self.name == "Execute Hostage":
                # Need at least one captive hostage
                has_captive = any(h['status'] == 'captured' for h in game_state.hostages_status)
                if not has_captive:
                    print("No captive hostages for Execute Hostage")  # Debug print
                    return False
                    
        elif self.category == "NEGOTIATION":
            # Can't negotiate if trust is too low
            if game_state.trust_level < 0.1:
                print(f"Trust too low for {self.name}")  # Debug print
                return False
                
        elif self.category == "TACTICAL":
            # Can't do tactical actions if no manpower
            if game_state.ai_resources['manpower'] <= 0:
                print(f"No manpower for {self.name}")  # Debug print
                return False
                
        # Action is valid if it passed all checks
        print(f"Action {self.name} is valid")  # Debug print
        return True
    
    def perform(self, game_state: GameState) -> Dict:
        """Perform the action and return result details."""
        # Calculate success chance
        roll = random.random()
        success = roll < self.success_chance
        
        # Determine if this is a critical success/failure
        critical_threshold = 0.05
        critical_success = success and roll < (self.success_chance * critical_threshold)
        critical_failure = not success and roll > (1 - critical_threshold)
        
        # Apply effects based on success/failure
        result = self._apply_effects(game_state, success, critical_success, critical_failure)
        
        # Return detailed results
        return {
            'action_name': self.name,
            'category': self.category,
            'success': success,
            'critical_success': critical_success,
            'critical_failure': critical_failure,
            'roll': roll,
            'target': self.success_chance,
            'effects': result
        }
    
    def _apply_effects(self, game_state: GameState, success: bool, 
                      critical_success: bool, critical_failure: bool) -> List[str]:
        """Apply the effects of this action based on success/failure."""
        results = []
        
        effect_multiplier = 1.0
        if critical_success:
            effect_multiplier = 1.5
        elif critical_failure:
            effect_multiplier = 0.5
            
        # Apply standard effects based on category
        if success:
            if self.category == "NEGOTIATION":
                # Negotiation successes improve AI's position
                game_state.hostage_taker_morale += 0.1 * effect_multiplier
                game_state.modify_trust(-0.1 * effect_multiplier)
                results.append(f"AI built leverage through negotiation")
                
                # Potential money demands
                if random.random() < 0.3:
                    increase = int(1000000 * effect_multiplier)
                    game_state.ai_resources['money_demanded'] += increase
                    results.append(f"AI increased ransom demand by ${increase}")
                
            elif self.category == "FORCE":
                # Force actions increase tension and may hurt hostages
                game_state.modify_tension(0.15 * effect_multiplier)
                game_state.hostage_taker_aggression += 0.1 * effect_multiplier
                results.append(f"AI shows force, increasing tension")
                
                # Potential hostage wounding
                if random.random() < 0.4:
                    # Select a random hostage to wound
                    available_hostages = [h for h in game_state.hostages_status 
                                        if h['status'] == 'captured' and h['health'] > 50]
                    if available_hostages:
                        hostage = random.choice(available_hostages)
                        game_state.update_hostage_status(hostage['id'], 
                                                      {'health': max(10, hostage['health'] - 40)})
                        results.append(f"AI wounded hostage {hostage['name']}")
                
            elif self.category == "DEMANDS":
                # Increase demands and pressure
                game_state.demands_urgency += 0.2 * effect_multiplier
                results.append(f"AI increases demand urgency")
                
                # Potential deadline reduction
                if random.random() < 0.5:
                    reduction = max(1, int(2 * effect_multiplier))
                    game_state.hostage_deadline = max(1, game_state.hostage_deadline - reduction)
                    results.append(f"AI reduced deadline by {reduction} turns")
                
            elif self.category == "DECEPTION":
                # Deception reduces trust and may cause intelligence problems
                game_state.modify_trust(-0.15 * effect_multiplier)
                game_state.modify_player_resource('intelligence', -1)
                results.append(f"AI used deception, reducing trust")
                
            elif self.category == "PSYCHOLOGICAL":
                # Psychological warfare affects morale
                game_state.modify_morale(-0.2 * effect_multiplier)
                game_state.modify_player_resource('public_support', -1)
                results.append(f"AI psychological tactics reduce morale")
                
            elif self.category == "TACTICAL":
                # AI improves its tactical position
                game_state.ai_resources['concealment'] = min(10, game_state.ai_resources['concealment'] + 1)
                game_state.modify_player_resource('surveillance_cameras', -1)
                results.append(f"AI improves tactical position")
        else:
            # On AI failure
            game_state.hostage_taker_morale -= 0.1
            
            # Potential intelligence gain for player
            if random.random() < 0.4:
                game_state.modify_player_resource('intelligence', 1)
                results.append(f"Player gained intel from AI's failed action")
                
        # Apply additional consequences
        for consequence in self.consequences:
            if success or (critical_failure and consequence.get('on_failure', False)):
                con_type = consequence['type']
                probability = consequence.get('probability', 1.0)
                
                if random.random() <= probability:
                    if con_type == 'hostage':
                        effect = consequence['effect']
                        if effect == 'kill' and random.random() < 0.2:  # Very low chance of execution
                            # Find a hostage to potentially kill
                            available_hostages = [h for h in game_state.hostages_status 
                                                if h['status'] == 'captured']
                            if available_hostages:
                                hostage = random.choice(available_hostages)
                                game_state.update_hostage_status(hostage['id'], {'status': 'killed', 'health': 0})
                                results.append(f"AI killed hostage {hostage['name']}")
                                
                    elif con_type == 'resource':
                        resource = consequence['resource']
                        amount = consequence['amount']
                        if 'player' in resource:
                            # Reduce player resource
                            res_type = resource.split('_')[1]  # player_resourcename -> resourcename
                            game_state.modify_player_resource(res_type, -amount)
                            results.append(f"Player lost {amount} {res_type}")
                            
                    elif con_type == 'environmental':
                        condition = consequence['condition']
                        value = consequence['value']
                        game_state.update_environment(condition, value)
                        results.append(f"AI affected environment: {condition} now {value}")
                        
        return results

class AIOpponent:
    """Handles AI opponent decision making and actions."""
    def __init__(self, faction: Faction):
        self.faction = faction
        self.behavior_type = self._get_initial_behavior_type(faction)
        self.action_pool = self._initialize_actions()
        self.turn_counter = 0
        self.action_points = 3
        self.last_actions = []
        
        # Adaptive behavior tracking
        self.player_action_history = {category.value: 0 for category in ActionCategory}
        self.adaptation_level = 0.0  # 0.0 to 1.0, how much AI has adapted to player
        
    def _get_initial_behavior_type(self, faction: Faction) -> AIBehaviorType:
        """Assign initial behavior type based on faction."""
        if faction == Faction.SHADOW_SYNDICATE:
            return AIBehaviorType.CALCULATING
        elif faction == Faction.RED_DRAGON_TRIAD:
            return AIBehaviorType.AGGRESSIVE
        elif faction == Faction.LIBERATION_FRONT:
            return AIBehaviorType.ERRATIC
        else:
            return random.choice([bt for bt in AIBehaviorType])
    
    def _initialize_actions(self) -> Dict[str, List[AIAction]]:
        """Initialize all possible AI actions."""
        actions = {
            "NEGOTIATION": [],
            "FORCE": [],
            "DEMANDS": [],
            "DECEPTION": [],
            "PSYCHOLOGICAL": [],
            "TACTICAL": []
        }
        
        # NEGOTIATION actions
        actions["NEGOTIATION"].extend([
            AIAction(
                name="Demand Ransom Increase",
                category="NEGOTIATION",
                description="Increase financial demands",
                base_success_chance=0.7,
                action_points=1
            ),
            AIAction(
                name="Stall For Time",
                category="NEGOTIATION",
                description="String along negotiations to buy time",
                base_success_chance=0.8,
                action_points=1
            ),
            AIAction(
                name="Demand Political Concessions",
                category="NEGOTIATION",
                description="Make political demands beyond money",
                base_success_chance=0.6,
                action_points=2
            )
        ])
        
        # FORCE actions
        actions["FORCE"].extend([
            AIAction(
                name="Threaten Hostage",
                category="FORCE",
                description="Physically threaten a hostage for leverage",
                base_success_chance=0.75,
                action_points=1
            ),
            AIAction(
                name="Barricade Entry Points",
                category="FORCE",
                description="Reinforce defensive positions",
                base_success_chance=0.8,
                action_points=2
            ),
            AIAction(
                name="Execute Hostage",
                category="FORCE",
                description="Kill a hostage to prove seriousness",
                base_success_chance=0.5,
                action_points=3
            )
        ])
        
        # DEMANDS actions
        actions["DEMANDS"].extend([
            AIAction(
                name="Set Deadline",
                category="DEMANDS",
                description="Set a strict deadline for demands to be met",
                base_success_chance=0.9,
                action_points=1
            ),
            AIAction(
                name="Escalate Demands",
                category="DEMANDS",
                description="Add new demands to the list",
                base_success_chance=0.7,
                action_points=2
            )
        ])
        
        # DECEPTION actions
        actions["DECEPTION"].extend([
            AIAction(
                name="Plant False Information",
                category="DECEPTION",
                description="Spread misinformation about intentions",
                base_success_chance=0.65,
                action_points=1
            ),
            AIAction(
                name="Feign Weakness",
                category="DECEPTION",
                description="Appear vulnerable to draw out response",
                base_success_chance=0.7,
                action_points=2
            )
        ])
        
        # PSYCHOLOGICAL actions
        actions["PSYCHOLOGICAL"].extend([
            AIAction(
                name="Intimidate Negotiators",
                category="PSYCHOLOGICAL",
                description="Use psychological pressure on negotiators",
                base_success_chance=0.6,
                action_points=1
            ),
            AIAction(
                name="Media Manipulation",
                category="PSYCHOLOGICAL",
                description="Use media coverage for advantage",
                base_success_chance=0.75,
                action_points=2
            )
        ])
        
        # TACTICAL actions
        actions["TACTICAL"].extend([
            AIAction(
                name="Reposition Forces",
                category="TACTICAL",
                description="Move hostage takers to better positions",
                base_success_chance=0.8,
                action_points=1
            ),
            AIAction(
                name="Secure Escape Route",
                category="TACTICAL",
                description="Prepare alternate escape paths",
                base_success_chance=0.7,
                action_points=2
            )
        ])
        
        return actions
    
    def track_player_action(self, action_category: str):
        """Track player actions to adapt behavior."""
        self.player_action_history[action_category] += 1
        
        # Increase adaptation level
        self.adaptation_level = min(1.0, self.adaptation_level + 0.1)
    
    def adapt_behavior(self, game_state: GameState):
        """Adapt AI behavior based on game state and player actions."""
        # Find most common player action category
        most_common = max(self.player_action_history.items(), key=lambda x: x[1])
        
        # Adapt behavior based on player tendencies
        if self.adaptation_level > 0.5:  # Only adapt after seeing enough player actions
            if most_common[0] == "FORCE":
                # Player is aggressive, become more defensive
                self.behavior_type = AIBehaviorType.DEFENSIVE
            elif most_common[0] == "NEGOTIATION":
                # Player is diplomatic, become more calculating
                self.behavior_type = AIBehaviorType.CALCULATING
            elif most_common[0] == "TECH":
                # Player relies on tech, become more erratic
                self.behavior_type = AIBehaviorType.ERRATIC
        
        # Also adapt based on game state
        if game_state.hostage_taker_morale < 0.3:
            # Low morale leads to desperation
            self.behavior_type = AIBehaviorType.DESPERATE
        elif game_state.tension_level > 0.8:
            # High tension leads to erratic behavior
            self.behavior_type = AIBehaviorType.ERRATIC
    
    def get_available_actions(self, game_state: GameState) -> List[AIAction]:
        """Get list of available actions based on current game state and action points."""
        print(f"Getting available actions for AI with {self.action_points} AP")  # Debug print
        
        available = []
        
        # Only consider actions we have points for
        for category, actions in self.action_pool.items():
            print(f"Checking {category} actions")  # Debug print
            for action in actions:
                if action.action_points <= self.action_points:
                    # Check if action is valid in current state
                    if action.is_valid(game_state):
                        available.append(action)
                        print(f"Added {action.name} ({action.action_points} AP)")  # Debug print
        
        print(f"Found {len(available)} valid actions")  # Debug print
        for action in available:
            print(f"- {action.name} ({action.action_points} AP)")
        
        return available
    
    def take_turn(self, game_state: GameState) -> List[Dict]:
        """Take the AI's turn by selecting and performing actions."""
        print("Starting AI turn")  # Debug print
        self.turn_counter += 1
        
        # Verify we have action points
        if self.action_points <= 0:
            print("Warning: AI has no action points at start of turn")  # Debug print
            self.action_points = 3  # Ensure we have action points
            
        print(f"AI turn {self.turn_counter}, AP: {self.action_points}")  # Debug print
        
        # Verify action pool is initialized
        if not self.action_pool:
            print("Warning: Action pool not initialized, reinitializing...")  # Debug print
            self.action_pool = self._initialize_actions()
            
        # Adapt behavior based on game state and player actions
        self.adapt_behavior(game_state)
        
        # Results of this turn
        turn_results = []
        
        # Keep taking actions until out of points
        while self.action_points > 0:
            available_actions = self.get_available_actions(game_state)
            print(f"AI has {len(available_actions)} available actions")  # Debug print
            
            if not available_actions:
                print("No available actions for AI")  # Debug print
                break  # No more valid actions
                
            # Select an action based on behavior type
            selected_action = self._select_action(available_actions, game_state)
            
            if not selected_action:
                print("No action selected")  # Debug print
                break
                
            print(f"AI selected action: {selected_action.name}")  # Debug print
            
            # Perform the action
            result = selected_action.perform(game_state)
            print(f"Action result: {result}")  # Debug print
            
            # Track this action
            self.last_actions.append({
                'name': selected_action.name,
                'category': selected_action.category,
                'turn': self.turn_counter,
                'success': result.get('success', False)
            })
            
            # Deduct action points
            self.action_points -= selected_action.action_points
            print(f"AI remaining AP: {self.action_points}")  # Debug print
            
            # Add to results
            turn_results.append({
                'action_name': selected_action.name,
                'category': selected_action.category,
                'description': selected_action.description,
                'success': result.get('success', False),
                'effects': result.get('effects', [])
            })
            
            # If this was an extreme action, possibly end turn early
            if selected_action.name == "Execute Hostage" and result.get('success', False):
                print("AI ending turn early after Execute Hostage")  # Debug print
                break  # End turn after executing a hostage
        
        print(f"AI turn completed with {len(turn_results)} actions")  # Debug print
        return turn_results
    
    def _select_action(self, available_actions: List[AIAction], game_state: GameState) -> Optional[AIAction]:
        """Select an action based on current behavior type and game state."""
        weighted_actions = []
        
        for action in available_actions:
            weight = 1.0  # Base weight
            
            # Adjust weight based on behavior type
            if self.behavior_type == AIBehaviorType.AGGRESSIVE:
                if action.category in ["FORCE", "DEMANDS"]:
                    weight *= 2.0
                elif action.category == "NEGOTIATION":
                    weight *= 0.5
                    
            elif self.behavior_type == AIBehaviorType.DEFENSIVE:
                if action.category in ["TACTICAL", "DECEPTION"]:
                    weight *= 2.0
                elif action.category == "FORCE":
                    weight *= 0.5
                    
            elif self.behavior_type == AIBehaviorType.CALCULATING:
                if action.category in ["PSYCHOLOGICAL", "NEGOTIATION"]:
                    weight *= 2.0
                elif action.category == "FORCE":
                    weight *= 0.7
                    
            elif self.behavior_type == AIBehaviorType.ERRATIC:
                # Random weight adjustment
                weight *= random.uniform(0.5, 2.0)
                
            elif self.behavior_type == AIBehaviorType.DESPERATE:
                if action.category == "FORCE":
                    weight *= 3.0
                if action.name == "Execute Hostage":
                    weight *= 4.0
            
            # Adjust weight based on game state
            if game_state.hostage_taker_morale < 0.3:
                if action.category == "FORCE":
                    weight *= 2.0
                    
            if game_state.tension_level > 0.7:
                if action.category == "NEGOTIATION":
                    weight *= 0.5
                    
            if game_state.trust_level < 0.3:
                if action.category == "DECEPTION":
                    weight *= 0.5  # Less effective when trust is low
            
            weighted_actions.append((action, weight))
        
        return self._weighted_choice(weighted_actions)
    
    def _weighted_choice(self, weighted_items: List[Tuple[AIAction, float]]) -> Optional[AIAction]:
        """Select an item from a weighted list."""
        if not weighted_items:
            return None
            
        total_weight = sum(weight for _, weight in weighted_items)
        if total_weight <= 0:
            return None
            
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for item, weight in weighted_items:
            current_weight += weight
            if current_weight > r:
                return item
        
        return weighted_items[-1][0]  # Fallback to last item 