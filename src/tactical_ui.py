import pygame
import pygame.gfxdraw
import sys
import math
import random
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum, auto
from core.game_state import GameState
from core.dialogue_system import ActionSystem, DialogueSystem, GameAction, ActionCategory
from core.enums import Faction
from input_handler import InputHandler

# Constants
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 60

# Layout
SIDE_PANEL_WIDTH = 350
TOP_HUD_HEIGHT = 80
BOTTOM_HUD_HEIGHT = 100
DIALOG_HEIGHT = 400
ACTION_MENU_Y = WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT - 300

# Colors - Military/Tech Theme
COLORS = {
    'background': (10, 12, 14),  # Near black
    'panel_bg': (20, 24, 28, 220),  # Dark blue-grey, semi-transparent
    'text': (0, 255, 170),  # Bright cyan-green
    'text_dim': (0, 180, 120),  # Dimmer cyan-green
    'highlight': (255, 255, 255),  # White (changed from bright green)
    'warning': (255, 160, 0),  # Orange
    'critical': (255, 60, 60),  # Red
    'success': (40, 255, 40),  # Bright green
    'failure': (255, 40, 40),  # Bright red
    'inactive': (80, 90, 100),  # Muted blue-grey
    'meter_bg': (30, 34, 38),  # Slightly lighter than background
    'trust': (0, 200, 100),  # Green
    'tension': (255, 100, 0),  # Orange-red
    'intel': (0, 150, 255),  # Bright blue
    'ap': (255, 200, 0),  # Gold
    'grid': (30, 40, 50),  # Dark blue-grey for background grid
    'border': (0, 255, 170, 30),  # Glowing cyan-green, very transparent
    'ai_overlay': (10, 12, 14, 200),  # Dark overlay for AI turn
    'ai_text': (255, 100, 100),  # Red text for AI actions
}

# UI Elements
UI_ELEMENTS = {
    'panel_border_radius': 8,
    'meter_height': 16,
    'grid_size': 40,
    'border_width': 2,
    'glow_radius': 20,
}

class UIState(Enum):
    """Enum for the various UI states."""
    SIDE_SELECT = auto()
    FACTION_SELECT = auto()
    MAIN_GAME = auto()
    ACTION_MENU = auto()
    EXIT_CONFIRM = auto()
    AI_TURN = auto()  # New state for AI turn
    HISTORY_LOG = auto()  # New state for viewing game history

class InputDirection(Enum):
    """Enum for directional input."""
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()

class TacticalUI:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        # Get the display info
        display_info = pygame.display.Info()
        self.native_width = display_info.current_w
        self.native_height = display_info.current_h
        
        # Initialize display with a windowed mode first
        self.is_fullscreen = False
        self.window_pos = (100, 100)  # Default window position
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("We Have a Situation! - Tactical")
        self.clock = pygame.time.Clock()
        
        # Store the windowed size
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Initialize game components
        self.action_system = ActionSystem()
        self.dialogue_system = DialogueSystem()
        
        # Initialize fonts
        self._init_fonts()
        
        # Initialize UI state
        self.ui_state = UIState.SIDE_SELECT  # Start with side selection
        self.selected_index = 0              # Used for menu selection
        self.current_category_index = 0      # Used for action categories
        self.selected_action_index = -1      # Used for action selection in wheel menu
        
        # AI turn display control
        self.show_ai_turn = False
        self.history_page = 0
        self.history_entries_per_page = 15
        
        self.game_state = None
        
        # Side and faction options
        self.sides = ["Negotiator", "Hostage Taker"]
        self.faction_descriptions = {
            Faction.FBI: "Elite tactical unit with jurisdiction autonomy, special agents including mentalists, psychological profilers, and bomb experts.",
            Faction.CIA: "Advanced intelligence division with high-tech capabilities, able to hack cameras, control infrastructure, and deploy drones.",
            Faction.LOCAL_PD: "Experienced local force with intimate knowledge of terrain, building layouts, and community connections.",
            Faction.SHADOW_SYNDICATE: "Professional criminal organization with diverse skillsets and international connections.",
            Faction.RED_DRAGON_TRIAD: "Hierarchical crime syndicate specializing in smuggling operations and extortion.",
            Faction.LIBERATION_FRONT: "Radical political group fighting for autonomy through both activism and violence."
        }
        self.faction_groups = {
            "Negotiator": [
                Faction.FBI,
                Faction.CIA,
                Faction.LOCAL_PD
            ],
            "Hostage Taker": [
                Faction.SHADOW_SYNDICATE,
                Faction.RED_DRAGON_TRIAD,
                Faction.LIBERATION_FRONT
            ]
        }
        self.selected_side = None
        
        # Initialize controller support
        self.controllers = []
        self._setup_controllers()
        
        # Action categories and available actions
        self.categories = list(ActionCategory)
        self.available_actions = {category: [] for category in ActionCategory}
        
        # Input settings
        self.input_cooldown = 50  # ms (further reduced for more responsive D-pad)
        self.last_input_time = 0
        self.stick_deadzone = 0.3
        
        # Button press tracking
        self.button_cooldown = 250  # ms cooldown for button presses (longer than input_cooldown)
        self.last_button_press = {i: 0 for i in range(20)}  # Track last press time for each button
        
        # D-pad specific cooldown (longer to avoid rapid movement)
        self.dpad_cooldown = 300  # ms cooldown specifically for D-pad inputs
        self.last_dpad_input_time = 0  # Track last D-pad input time
        
        # Direction tracking to prevent rapid repeats
        self.last_direction = None
    
    def _init_fonts(self):
        """Initialize fonts for different UI elements."""
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.hud_font = pygame.font.Font(None, 24)
        self.dialog_font = pygame.font.Font(None, 18)
    
    def _setup_controllers(self):
        """Initialize any connected controllers."""
        # Re-initialize controllers each time to get fresh state
        self.controllers = []
        
        # Check for connected controllers
        num_joysticks = pygame.joystick.get_count()
        print(f"Found {num_joysticks} controllers")
        
        for i in range(num_joysticks):
            try:
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.controllers.append(joystick)
                print(f"Controller initialized: {joystick.get_name()}")
                print(f"  Buttons: {joystick.get_numbuttons()}")
                print(f"  Axes: {joystick.get_numaxes()}")
                print(f"  Hats: {joystick.get_numhats()}")
            except pygame.error as e:
                print(f"Error initializing controller {i}: {e}")
        
        # Return whether we have controllers
        return len(self.controllers) > 0
    
    def _draw_panel(self, rect: pygame.Rect, title: str):
        """Draw a standard panel with background and border."""
        # Draw background
        pygame.draw.rect(self.screen, COLORS['panel_bg'], rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
        
        # Draw border
        pygame.draw.rect(self.screen, COLORS['border'], rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'],
                        width=UI_ELEMENTS['border_width'])
        
        # Draw title if provided
        if title:
            title_surf = self.menu_font.render(title, True, COLORS['text'])
            title_rect = title_surf.get_rect(topleft=(rect.left + 10, rect.top + 10))
            self.screen.blit(title_surf, title_rect)
    
    def _draw_meter(self, rect: pygame.Rect, value: float, color: Tuple[int, int, int]):
        """Draw a meter with background and fill."""
        # Draw background
        pygame.draw.rect(self.screen, COLORS['meter_bg'], rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
        
        # Draw fill
        fill_rect = pygame.Rect(rect.left, rect.top,
                              rect.width * value, rect.height)
        pygame.draw.rect(self.screen, color, fill_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
    
    def _draw_tactical_grid(self):
        """Draw background tactical grid."""
        for x in range(0, WINDOW_WIDTH, UI_ELEMENTS['grid_size']):
            alpha = 255 if x % (UI_ELEMENTS['grid_size'] * 4) == 0 else 100
            pygame.draw.line(self.screen, (*COLORS['grid'], alpha),
                           (x, 0), (x, WINDOW_HEIGHT))
        
        for y in range(0, WINDOW_HEIGHT, UI_ELEMENTS['grid_size']):
            alpha = 255 if y % (UI_ELEMENTS['grid_size'] * 4) == 0 else 100
            pygame.draw.line(self.screen, (*COLORS['grid'], alpha),
                           (0, y), (WINDOW_WIDTH, y))
    
    def _draw_top_hud(self):
        """Draw the top HUD with core metrics and resources."""
        if not self.game_state:
            return
        
        # Draw HUD background
        hud_rect = pygame.Rect(0, 0, WINDOW_WIDTH, TOP_HUD_HEIGHT)
        self._draw_panel(hud_rect, "")
        
        # Draw faction and turn info
        faction_text = f"{self.game_state.player_faction.value} | Turn {self.game_state.turn}"
        faction_surf = self.hud_font.render(faction_text, True, COLORS['text'])
        self.screen.blit(faction_surf, (20, 10))
        
        # Draw AP
        ap_text = f"Action Points: {self.game_state.action_points}"
        ap_surf = self.hud_font.render(ap_text, True, COLORS['ap'])
        self.screen.blit(ap_surf, (20, 40))
        
        # Draw core metrics
        metrics = [
            ("Trust", self.game_state.trust_level, COLORS['trust']),
            ("Tension", self.game_state.tension_level, COLORS['tension']),
            ("Morale", self.game_state.intel_level, COLORS['intel'])
        ]
        
        x = WINDOW_WIDTH//2 - 300
        for name, value, color in metrics:
            # Draw label
            label = self.hud_font.render(name, True, color)
            self.screen.blit(label, (x, 10))
            
            # Draw meter
            meter_rect = pygame.Rect(x, 35, 150, UI_ELEMENTS['meter_height'])
            self._draw_meter(meter_rect, value, color)
            
            x += 200
        
        # Draw resources with more spacing
        man_pos = (WINDOW_WIDTH - 400, 25)
        equ_pos = (WINDOW_WIDTH - 250, 25)
        int_pos = (WINDOW_WIDTH - 100, 25)
        
        # Draw each resource separately
        man_surf = self.hud_font.render("M: " + str(self.game_state.resources['manpower']), True, COLORS['text'])
        equ_surf = self.hud_font.render("E: " + str(self.game_state.resources['equipment']), True, COLORS['text'])
        int_surf = self.hud_font.render("I: " + str(self.game_state.resources['intel']), True, COLORS['text'])
        
        self.screen.blit(man_surf, man_pos)
        self.screen.blit(equ_surf, equ_pos)
        self.screen.blit(int_surf, int_pos)
    
    def _draw_objectives_panel(self):
        """Draw the objectives panel."""
        if not self.game_state:
            return
            
        rect = pygame.Rect(20, TOP_HUD_HEIGHT + 20,
                          SIDE_PANEL_WIDTH, 200)
        self._draw_panel(rect, "OBJECTIVES")
        
        y = rect.top + 50
        max_width = rect.width - 60  # Account for padding and priority indicator
        
        for obj in self.game_state.get_objectives():
            # Priority indicator
            priority_color = (COLORS['critical'] if obj['priority'] == 1 else
                            COLORS['warning'] if obj['priority'] == 2 else
                            COLORS['text_dim'])
            pygame.draw.circle(self.screen, priority_color,
                             (rect.left + 20, y + 10), 5)
            
            # Objective text with word wrapping
            color = (COLORS['success'] if obj['complete'] else
                    COLORS['failure'] if obj['failed'] else
                    COLORS['text'])
            
            # Word wrap implementation
            words = obj['text'].split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_surface = self.hud_font.render(test_line, True, color)
                
                if test_surface.get_width() <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
                
            # Draw each line
            line_y = y
            for line in lines:
                text_surf = self.hud_font.render(line, True, color)
                self.screen.blit(text_surf, (rect.left + 40, line_y))
                line_y += 25
                
            y = line_y + 10  # Add space between objectives
    
    def _draw_dialogue_panel(self):
        """Draw the dialogue panel at the bottom of the screen."""
        if not self.game_state:
            return
        
        # Set up panel dimensions
        panel_width = WINDOW_WIDTH - SIDE_PANEL_WIDTH - 20
        panel_x = 10
        panel_y = WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT - DIALOG_HEIGHT - 10
        panel_height = DIALOG_HEIGHT
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Draw panel background
        self._draw_panel(panel_rect, "Comms Channel")
        
        # Calculate visible dialogue entries (most recent first)
        dialogue_entries = self.game_state.dialogue_history[-10:]  # Show last 10 entries
        
        # Display entries
        entry_height = 30
        content_y = panel_y + panel_height - (len(dialogue_entries) * entry_height) - 20
        
        for entry in dialogue_entries:
            # Determine text color based on speaker
            text_color = COLORS['text']
            if entry['speaker'] == "SYSTEM":
                text_color = COLORS['warning']
            elif entry['speaker'] == self.game_state.player_faction.value:
                text_color = COLORS['success']
            elif not entry.get('success', True):
                text_color = COLORS['failure']
            
            # Format entry text
            entry_text = f"{entry['speaker']}: {entry['text']}"
            
            # Render text
            text_surf = self.dialog_font.render(entry_text, True, text_color)
            text_rect = text_surf.get_rect(topleft=(panel_x + 20, content_y))
            
            # Draw this entry
            self.screen.blit(text_surf, text_rect)
            content_y += entry_height
    
    def _draw_ai_turn_overlay(self):
        """Draw the AI turn overlay with actions taken by the AI."""
        if not self.game_state:
            return
            
        # Draw semi-transparent overlay covering the entire screen
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 14, 200))  # Dark overlay
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = f"{self.game_state.ai_faction.value} ACTIONS"
        title_surf = self.title_font.render(title_text, True, (255, 100, 100))  # Red text
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 150))
        self.screen.blit(title_surf, title_rect)
        
        # Draw AI actions
        actions = self.game_state.ai_last_turn_actions
        
        if not actions:
            no_action_surf = self.menu_font.render("No actions taken this turn.", True, COLORS['text'])
            no_action_rect = no_action_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            self.screen.blit(no_action_surf, no_action_rect)
        else:
            # Draw each action
            y_start = WINDOW_HEIGHT//2 - (len(actions) * 50)//2
            for i, action in enumerate(actions):
                y_pos = y_start + i * 60
                
                # Action name and result
                action_text = f"{action['action']} - {action['category']}"
                result_text = "Success" if action['success'] else "Failed"
                
                action_surf = self.menu_font.render(action_text, True, COLORS['text'])
                result_surf = self.menu_font.render(result_text, True, 
                                                  COLORS['success'] if action['success'] else COLORS['failure'])
                
                action_rect = action_surf.get_rect(center=(WINDOW_WIDTH//2, y_pos))
                result_rect = result_surf.get_rect(center=(WINDOW_WIDTH//2, y_pos + 30))
                
                self.screen.blit(action_surf, action_rect)
                self.screen.blit(result_surf, result_rect)
                
                # Draw effects if any
                if 'effects' in action and action['effects']:
                    effect_text = ", ".join(action['effects'][:2])  # Show first 2 effects only
                    if len(action['effects']) > 2:
                        effect_text += "..."
                        
                    effect_surf = self.dialog_font.render(effect_text, True, COLORS['text_dim'])
                    effect_rect = effect_surf.get_rect(center=(WINDOW_WIDTH//2, y_pos + 50))
                    self.screen.blit(effect_surf, effect_rect)
        
        # Draw continue prompt
        continue_text = "Press A to continue"
        continue_surf = self.dialog_font.render(continue_text, True, COLORS['text'])
        continue_rect = continue_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 150))
        self.screen.blit(continue_surf, continue_rect)
        
    def _draw_game_history(self):
        """Draw a full-screen history log panel."""
        if not self.game_state or not hasattr(self.game_state, 'game_history'):
            return
            
        # Create semi-transparent background
        bg_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        bg_surface.fill((10, 12, 14, 230))  # Dark, semi-transparent background
        self.screen.blit(bg_surface, (0, 0))
        
        # Define panel dimensions
        panel_width = WINDOW_WIDTH - 200
        panel_height = WINDOW_HEIGHT - 200
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2
        
        # Draw panel
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        self._draw_panel(panel_rect, "GAME HISTORY")
        
        # Get history entries
        history_entries = self.game_state.game_history
        
        # Calculate pagination
        entries_per_page = self.history_entries_per_page
        total_pages = max(1, (len(history_entries) + entries_per_page - 1) // entries_per_page)
        
        # Get current page entries
        start_idx = self.history_page * entries_per_page
        end_idx = min(start_idx + entries_per_page, len(history_entries))
        current_page_entries = history_entries[start_idx:end_idx]
        
        # Draw entries
        entry_y = panel_y + 50
        entry_x = panel_x + 30
        line_height = 24
        
        for i, entry in enumerate(current_page_entries):
            # Format: [Turn X] Message
            turn_text = f"[Turn {entry.get('turn', '?')}]"
            turn_surf = self.hud_font.render(turn_text, True, COLORS['ap'])
            self.screen.blit(turn_surf, (entry_x, entry_y))
            
            # Entry message
            msg_surf = self.hud_font.render(entry.get('message', 'Unknown event'), True, COLORS['text'])
            self.screen.blit(msg_surf, (entry_x + 100, entry_y))
            
            entry_y += line_height
        
        # Draw pagination info
        page_text = f"Page {self.history_page + 1}/{total_pages}"
        page_surf = self.hud_font.render(page_text, True, COLORS['text_dim'])
        page_rect = page_surf.get_rect(center=(WINDOW_WIDTH//2, panel_y + panel_height - 30))
        self.screen.blit(page_surf, page_rect)
        
        # Draw navigation hints
        hint_y = panel_y + panel_height + 20
        
        # Up/down navigation hint
        nav_hint = "↑/↓: Navigate Pages"
        nav_surf = self.hud_font.render(nav_hint, True, COLORS['text'])
        nav_rect = nav_surf.get_rect(center=(WINDOW_WIDTH//2 - 150, hint_y))
        self.screen.blit(nav_surf, nav_rect)
        
        # Back hint
        back_hint = "ESC/B: Return to Game"
        back_surf = self.hud_font.render(back_hint, True, COLORS['text'])
        back_rect = back_surf.get_rect(center=(WINDOW_WIDTH//2 + 150, hint_y))
        self.screen.blit(back_surf, back_rect)
    
    def _draw_tactical_panel(self):
        """Draw the tactical information panel."""
        if not self.game_state:
            return
            
        rect = pygame.Rect(WINDOW_WIDTH - SIDE_PANEL_WIDTH - 20,
                          TOP_HUD_HEIGHT + 20,
                          SIDE_PANEL_WIDTH, 200)
        self._draw_panel(rect, "TACTICAL")
        
        y = rect.top + 50
        for pos, active in self.game_state.tactical_positions.items():
            color = COLORS['success'] if active else COLORS['inactive']
            text = self.hud_font.render(pos.replace('_', ' ').title(), True, color)
            self.screen.blit(text, (rect.left + 20, y))
            y += 30
    
    def _draw_history_panel(self):
        """Draw the action history panel."""
        if not self.game_state:
            return
            
        rect = pygame.Rect(WINDOW_WIDTH - SIDE_PANEL_WIDTH - 20,
                          TOP_HUD_HEIGHT + 240,
                          SIDE_PANEL_WIDTH,
                          WINDOW_HEIGHT - TOP_HUD_HEIGHT - BOTTOM_HUD_HEIGHT - 260)
        self._draw_panel(rect, f"TURN {self.game_state.turn}")
        
        y = rect.top + 50
        for entry in self.game_state.game_history[-6:]:
            # Turn number
            turn_text = f"T{entry['turn']}"
            turn_surf = self.hud_font.render(turn_text, True, COLORS['text_dim'])
            self.screen.blit(turn_surf, (rect.left + 20, y))
            
            # Action
            color = COLORS['success'] if entry.get('success', False) else COLORS['failure']
            action_surf = self.hud_font.render(entry['action'], True, color)
            self.screen.blit(action_surf, (rect.left + 70, y))
            
            # Effects
            if entry.get('effects'):
                # Handle different types of effects
                effects_text = ""
                try:
                    # If effects is a list of ActionEffect enums
                    if isinstance(entry['effects'], list) and all(hasattr(e, 'value') for e in entry['effects']):
                        effects_text = ", ".join(e.value for e in entry['effects'])
                    # If effects is a list of dictionaries
                    elif isinstance(entry['effects'], list) and all(isinstance(e, dict) for e in entry['effects']):
                        effects_text = ", ".join(e.get('type', 'effect') for e in entry['effects'])
                    # Fallback
                    else:
                        effects_text = "Effects applied"
                except Exception as e:
                    effects_text = "Effects applied"
                
                effects_surf = self.dialog_font.render(effects_text, True, COLORS['text_dim'])
                self.screen.blit(effects_surf, (rect.left + 30, y + 25))
            
            y += 50
    
    def _get_scaled_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Scale a rectangle based on current screen size."""
        current_w, current_h = self.screen.get_size()
        scale_x = current_w / WINDOW_WIDTH
        scale_y = current_h / WINDOW_HEIGHT
        
        return pygame.Rect(
            int(rect.x * scale_x),
            int(rect.y * scale_y),
            int(rect.width * scale_x),
            int(rect.height * scale_y)
        )
    
    def _draw_action_menu(self):
        """Draw a wheel-based action menu with four directional options."""
        if not self.game_state:
            return

        # Draw semi-transparent background
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS['background'])
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))

        # Get current category and actions
        current_category = list(ActionCategory)[self.current_category_index]
        actions = self.available_actions.get(current_category, [])

        # Draw category name at the top
        title = f"{current_category.value} Actions"
        title_surf = self.title_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, 80))
        self.screen.blit(title_surf, title_rect)

        # Center point for the wheel
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        # Draw the center circle
        pygame.draw.circle(self.screen, COLORS['panel_bg'], (center_x, center_y), 100)
        pygame.draw.circle(self.screen, COLORS['border'], (center_x, center_y), 100, width=2)
        
        # Draw center text describing the wheel
        center_text = f"{len(actions)} Available Actions"
        center_surf = self.menu_font.render(center_text, True, COLORS['text'])
        center_rect = center_surf.get_rect(center=(center_x, center_y - 10))
        self.screen.blit(center_surf, center_rect)
        
        # Draw AP info
        ap_text = f"AP: {self.game_state.action_points}"
        ap_surf = self.menu_font.render(ap_text, True, COLORS['ap'])
        ap_rect = ap_surf.get_rect(center=(center_x, center_y + 20))
        self.screen.blit(ap_surf, ap_rect)

        if actions:
            # Draw up to 4 actions in a wheel/compass pattern
            directions = [
                ("UP", (0, -200), "↑", InputDirection.UP),       # North
                ("RIGHT", (200, 0), "→", InputDirection.RIGHT),  # East
                ("DOWN", (0, 200), "↓", InputDirection.DOWN),    # South 
                ("LEFT", (-200, 0), "←", InputDirection.LEFT)    # West
            ]
            
            # Show all available actions (up to 4)
            action_count = min(len(actions), 4)
            for i in range(action_count):
                if i >= len(directions):
                    break
                
                direction, offset, arrow, input_dir = directions[i]
                pos_x = center_x + offset[0]
                pos_y = center_y + offset[1]
                action = actions[i]
                
                # Check if we have enough AP for this action
                can_afford = self.game_state.action_points >= action.action_points
                
                # Check if this action is currently selected
                is_selected = i == self.selected_action_index
                
                # Draw connecting line from center to action
                line_color = COLORS['highlight'] if is_selected else COLORS['border'] if can_afford else COLORS['inactive']
                line_width = 3 if is_selected else 2
                pygame.draw.line(self.screen, line_color, 
                                (center_x, center_y), 
                                (pos_x, pos_y - 60 if direction in ["UP", "DOWN"] else pos_y), 
                                width=line_width)
                
                # Draw directional indicator
                dir_pos = (0, 0)
                if direction == "UP":
                    dir_pos = (center_x, center_y - 60)
                elif direction == "RIGHT":
                    dir_pos = (center_x + 60, center_y)
                elif direction == "DOWN":
                    dir_pos = (center_x, center_y + 60)
                else:  # LEFT
                    dir_pos = (center_x - 60, center_y)
                
                # Draw arrow in a circle
                arrow_bg_color = COLORS['highlight'] if is_selected else COLORS['panel_bg'] if can_afford else COLORS['inactive']
                pygame.draw.circle(self.screen, arrow_bg_color, dir_pos, 30)
                pygame.draw.circle(self.screen, line_color, dir_pos, 30, width=line_width)
                
                # Draw the arrow
                arrow_color = COLORS['text'] if can_afford or is_selected else COLORS['inactive']
                arrow_surf = self.title_font.render(arrow, True, arrow_color)
                arrow_rect = arrow_surf.get_rect(center=dir_pos)
                self.screen.blit(arrow_surf, arrow_rect)
                
                # Draw action box
                box_width = 240
                box_height = 120
                box_rect = pygame.Rect(pos_x - box_width//2, pos_y - box_height//2, box_width, box_height)
                
                # Make box stand out if selected
                box_bg_color = COLORS['highlight'] if is_selected else COLORS['panel_bg'] if can_afford else COLORS['inactive']
                if is_selected:
                    # Draw a slightly larger box behind for a glowing effect if selected
                    glow_rect = pygame.Rect(box_rect.left-3, box_rect.top-3, box_rect.width+6, box_rect.height+6)
                    pygame.draw.rect(self.screen, COLORS['text'], glow_rect, border_radius=12)
                
                # Use different opacity for the box background if selected
                if is_selected:
                    box_bg_color = (*COLORS['panel_bg'][:3], 255)  # Full opacity
                
                box_border_color = COLORS['highlight'] if is_selected else COLORS['border'] if can_afford else COLORS['inactive']
                
                pygame.draw.rect(self.screen, box_bg_color, box_rect, border_radius=10)
                pygame.draw.rect(self.screen, box_border_color, box_rect, border_radius=10, width=2 if not is_selected else 3)
                
                # Draw action name with number
                name_color = COLORS['highlight'] if is_selected else COLORS['text'] if can_afford else COLORS['inactive']
                name_text = f"{i+1}. {action.name}"
                name_surf = self.menu_font.render(name_text, True, name_color)
                name_rect = name_surf.get_rect(centerx=pos_x, centery=pos_y - 40)
                self.screen.blit(name_surf, name_rect)
                
                # Draw AP cost and success chance
                stats_color = COLORS['highlight'] if is_selected else COLORS['ap'] if can_afford else COLORS['inactive']
                stats_text = f"{action.action_points} AP | {int(action.success_chance * 100)}% Success"
                stats_surf = self.hud_font.render(stats_text, True, stats_color)
                stats_rect = stats_surf.get_rect(centerx=pos_x, centery=pos_y - 10)
                self.screen.blit(stats_surf, stats_rect)
                
                # Draw brief description
                desc_color = COLORS['highlight'] if is_selected else COLORS['text_dim'] if can_afford else COLORS['inactive']
                if hasattr(action, 'description') and action.description:
                    desc_text = action.description[:30] + "..." if len(action.description) > 30 else action.description
                    desc_surf = self.hud_font.render(desc_text, True, desc_color)
                    desc_rect = desc_surf.get_rect(centerx=pos_x, centery=pos_y + 20)
                    self.screen.blit(desc_surf, desc_rect)
                
        else:
            # Draw "No actions available" message
            no_actions_text = "No actions available for this category"
            no_actions_surf = self.menu_font.render(no_actions_text, True, COLORS['warning'])
            no_actions_rect = no_actions_surf.get_rect(center=(center_x, center_y + 150))
            self.screen.blit(no_actions_surf, no_actions_rect)

        # Draw controls hints at the bottom in a clearer format
        hint_y = WINDOW_HEIGHT - 130
        
        # Action selection hint
        action_hint = "↑/↓/←/→: Select Action"
        action_surf = self.hud_font.render(action_hint, True, COLORS['text'])
        action_rect = action_surf.get_rect(center=(WINDOW_WIDTH//2 - 250, hint_y))
        self.screen.blit(action_surf, action_rect)
        
        # Confirmation hint
        confirm_hint = "Enter/A: Confirm Selection"
        confirm_surf = self.hud_font.render(confirm_hint, True, COLORS['text'])
        confirm_rect = confirm_surf.get_rect(center=(WINDOW_WIDTH//2, hint_y))
        self.screen.blit(confirm_surf, confirm_rect)
        
        # Back hint
        back_hint = "ESC/B: Back to Main"
        back_surf = self.hud_font.render(back_hint, True, COLORS['text'])
        back_rect = back_surf.get_rect(center=(WINDOW_WIDTH//2 + 250, hint_y))
        self.screen.blit(back_surf, back_rect)
        
        # Draw category navigation hint
        hint_y += 30
        cat_hint = "Q/E or LB/RB or Right Stick: Change Category"
        cat_surf = self.hud_font.render(cat_hint, True, COLORS['text'])
        cat_rect = cat_surf.get_rect(center=(WINDOW_WIDTH//2, hint_y))
        self.screen.blit(cat_surf, cat_rect)
        
        # Draw available actions count
        hint_y += 30
        count_text = f"Showing {min(len(actions), 4)}/{len(actions)} Available Actions"
        count_surf = self.hud_font.render(count_text, True, COLORS['text_dim'])
        count_rect = count_surf.get_rect(center=(WINDOW_WIDTH//2, hint_y))
        self.screen.blit(count_surf, count_rect)
    
    def _draw_bottom_hud(self):
        """Draw the bottom HUD with controls and current category."""
        current_w, current_h = self.screen.get_size()
        rect = self._get_scaled_rect(pygame.Rect(0, WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT,
                                               WINDOW_WIDTH, BOTTOM_HUD_HEIGHT))
        self._draw_panel(rect, "")
        
        if self.ui_state == UIState.MAIN_GAME:
            # Current category
            category = self.categories[self.current_category_index].value
            text = self.menu_font.render(category, True, COLORS['text'])
            text_rect = text.get_rect(center=(current_w//2, rect.centery))
            self.screen.blit(text, text_rect)
            
            # Category selection arrows
            if self.current_category_index > 0:
                left = self.menu_font.render("◄", True, COLORS['text'])
                self.screen.blit(left, (text_rect.left - 40, text_rect.top))
            
            if self.current_category_index < len(self.categories) - 1:
                right = self.menu_font.render("►", True, COLORS['text'])
                self.screen.blit(right, (text_rect.right + 10, text_rect.top))
        
        # Draw controls - ensure they're visible in the bottom right
        controls = self._get_controls_for_state()
        x = current_w - 200
        y = rect.top + 20
        for key, action in controls:
            text = f"{key}: {action}"
            surf = self.hud_font.render(text, True, COLORS['text'])
            self.screen.blit(surf, (x, y))
            y += 25
    
    def _get_controls_for_state(self) -> List[Tuple[str, str]]:
        """Get control hints for current UI state."""
        if self.ui_state == UIState.SIDE_SELECT:
            return [
                ("↑/↓", "Select Side"),
                ("Enter/A", "Confirm")
            ]
        elif self.ui_state == UIState.FACTION_SELECT:
            return [
                ("↑/↓", "Select"),
                ("Enter/A", "Confirm"),
                ("Esc/B", "Back")
            ]
        elif self.ui_state == UIState.MAIN_GAME:
            return [
                ("←/→", "Category"),
                ("Enter/A", "Select"),
                ("Y", "Special"),
                ("H", "History"),
                ("Q", "Exit")
            ]
        elif self.ui_state == UIState.ACTION_MENU:
            return [
                ("←/→", "Select"),
                ("Enter/A", "Confirm"),
                ("Esc/B", "Back")
            ]
        elif self.ui_state == UIState.EXIT_CONFIRM:
            return [
                ("Y", "Confirm Exit"),
                ("N", "Cancel")
            ]
        elif self.ui_state == UIState.HISTORY_LOG:
            return [
                ("↑/↓", "Navigate"),
                ("Esc/B", "Back")
            ]
        elif self.ui_state == UIState.AI_TURN:
            return [
                ("Enter/A", "Continue")
            ]
        return []
    
    def draw(self):
        """Main draw method - renders the current UI state."""
        # Clear the screen
        self.screen.fill(COLORS['background'])
        
        # Draw tactical grid background
        self._draw_tactical_grid()
        
        # Draw based on current UI state
        if self.ui_state == UIState.SIDE_SELECT:
            self._draw_side_selection()
        elif self.ui_state == UIState.FACTION_SELECT:
            self._draw_faction_selection()
        elif self.ui_state == UIState.MAIN_GAME:
            self._draw_main_game()
        elif self.ui_state == UIState.ACTION_MENU:
            # Draw the main game as background for action menu
            self._draw_main_game()
            self._draw_action_menu()
        elif self.ui_state == UIState.EXIT_CONFIRM:
            # Draw the main game as background for exit confirmation
            self._draw_main_game()
            self._draw_exit_confirmation()
        elif self.ui_state == UIState.AI_TURN:
            # Draw the main game as background for AI turn
            self._draw_main_game()
            self._draw_ai_turn_overlay()
        elif self.ui_state == UIState.HISTORY_LOG:
            # Draw the main game as background for history log
            self._draw_main_game()
            self._draw_game_history()
        
        # Update display
        pygame.display.flip()
    
    def _draw_side_selection(self):
        """Draw the side selection screen."""
        # Draw title
        title = self.title_font.render("SELECT YOUR SIDE", True, COLORS['text'])
        title_rect = title.get_rect(centerx=WINDOW_WIDTH//2, y=200)
        self.screen.blit(title, title_rect)
        
        # Draw side options
        y = 300
        for i, side in enumerate(self.sides):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Draw selection background
            if selected:
                rect = pygame.Rect(WINDOW_WIDTH//2 - 200, y - 10, 400, 50)
                pygame.draw.rect(self.screen, COLORS['border'], rect,
                               border_radius=5)
            
            # Draw side name
            text = self.menu_font.render(side, True, color)
            text_rect = text.get_rect(centerx=WINDOW_WIDTH//2, y=y)
            self.screen.blit(text, text_rect)
            
            y += 60
    
    def _draw_faction_selection(self):
        """Draw the faction selection screen."""
        # Draw title
        title = self.title_font.render("SELECT YOUR FACTION", True, COLORS['text'])
        title_rect = title.get_rect(centerx=WINDOW_WIDTH//2, y=200)
        self.screen.blit(title, title_rect)
        
        # Draw faction options
        y = 300
        for i, faction in enumerate(self.faction_groups[self.selected_side]):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Draw selection background
            if selected:
                rect = pygame.Rect(WINDOW_WIDTH//2 - 485, y - 10, 970, 80)
                pygame.draw.rect(self.screen, COLORS['border'], rect,
                               border_radius=5)
            
            # Draw faction name
            text = self.menu_font.render(faction.value, True, color)
            text_rect = text.get_rect(centerx=WINDOW_WIDTH//2, y=y)
            self.screen.blit(text, text_rect)
            
            # Draw faction description
            if selected:
                desc = self.faction_descriptions[faction]
                desc_surf = self.hud_font.render(desc, True, COLORS['text_dim'])
                desc_rect = desc_surf.get_rect(centerx=WINDOW_WIDTH//2, y=y + 30)
                self.screen.blit(desc_surf, desc_rect)
            
            y += 100  # Increased spacing to accommodate descriptions
    
    def _draw_main_game(self):
        """Draw the main game interface."""
        self._draw_top_hud()
        self._draw_objectives_panel()
        self._draw_dialogue_panel()
        self._draw_tactical_panel()
        self._draw_history_panel()
        self._draw_bottom_hud()
    
    def _draw_exit_confirmation(self):
        """Draw the exit confirmation screen."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill(COLORS['background'])
        overlay.set_alpha(200)  # More opaque for better visibility
        self.screen.blit(overlay, (0, 0))
        
        # Create confirmation box
        box_width = 500
        box_height = 250
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = (WINDOW_HEIGHT - box_height) // 2
        
        # Draw box background
        pygame.draw.rect(self.screen, COLORS['panel_bg'],
                       (box_x, box_y, box_width, box_height),
                       border_radius=UI_ELEMENTS['panel_border_radius'])
        
        # Draw box border
        pygame.draw.rect(self.screen, COLORS['border'],
                       (box_x, box_y, box_width, box_height),
                       border_radius=UI_ELEMENTS['panel_border_radius'],
                       width=UI_ELEMENTS['border_width'])
        
        # Draw confirmation text
        title = self.title_font.render("Exit Game?", True, COLORS['text'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, box_y + 50))
        self.screen.blit(title, title_rect)
        
        # Draw options
        option_y = box_y + 130
        
        # No option (left)
        no_selected = self.selected_index == 0
        no_color = COLORS['highlight'] if no_selected else COLORS['text']
        no_box = pygame.Rect(box_x + 80, option_y - 5, 120, 50)
        if no_selected:
            pygame.draw.rect(self.screen, COLORS['border'], no_box, border_radius=5)
        no_text = self.menu_font.render("NO", True, no_color)
        no_rect = no_text.get_rect(center=(box_x + 140, option_y + 20))
        self.screen.blit(no_text, no_rect)
        
        # Yes option (right)
        yes_selected = self.selected_index == 1
        yes_color = COLORS['highlight'] if yes_selected else COLORS['text']
        yes_box = pygame.Rect(box_x + 300, option_y - 5, 120, 50)
        if yes_selected:
            pygame.draw.rect(self.screen, COLORS['border'], yes_box, border_radius=5)
        yes_text = self.menu_font.render("YES", True, yes_color)
        yes_rect = yes_text.get_rect(center=(box_x + 360, option_y + 20))
        self.screen.blit(yes_text, yes_rect)
        
        # Draw hint
        hint_text = "Use ←/→ to select | Enter to confirm | ESC to cancel"
        hint_surf = self.hud_font.render(hint_text, True, COLORS['text'])
        hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, box_y + 200))
        self.screen.blit(hint_surf, hint_rect)

    def _handle_back_button(self):
        """Handle B button press for backing out of screens."""
        print("Handling B button (back) functionality")
        
        # Logic for different UI states
        if self.ui_state == UIState.MAIN_GAME:
            print("Going from main game to exit confirm")
            self.ui_state = UIState.EXIT_CONFIRM
            self.selected_index = 0  # Default to 'No'
            return True
            
        elif self.ui_state == UIState.ACTION_MENU:
            print("Going from action menu to main game")
            self.ui_state = UIState.MAIN_GAME
            # Reset action selection
            self.selected_action_index = -1
            return True
            
        elif self.ui_state == UIState.EXIT_CONFIRM:
            print("Canceling exit confirmation")
            self.ui_state = UIState.MAIN_GAME
            return True
            
        elif self.ui_state == UIState.FACTION_SELECT:
            print("Going back to side selection")
            self.ui_state = UIState.SIDE_SELECT
            return True
            
        elif self.ui_state == UIState.AI_TURN:
            print("Returning from AI turn to main game")
            self.ui_state = UIState.MAIN_GAME
            self.show_ai_turn = False
            return True
            
        elif self.ui_state == UIState.HISTORY_LOG:
            print("Returning from history log to main game")
            self.ui_state = UIState.MAIN_GAME
            return True
            
        return False

    def _end_turn(self):
        """End the current turn and process AI actions."""
        if not self.game_state:
            return
            
        # Process end of turn in game state
        self.game_state.end_turn()
        
        # First check if the game is over
        if self.game_state.game_over:
            self._handle_game_over()
            return
        
        # Display AI turn overlay after processing
        if self.game_state.ai_last_turn_actions:
            self.show_ai_turn = True
            self.ui_state = UIState.AI_TURN
        
        # Update action points display
        if self.game_state.next_turn_extra_ap > 0:
            self.game_state.action_points += self.game_state.next_turn_extra_ap
            self.game_state.next_turn_extra_ap = 0
        
        # Update available actions for the new turn
        self._update_available_actions()
        
        # Add turn transition message to dialogue
        self._add_dialogue_message("SYSTEM", f"Turn {self.game_state.turn} begins. You have {self.game_state.action_points} action points.")
        
        print(f"Turn ended. Now turn {self.game_state.turn} with {self.game_state.action_points} AP.")

    def _handle_input(self):
        """Process keyboard and controller input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Handle keyboard input
            elif event.type == pygame.KEYDOWN:
                current_time = pygame.time.get_ticks()
                
                # Handle H key for history log
                if event.key == pygame.K_h and self.ui_state == UIState.MAIN_GAME:
                    print("Showing history log")
                    self.ui_state = UIState.HISTORY_LOG
                    self.history_page = 0  # Reset to first page
                    return True
                
                # Handle ESC key
                elif event.key == pygame.K_ESCAPE:
                    if not self._handle_back_button():
                        return False
                
                # Process other keyboard input if cooldown has elapsed
                elif current_time - self.last_input_time > self.input_cooldown:
                    if self.ui_state == UIState.SIDE_SELECT:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.selected_index = max(0, self.selected_index - 1)
                            self.last_input_time = current_time
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected_index = min(len(self.sides) - 1, self.selected_index + 1)
                            self.last_input_time = current_time
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.selected_side = self.sides[self.selected_index]
                            self.ui_state = UIState.FACTION_SELECT
                            self.selected_index = 0
                            self.last_input_time = current_time
                    
                    elif self.ui_state == UIState.FACTION_SELECT:
                        factions = self.faction_groups[self.selected_side]
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.selected_index = max(0, self.selected_index - 1)
                            self.last_input_time = current_time
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected_index = min(len(factions) - 1, self.selected_index + 1)
                            self.last_input_time = current_time
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self._select_faction(factions[self.selected_index])
                            self.last_input_time = current_time
                    
                    elif self.ui_state == UIState.HISTORY_LOG:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.history_page = max(0, self.history_page - 1)
                            self.last_input_time = current_time
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            total_pages = max(1, (len(self.game_state.game_history) + 
                                                self.history_entries_per_page - 1) // 
                                                self.history_entries_per_page)
                            self.history_page = min(total_pages - 1, self.history_page + 1)
                            self.last_input_time = current_time
                    
                    # For other UI states, add appropriate input handling here
        
        return True
        
    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            # Process input and check if we should continue
            if not self._handle_input():
                running = False
                
            # Update game state if needed
            
            # Draw everything
            self.draw()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up and exit
        pygame.quit()

def main():
    """Entry point for the tactical UI."""
    ui = TacticalUI()
    ui.run()

if __name__ == "__main__":
    main() 