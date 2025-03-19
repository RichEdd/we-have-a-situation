import tkinter as tk
from tkinter import Text, Listbox, Button, Label, Frame, Scrollbar
from core.game_engine import GameEngine, PlayerRole, PlayerAffiliation
from core.dialogue_system import DialogueSystem
from scenarios.base_scenario import create_bank_scenario

class NegotiationGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("We Have a Situation!")
        self.root.geometry("800x600")
        
        # Initialize game components
        self.game_engine = GameEngine()
        self.dialogue_system = DialogueSystem()
        self.scenario = create_bank_scenario()
        self.game_engine.initialize_game(self.scenario.get_initial_state())
        
        self.create_widgets()
        self.update_game_state()
    
    def create_widgets(self):
        # Game state display
        state_frame = Frame(self.root)
        state_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.turn_label = Label(state_frame, text="Turn: 0")
        self.turn_label.pack(side=tk.LEFT, padx=5)
        
        self.player_label = Label(state_frame, text="Current Player: Negotiator")
        self.player_label.pack(side=tk.LEFT, padx=5)
        
        # Resources display
        resources_frame = Frame(self.root)
        resources_frame.pack(fill=tk.X, padx=10, pady=5)
        
        Label(resources_frame, text="Resources:").pack(anchor=tk.W)
        self.resources_text = Text(resources_frame, height=4, width=70)
        self.resources_text.pack(fill=tk.X)
        
        # Dialogue history
        history_frame = Frame(self.root)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        Label(history_frame, text="Dialogue History:").pack(anchor=tk.W)
        self.history_text = Text(history_frame, height=10, width=70)
        history_scrollbar = Scrollbar(history_frame)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.history_text.config(yscrollcommand=history_scrollbar.set)
        history_scrollbar.config(command=self.history_text.yview)
        
        # Action options
        options_frame = Frame(self.root)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        Label(options_frame, text="Available Actions:").pack(anchor=tk.W)
        self.options_listbox = Listbox(options_frame, height=4, width=70)
        self.options_listbox.pack(fill=tk.X)
        
        # Action button
        self.action_button = Button(self.root, text="Take Action", command=self.take_action)
        self.action_button.pack(pady=10)
        
        # Status bar
        self.status_label = Label(self.root, text="Select your action")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def update_game_state(self):
        # Update turn and player labels
        self.turn_label.config(text=f"Turn: {self.game_engine.game_state.current_turn}")
        self.player_label.config(text=f"Current Player: {self.game_engine.game_state.current_player_role.value}")
        
        # Update resources display
        self.resources_text.delete('1.0', tk.END)
        for role, player in self.game_engine.game_state.players.items():
            resources_str = ", ".join(f"{k}: {v}" for k, v in player.resources.items())
            self.resources_text.insert(tk.END, f"{role.value}: {resources_str}\n")
        
        # Update available options
        self.options_listbox.delete(0, tk.END)
        current_player = self.game_engine.game_state.players[self.game_engine.game_state.current_player_role]
        self.current_options = self.dialogue_system.get_available_options({
            "role": current_player.role.value,
            "resources": current_player.resources
        })
        
        for i, option in enumerate(self.current_options, 1):
            self.options_listbox.insert(tk.END, 
                f"{i}. {option.text} ({option.type.value}, {option.success_chance*100:.0f}% success)")
    
    def take_action(self):
        selection = self.options_listbox.curselection()
        if not selection:
            self.status_label.config(text="Please select an action first")
            return
        
        chosen_option = self.current_options[selection[0]]
        result = self.dialogue_system.process_dialogue(
            chosen_option,
            self.game_engine.game_state.__dict__
        )
        
        # Display results in history
        self.history_text.insert(tk.END, f"\n{'='*50}\n")
        self.history_text.insert(tk.END, f"Turn {self.game_engine.game_state.current_turn}:\n")
        self.history_text.insert(tk.END, f"Action: {chosen_option.text}\n")
        self.history_text.insert(tk.END, f"Success: {'Yes' if result['success'] else 'No'}\n")
        self.history_text.insert(tk.END, f"Response: {result['response']}\n")
        self.history_text.insert(tk.END, "Effects:\n")
        for effect in result['effects']:
            self.history_text.insert(tk.END, f"- {effect['type']}\n")
            if 'new_tension' in effect:
                self.history_text.insert(tk.END, f"  Tension: {effect['new_tension']:.2f}\n")
            if 'new_trust' in effect:
                self.history_text.insert(tk.END, f"  Trust: {effect['new_trust']:.2f}\n")
        
        self.history_text.see(tk.END)  # Scroll to bottom
        
        # Process turn in game engine
        self.game_engine.process_turn({"type": "dialogue", "option": chosen_option})
        
        # Check win conditions
        if self.game_engine._check_win_conditions():
            self.status_label.config(text="Game Over!")
            self.action_button.config(state=tk.DISABLED)
        else:
            self.update_game_state()
            self.status_label.config(text="Action completed. Select your next move.")

def main():
    root = tk.Tk()
    app = NegotiationGameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 