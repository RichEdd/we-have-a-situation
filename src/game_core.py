from enum import Enum, auto
import random

class GamePhase(Enum):
    SETUP = auto()
    NEGOTIATION = auto()
    ACTION = auto()
    END_TURN = auto()
    GAME_OVER = auto()

class ActionType(Enum):
    NEGOTIATE = auto()
    TACTICAL = auto()
    SPECIAL = auto()
    FORCE = auto()

class Action:
    def __init__(self, name, action_type, ap_cost, success_chance, description=""):
        self.name = name
        self.type = action_type
        self.ap_cost = ap_cost
        self.success_chance = success_chance
        self.description = description

class GameState:
    def __init__(self):
        # Core game state
        self.turn = 1
        self.trust = 50  # 0-100
        self.tension = 30  # Starting at 30% - situations are tense but manageable
        self.morale = 75  # Starting morale at 75%
        
        # Personnel and environment info
        self.hostages = 5
        self.terrorists = 3  # Number of terrorists
        self.exits = 2      # Number of available exits
        self.cameras = 4    # Number of functioning cameras
        
        # Game state
        self.ap = 3        # Action Points
        self.phase = GamePhase.SETUP
        
        # Game flags
        self.game_over = False
        self.victory = False
        
        # History
        self.messages = []
        self.message_history = ["Crisis situation begins. Hostage negotiation team deployed."]  # Initialize with starting message
    
    def add_message(self, text):
        """Add a message to the game history."""
        self.message_history.append(text)
        # Keep only the last 8 messages
        if len(self.message_history) > 8:
            self.message_history = self.message_history[-8:]
    
    def update_state(self, trust_change=0, tension_change=0, morale_change=0):
        """Update game state values, keeping them within 0-100 range."""
        self.trust = max(0, min(100, self.trust + trust_change))
        self.tension = max(0, min(100, self.tension + tension_change))
        self.morale = max(0, min(100, self.morale + morale_change))
        
        # Check win/loss conditions
        if self.trust >= 90:
            self.game_over = True
            self.victory = True
            self.add_message("Victory! Situation resolved peacefully.")
        elif self.tension >= 90:
            self.game_over = True
            self.victory = False
            self.add_message("Game Over: Situation escalated out of control.")
        elif self.hostages <= 0:
            self.game_over = True
            self.victory = False
            self.add_message("Game Over: All hostages lost.")

class ActionSystem:
    def __init__(self):
        self.actions = self._initialize_actions()
    
    def _initialize_actions(self):
        return {
            ActionType.NEGOTIATE: [
                Action("Talk Down", ActionType.NEGOTIATE, 1, 0.7,
                      "Attempt to calm the situation."),
                Action("Make Deal", ActionType.NEGOTIATE, 2, 0.8,
                      "Offer a deal to the hostage takers."),
                Action("Build Trust", ActionType.NEGOTIATE, 2, 0.75,
                      "Work on building trust with the hostage takers."),
                Action("Gather Intel", ActionType.NEGOTIATE, 1, 0.9,
                      "Learn more about the situation through dialogue.")
            ],
            ActionType.TACTICAL: [
                Action("Position Units", ActionType.TACTICAL, 1, 0.8,
                      "Move units into tactical positions."),
                Action("Secure Perimeter", ActionType.TACTICAL, 2, 0.85,
                      "Establish a secure perimeter around the area."),
                Action("Scout Location", ActionType.TACTICAL, 1, 0.9,
                      "Gather tactical information about the location."),
                Action("Set Up Command", ActionType.TACTICAL, 2, 0.8,
                      "Establish a command center for operations.")
            ],
            ActionType.SPECIAL: [
                Action("Crisis Expert", ActionType.SPECIAL, 3, 0.7,
                      "Use expert crisis management techniques."),
                Action("Psychological Edge", ActionType.SPECIAL, 2, 0.75,
                      "Apply advanced psychological tactics."),
                Action("Inside Contact", ActionType.SPECIAL, 2, 0.8,
                      "Utilize an inside contact for advantage."),
                Action("Media Control", ActionType.SPECIAL, 2, 0.85,
                      "Manage media coverage of the situation.")
            ],
            ActionType.FORCE: [
                Action("Show Force", ActionType.FORCE, 1, 0.8,
                      "Display force to intimidate."),
                Action("Breach Prep", ActionType.FORCE, 2, 0.75,
                      "Prepare for potential breach action."),
                Action("Sniper Setup", ActionType.FORCE, 2, 0.7,
                      "Position snipers for tactical advantage."),
                Action("Quick Strike", ActionType.FORCE, 3, 0.65,
                      "Prepare for immediate tactical action.")
            ]
        }
    
    def get_actions(self, action_type):
        """Get all actions of a specific type."""
        return self.actions.get(action_type, [])
    
    def execute_action(self, action, game_state):
        """Execute an action and return success status and message."""
        if game_state.ap < action.ap_cost:
            message = f"Not enough AP to perform {action.name}"
            game_state.add_message(message)
            return False, message

        game_state.ap -= action.ap_cost
        
        # Determine success based on chance
        success = random.random() < action.success_chance
        
        if success:
            # Apply action effects
            if action.type == ActionType.NEGOTIATE:
                game_state.trust += 10
                game_state.tension -= 5
                game_state.morale += 5
                message = f"Successfully used {action.name}. Trust increased."
            elif action.type == ActionType.TACTICAL:
                game_state.tension -= 10
                game_state.morale += 10
                message = f"Successfully executed {action.name}. Tension decreased."
            elif action.type == ActionType.SPECIAL:
                game_state.trust += 5
                game_state.tension -= 15
                game_state.morale += 15
                message = f"Special action {action.name} succeeded!"
            elif action.type == ActionType.FORCE:
                game_state.tension += 20
                game_state.morale -= 5
                message = f"Force action {action.name} executed. Tension increased significantly."
        else:
            # Failed action effects
            game_state.tension += 10
            game_state.morale -= 10
            message = f"{action.name} failed. Tension increased."

        # Ensure values stay within bounds
        game_state.trust = max(0, min(100, game_state.trust))
        game_state.tension = max(0, min(100, game_state.tension))
        game_state.morale = max(0, min(100, game_state.morale))
        
        # Add message to history
        game_state.add_message(message)
        
        return success, message 