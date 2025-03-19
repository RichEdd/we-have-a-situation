import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QTextEdit, QListWidget,
                           QPushButton, QFrame, QComboBox, QProgressBar,
                           QTabWidget, QGridLayout)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QPixmap, QFont, QColor
from core.game_engine import GameEngine
from core.dialogue_system import (DialogueSystem, ActionSystem, GameState,
                                Faction, ActionCategory, Action)
from scenarios.base_scenario import create_bank_scenario

class NegotiationGameGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("We Have a Situation!")
        self.setGeometry(100, 100, 1200, 900)  # Made wider and taller
        
        # Initialize game components
        self.action_system = ActionSystem()
        self.dialogue_system = DialogueSystem()
        self.scenario = create_bank_scenario()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Add logo
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_label = QLabel()
        pixmap = QPixmap("assets/WHAS-logo.png")
        scaled_pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        main_layout.addWidget(logo_frame)
        
        # Create faction selection at start
        self.setup_faction_selection(main_layout)
        
        # Create game interface (hidden initially)
        self.game_widget = QWidget()
        self.game_layout = QVBoxLayout(self.game_widget)
        self.setup_game_interface()
        self.game_widget.hide()
        main_layout.addWidget(self.game_widget)
        
        # Create status bar
        self.statusBar().showMessage("Select your faction to begin")
    
    def setup_faction_selection(self, parent_layout):
        self.faction_frame = QFrame()
        faction_layout = QVBoxLayout(self.faction_frame)
        
        # Title
        title_label = QLabel("Choose Your Faction")
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        faction_layout.addWidget(title_label)
        
        # Faction selection combo box
        self.faction_combo = QComboBox()
        self.faction_combo.addItems([
            Faction.FBI.value,
            Faction.CIA.value,
            Faction.LOCAL_PD.value
        ])
        faction_layout.addWidget(self.faction_combo)
        
        # Start button
        start_button = QPushButton("Start Game")
        start_button.clicked.connect(self.start_game)
        faction_layout.addWidget(start_button)
        
        parent_layout.addWidget(self.faction_frame)
    
    def setup_game_interface(self):
        # Create game state section
        state_frame = QFrame()
        state_layout = QGridLayout(state_frame)
        
        self.turn_label = QLabel("Turn: 1")
        self.faction_label = QLabel("Faction: ")
        self.ap_label = QLabel("Action Points: 3")
        
        state_layout.addWidget(self.turn_label, 0, 0)
        state_layout.addWidget(self.faction_label, 0, 1)
        state_layout.addWidget(self.ap_label, 0, 2)
        
        self.game_layout.addWidget(state_frame)
        
        # Create metrics section
        metrics_frame = QFrame()
        metrics_layout = QGridLayout(metrics_frame)
        
        # Trust and Tension meters
        self.trust_bar = QProgressBar()
        self.tension_bar = QProgressBar()
        self.intel_bar = QProgressBar()
        
        for bar in [self.trust_bar, self.tension_bar, self.intel_bar]:
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setValue(50)
        
        metrics_layout.addWidget(QLabel("Trust:"), 0, 0)
        metrics_layout.addWidget(self.trust_bar, 0, 1)
        metrics_layout.addWidget(QLabel("Tension:"), 1, 0)
        metrics_layout.addWidget(self.tension_bar, 1, 1)
        metrics_layout.addWidget(QLabel("Intel:"), 2, 0)
        metrics_layout.addWidget(self.intel_bar, 2, 1)
        
        self.game_layout.addWidget(metrics_frame)
        
        # Create tabbed action categories
        action_tabs = QTabWidget()
        
        # Create a tab for each action category
        for category in ActionCategory:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            action_list = QListWidget()
            tab_layout.addWidget(action_list)
            action_tabs.addTab(tab, category.value)
            setattr(self, f"{category.value.lower()}_list", action_list)
        
        self.game_layout.addWidget(action_tabs)
        
        # Create special abilities section
        special_frame = QFrame()
        special_layout = QVBoxLayout(special_frame)
        special_layout.addWidget(QLabel("Special Abilities:"))
        self.special_list = QListWidget()
        special_layout.addWidget(self.special_list)
        
        self.game_layout.addWidget(special_frame)
        
        # Create resources section
        resources_frame = QFrame()
        resources_layout = QVBoxLayout(resources_frame)
        resources_layout.addWidget(QLabel("Resources:"))
        self.resources_text = QTextEdit()
        self.resources_text.setMaximumHeight(100)
        self.resources_text.setReadOnly(True)
        resources_layout.addWidget(self.resources_text)
        
        self.game_layout.addWidget(resources_frame)
        
        # Create dialogue/game history tabs
        history_tabs = QTabWidget()
        
        # Dialogue History tab
        dialogue_tab = QWidget()
        dialogue_layout = QVBoxLayout(dialogue_tab)
        self.dialogue_text = QTextEdit()
        self.dialogue_text.setReadOnly(True)
        dialogue_layout.addWidget(self.dialogue_text)
        history_tabs.addTab(dialogue_tab, "Dialogue History")
        
        # Game History tab
        game_tab = QWidget()
        game_layout = QVBoxLayout(game_tab)
        self.game_history_text = QTextEdit()
        self.game_history_text.setReadOnly(True)
        game_layout.addWidget(self.game_history_text)
        history_tabs.addTab(game_tab, "Game History")
        
        self.game_layout.addWidget(history_tabs)
        
        # Create action button
        self.action_button = QPushButton("Take Action")
        self.action_button.clicked.connect(self.take_action)
        self.game_layout.addWidget(self.action_button)
    
    def start_game(self):
        selected_faction = next(f for f in Faction 
                              if f.value == self.faction_combo.currentText())
        
        # Initialize game state with selected faction
        self.game_state = GameState(selected_faction)
        
        # Hide faction selection and show game interface
        self.faction_frame.hide()
        self.game_widget.show()
        
        # Update interface
        self.faction_label.setText(f"Faction: {selected_faction.value}")
        self.update_game_state()
        
        self.statusBar().showMessage("Game started. Choose your action.")
    
    def update_game_state(self):
        # Update basic state labels
        self.turn_label.setText(f"Turn: {self.game_state.turn}")
        self.ap_label.setText(f"Action Points: {self.game_state.action_points}")
        
        # Update progress bars
        self.trust_bar.setValue(int(self.game_state.trust_level * 100))
        self.tension_bar.setValue(int(self.game_state.tension_level * 100))
        self.intel_bar.setValue(int(self.game_state.intel_level * 100))
        
        # Update resources display
        self.resources_text.clear()
        for resource, amount in self.game_state.resources.items():
            self.resources_text.append(f"{resource.capitalize()}: {amount}")
        
        # Update available actions in each category
        available_actions = self.action_system.get_available_actions(self.game_state)
        
        # Clear all action lists
        for category in ActionCategory:
            action_list = getattr(self, f"{category.value.lower()}_list")
            action_list.clear()
        
        # Populate action lists
        for category, actions in available_actions.items():
            action_list = getattr(self, f"{category.value.lower()}_list")
            for action in actions:
                if not action.is_special:
                    item_text = (f"{action.name} ({action.action_points} AP) - "
                               f"{action.success_chance*100:.0f}% success")
                    action_list.addItem(item_text)
        
        # Update special abilities list
        self.special_list.clear()
        for category, actions in available_actions.items():
            special_actions = [a for a in actions if a.is_special]
            for action in special_actions:
                if action.name not in self.game_state.used_special_abilities:
                    item_text = (f"Level {action.special_level} - {action.name} "
                               f"({action.action_points} AP) - "
                               f"{action.success_chance*100:.0f}% success")
                    self.special_list.addItem(item_text)
    
    def take_action(self):
        # Get the currently selected tab (action category)
        action_tabs = self.findChild(QTabWidget)
        current_tab = action_tabs.currentWidget()
        action_list = current_tab.findChild(QListWidget)
        
        # Check if an action is selected from regular actions
        selected_action = None
        if action_list and action_list.selectedItems():
            selected_item = action_list.selectedItems()[0]
            action_text = selected_item.text()
            selected_action = self._parse_action_from_text(action_text, is_special=False)
        
        # Check if a special ability is selected
        elif self.special_list.selectedItems():
            selected_item = self.special_list.selectedItems()[0]
            action_text = selected_item.text()
            selected_action = self._parse_action_from_text(action_text, is_special=True)
        
        if not selected_action:
            self.statusBar().showMessage("Please select an action first")
            return
        
        # Validate action points
        if selected_action.action_points > self.game_state.action_points:
            self.statusBar().showMessage(f"Not enough action points! Need {selected_action.action_points} AP")
            return
        
        # Execute the action
        result = self.action_system.execute_action(selected_action, self.game_state)
        
        # Update game history with the result
        self._update_history(selected_action, result)
        
        # Update game state
        self.game_state.action_points -= selected_action.action_points
        if selected_action.is_special:
            self.game_state.used_special_abilities.append(selected_action.name)
        
        # Apply action effects
        self._apply_action_effects(result)
        
        # Update the UI
        self.update_game_state()
        
        # Check if turn should end
        if self.game_state.action_points <= 0:
            self._end_turn()
        else:
            self.statusBar().showMessage(f"Action completed. {self.game_state.action_points} AP remaining")
    
    def _parse_action_from_text(self, text, is_special):
        """Parse action details from the displayed text."""
        # Extract action name and AP cost
        if is_special:
            # Format: "Level X - Name (Y AP) - Z% success"
            level = int(text.split("Level ")[1].split(" -")[0])
            name = text.split(" - ")[1].split(" (")[0]
            ap_cost = int(text.split("(")[1].split(" AP)")[0])
        else:
            # Format: "Name (X AP) - Y% success"
            name = text.split(" (")[0]
            ap_cost = int(text.split("(")[1].split(" AP)")[0])
            level = 0
        
        return Action(
            name=name,
            action_points=ap_cost,
            is_special=is_special,
            special_level=level if is_special else 0
        )
    
    def _update_history(self, action, result):
        """Update both dialogue and game history with action results."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        # Update dialogue history if it's a dialogue action
        if action.category == ActionCategory.DIALOGUE:
            self.dialogue_text.append(f"\n[{timestamp}] {self.game_state.faction.value}:")
            self.dialogue_text.append(f"► {action.name}")
            if result.get('response'):
                self.dialogue_text.append(f"← {result['response']}")
        
        # Update game history
        self.game_history_text.append(f"\n[{timestamp}] {self.game_state.faction.value}:")
        self.game_history_text.append(f"► Used {action.name}")
        
        if result.get('success'):
            self.game_history_text.append("✓ Action successful")
        else:
            self.game_history_text.append("✗ Action failed")
        
        if result.get('effects'):
            self.game_history_text.append("Effects:")
            for effect in result['effects']:
                self.game_history_text.append(f"  • {effect}")
    
    def _apply_action_effects(self, result):
        """Apply the effects of an action to the game state."""
        if not result.get('effects'):
            return
            
        for effect in result['effects']:
            if 'trust' in effect:
                self.game_state.trust_level = max(0, min(1, effect['trust']))
            if 'tension' in effect:
                self.game_state.tension_level = max(0, min(1, effect['tension']))
            if 'intel' in effect:
                self.game_state.intel_level = max(0, min(1, effect['intel']))
            if 'resources' in effect:
                for resource, change in effect['resources'].items():
                    self.game_state.resources[resource] = max(0, 
                        self.game_state.resources.get(resource, 0) + change)
    
    def _end_turn(self):
        """Handle end of turn logic."""
        # Reset action points
        self.game_state.action_points = 3
        
        # Clear used special abilities
        self.game_state.used_special_abilities.clear()
        
        # Increment turn counter
        self.game_state.turn += 1
        
        # Update UI
        self.update_game_state()
        self.statusBar().showMessage("New turn started")
        
        # Add turn marker to history
        self.game_history_text.append(f"\n{'='*30}")
        self.game_history_text.append(f"Turn {self.game_state.turn} Started")
        self.game_history_text.append(f"{'='*30}")

def main():
    app = QApplication(sys.argv)
    window = NegotiationGameGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 