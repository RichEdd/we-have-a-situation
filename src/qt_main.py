import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QTextEdit, QListWidget,
                           QPushButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from core.game_engine import GameEngine, PlayerRole, PlayerAffiliation
from core.dialogue_system import DialogueSystem
from scenarios.base_scenario import create_bank_scenario

class NegotiationGameGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("We Have a Situation!")
        self.setGeometry(100, 100, 800, 800)  # Made taller to accommodate logo
        
        # Initialize game components
        self.game_engine = GameEngine()
        self.dialogue_system = DialogueSystem()
        self.scenario = create_bank_scenario()
        self.game_engine.initialize_game(self.scenario.get_initial_state())
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add logo
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_label = QLabel()
        pixmap = QPixmap("assets/WHAS-logo.png")
        scaled_pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_frame)
        
        # Create game state section
        state_frame = QFrame()
        state_layout = QHBoxLayout(state_frame)
        self.turn_label = QLabel("Turn: 0")
        self.player_label = QLabel("Current Player: Negotiator")
        state_layout.addWidget(self.turn_label)
        state_layout.addWidget(self.player_label)
        layout.addWidget(state_frame)
        
        # Create resources section
        resources_frame = QFrame()
        resources_layout = QVBoxLayout(resources_frame)
        resources_layout.addWidget(QLabel("Resources:"))
        self.resources_text = QTextEdit()
        self.resources_text.setMaximumHeight(100)
        self.resources_text.setReadOnly(True)
        resources_layout.addWidget(self.resources_text)
        layout.addWidget(resources_frame)
        
        # Create dialogue history section
        history_frame = QFrame()
        history_layout = QVBoxLayout(history_frame)
        history_layout.addWidget(QLabel("Dialogue History:"))
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        layout.addWidget(history_frame)
        
        # Create action options section
        options_frame = QFrame()
        options_layout = QVBoxLayout(options_frame)
        options_layout.addWidget(QLabel("Available Actions:"))
        self.options_list = QListWidget()
        options_layout.addWidget(self.options_list)
        layout.addWidget(options_frame)
        
        # Create action button
        self.action_button = QPushButton("Take Action")
        self.action_button.clicked.connect(self.take_action)
        layout.addWidget(self.action_button)
        
        # Create status bar
        self.statusBar().showMessage("Select your action")
        
        # Update initial game state
        self.update_game_state()
    
    def update_game_state(self):
        # Update turn and player labels
        self.turn_label.setText(f"Turn: {self.game_engine.game_state.current_turn}")
        self.player_label.setText(f"Current Player: {self.game_engine.game_state.current_player_role.value}")
        
        # Update resources display
        self.resources_text.clear()
        for role, player in self.game_engine.game_state.players.items():
            resources_str = ", ".join(f"{k}: {v}" for k, v in player.resources.items())
            self.resources_text.append(f"{role.value}: {resources_str}")
        
        # Update available options
        self.options_list.clear()
        current_player = self.game_engine.game_state.players[self.game_engine.game_state.current_player_role]
        self.current_options = self.dialogue_system.get_available_options({
            "role": current_player.role.value,
            "resources": current_player.resources
        })
        
        for i, option in enumerate(self.current_options, 1):
            self.options_list.addItem(
                f"{i}. {option.text} ({option.type.value}, {option.success_chance*100:.0f}% success)")
    
    def take_action(self):
        selected_items = self.options_list.selectedItems()
        if not selected_items:
            self.statusBar().showMessage("Please select an action first")
            return
        
        selected_index = self.options_list.row(selected_items[0])
        chosen_option = self.current_options[selected_index]
        result = self.dialogue_system.process_dialogue(
            chosen_option,
            self.game_engine.game_state.__dict__
        )
        
        # Display results in history
        self.history_text.append(f"\n{'='*50}")
        self.history_text.append(f"Turn {self.game_engine.game_state.current_turn}:")
        self.history_text.append(f"Action: {chosen_option.text}")
        self.history_text.append(f"Success: {'Yes' if result['success'] else 'No'}")
        self.history_text.append(f"Response: {result['response']}")
        self.history_text.append("Effects:")
        for effect in result['effects']:
            self.history_text.append(f"- {effect['type']}")
            if 'new_tension' in effect:
                self.history_text.append(f"  Tension: {effect['new_tension']:.2f}")
            if 'new_trust' in effect:
                self.history_text.append(f"  Trust: {effect['new_trust']:.2f}")
        
        # Process turn in game engine
        self.game_engine.process_turn({"type": "dialogue", "option": chosen_option})
        
        # Check win conditions
        if self.game_engine._check_win_conditions():
            self.statusBar().showMessage("Game Over!")
            self.action_button.setEnabled(False)
        else:
            self.update_game_state()
            self.statusBar().showMessage("Action completed. Select your next move.")

def main():
    app = QApplication(sys.argv)
    window = NegotiationGameGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 