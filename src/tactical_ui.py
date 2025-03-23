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
        self.game_state = None
        
        # Side and faction options
        self.sides = ["Negotiator", "Hostage Taker"]
        self.faction_descriptions = {
            Faction.FBI: "Elite tactical unit with jurisdiction autonomy, special agents including mentalists, psychological profilers, and bomb experts.",
            Faction.CIA: "Advanced intelligence division with high-tech capabilities, able to hack cameras, control infrastructure, and deploy drones.",
            Faction.LOCAL_PD: "Experienced local force with intimate knowledge of terrain, building layouts, and community connections.",
            Faction.CHILDREN_OF_THE_VEIL: "Mysterious religious cult with strong influence over local rural communities and devoted followers.",
            Faction.ZERO_SIGNAL: "Decentralized dark web hacker collective specializing in cyber warfare and digital disruption.",
            Faction.ECLIPSE_ORDER: "Well-funded terrorist organization with significant financial resources and political influence."
        }
        self.faction_groups = {
            "Negotiator": [
                Faction.FBI,
                Faction.CIA,
                Faction.LOCAL_PD
            ],
            "Hostage Taker": [
                Faction.CHILDREN_OF_THE_VEIL,
                Faction.ZERO_SIGNAL,
                Faction.ECLIPSE_ORDER
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
        """Draw the dialogue panel."""
        if not self.game_state:
            return
            
        rect = pygame.Rect(20, TOP_HUD_HEIGHT + 240,
                          SIDE_PANEL_WIDTH,
                          WINDOW_HEIGHT - TOP_HUD_HEIGHT - BOTTOM_HUD_HEIGHT - 260)
        self._draw_panel(rect, "COMMS")
        
        # Get the last 8 dialogue entries (most recent)
        latest_messages = self.game_state.dialogue_history[-8:]
        
        # Start drawing from the top of the panel, with newest messages at the top
        y = rect.top + 50  # Start at the top, leaving some padding
        max_width = rect.width - 50  # Account for padding
        
        # Process messages in reverse so newest is at top
        for entry in reversed(latest_messages):
            # Speaker
            color = COLORS['success'] if entry.get('success', True) else COLORS['failure']
            speaker = self.hud_font.render(f"{entry['speaker']}:", True, color)
            self.screen.blit(speaker, (rect.left + 20, y))
            y += 25
            
            # Message with word wrapping
            words = entry['text'].split(' ')
            message_lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                test_surface = self.dialog_font.render(test_line, True, COLORS['text'])
                
                if test_surface.get_width() <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        message_lines.append(current_line)
                    current_line = word
            
            if current_line:
                message_lines.append(current_line)
            
            # Draw each line
            for line in message_lines:
                text_surf = self.dialog_font.render(line, True, COLORS['text'])
                self.screen.blit(text_surf, (rect.left + 30, y))
                y += 20
            
            y += 15  # Add space between dialogue entries
            
            # Check if we've gone beyond the bottom of the panel
            if y > rect.bottom - 20:
                break
    
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
        return []
    
    def draw(self):
        """Draw the current game state."""
        # Clear screen
        self.screen.fill(COLORS['background'])
        
        # Draw main game interface if active
        if self.game_state:
            self._draw_top_hud()
            self._draw_objectives_panel()
            self._draw_dialogue_panel()
            self._draw_tactical_panel()
            self._draw_history_panel()
            self._draw_bottom_hud()
        
        # Draw current UI state
        if self.ui_state == UIState.SIDE_SELECT:
            self._draw_side_selection()
        elif self.ui_state == UIState.FACTION_SELECT:
            self._draw_faction_selection()
        elif self.ui_state == UIState.ACTION_MENU:
            # No need to call draw again, just draw the action menu on top
            self._draw_action_menu()
        elif self.ui_state == UIState.EXIT_CONFIRM:
            # No need to call draw again, just draw the exit confirm on top
            self._draw_exit_confirm()
        
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
                rect = pygame.Rect(WINDOW_WIDTH//2 - 400, y - 10, 800, 80)
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
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        try:
            # Store current display flags
            current_flags = self.screen.get_flags()
            
            if not self.is_fullscreen:
                # Switch to fullscreen
                pygame.display.quit()
                pygame.display.init()
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
                self.is_fullscreen = True
            else:
                # Return to windowed mode
                pygame.display.quit()
                pygame.display.init()
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
                self.is_fullscreen = False
            
            # Reinitialize fonts after display mode change
            self._init_fonts()
            
            # Force a complete redraw
            self.draw()
            pygame.display.flip()
            
        except Exception as e:
            print(f"Error toggling fullscreen: {e}")
            # Fallback to windowed mode if something goes wrong
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.is_fullscreen = False
            self._init_fonts()
            self.draw()
            pygame.display.flip()
    
    def handle_resize(self, event):
        """Handle window resize events."""
        if not self.is_fullscreen:
            self.windowed_size = event.size
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
    
    def _handle_input(self, event):
        """Process a single input event."""
        if event.type == pygame.QUIT:
            self.running = False
            
        elif event.type == pygame.KEYDOWN:
            # Check for escape key
            if event.key == pygame.K_ESCAPE:
                if self.ui_state == UIState.MAIN_GAME:
                    # Open exit confirmation
                    self.ui_state = UIState.EXIT_CONFIRM
                    self.selected_index = 0  # Default to 'No'
                elif self.ui_state == UIState.ACTION_MENU:
                    # Return to main game
                    self.ui_state = UIState.MAIN_GAME
                    # Reset action selection
                    self.selected_action_index = -1
                elif self.ui_state == UIState.EXIT_CONFIRM:
                    # Cancel exit confirmation
                    self.ui_state = UIState.MAIN_GAME
                elif self.ui_state == UIState.FACTION_SELECT:
                    # Return to side selection
                    self.ui_state = UIState.SIDE_SELECT
                    
            # Check for category navigation keys (Q/E)
            elif event.key == pygame.K_q:
                if self.ui_state == UIState.MAIN_GAME or self.ui_state == UIState.ACTION_MENU:
                    # In action menu or main game, Q rotates categories left
                    num_categories = len(ActionCategory)
                    self.current_category_index = (self.current_category_index - 1) % num_categories
                    # Reset action selection when changing category
                    self.selected_action_index = -1
                    
                    # Debug prints
                    current_category = list(ActionCategory)[self.current_category_index]
                    actions = self.available_actions.get(current_category, [])
                    print(f"Category changed to: {current_category.value}, {len(actions)} actions available")
                
                elif self.ui_state not in [UIState.SIDE_SELECT, UIState.FACTION_SELECT]:
                    # Q for quit in other states
                    self.ui_state = UIState.EXIT_CONFIRM
                    self.selected_index = 0  # Default to 'No'
            
            # E key for rotating categories right
            elif event.key == pygame.K_e:
                if self.ui_state == UIState.MAIN_GAME or self.ui_state == UIState.ACTION_MENU:
                    num_categories = len(ActionCategory)
                    self.current_category_index = (self.current_category_index + 1) % num_categories
                    # Reset action selection when changing category
                    self.selected_action_index = -1
                    
                    # Debug prints
                    current_category = list(ActionCategory)[self.current_category_index]
                    actions = self.available_actions.get(current_category, [])
                    print(f"Category changed to: {current_category.value}, {len(actions)} actions available")
            
            # Handle directional input
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self._handle_direction(InputDirection.UP)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self._handle_direction(InputDirection.DOWN)
            elif event.key in [pygame.K_LEFT, pygame.K_a]:
                self._handle_direction(InputDirection.LEFT)
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                self._handle_direction(InputDirection.RIGHT)
            
            # Handle numeric keys for action selection (optional shortcut)
            elif self.ui_state == UIState.ACTION_MENU and event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                index = event.key - pygame.K_1  # Convert key to index (0-3)
                self.selected_action_index = index  # Just highlight the option
                # Don't execute immediately, let user confirm with enter
            
            # Handle confirmation (ENTER or SPACE)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._handle_confirm()
                
            # Handle yes/no in exit confirmation
            elif self.ui_state == UIState.EXIT_CONFIRM:
                if event.key == pygame.K_y:
                    self.running = False  # Exit on Y
                elif event.key == pygame.K_n:
                    self.ui_state = UIState.MAIN_GAME  # Return to game on N

    def _handle_direction(self, direction):
        """Handle a directional input based on the current UI state."""
        # Get current time for D-pad cooldown
        current_time = pygame.time.get_ticks()
        
        # Check if we're within the D-pad cooldown period or repeating the same direction
        if current_time - self.last_dpad_input_time <= self.dpad_cooldown:
            return False
            
        # Update the D-pad input time
        self.last_dpad_input_time = current_time
        
        # Store last direction to help prevent rapid repeats
        old_direction = self.last_direction
        self.last_direction = direction
        
        # Side selection state
        if self.ui_state == UIState.SIDE_SELECT:
            if direction == InputDirection.UP:
                self.selected_index = (self.selected_index - 1) % len(self.sides)
            elif direction == InputDirection.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.sides)
                
        # Faction selection state
        elif self.ui_state == UIState.FACTION_SELECT:
            factions = self.faction_groups[self.selected_side]
            
            if direction == InputDirection.UP:
                self.selected_index = (self.selected_index - 1) % len(factions)
            elif direction == InputDirection.DOWN:
                self.selected_index = (self.selected_index + 1) % len(factions)
                
        # Main game state
        elif self.ui_state == UIState.MAIN_GAME:
            # Left/Right (A/D) used to change category
            if direction in [InputDirection.LEFT, InputDirection.RIGHT]:
                num_categories = len(ActionCategory)
                delta = 1 if direction == InputDirection.RIGHT else -1
                self.current_category_index = (self.current_category_index + delta) % num_categories
                
                # Debug prints
                current_category = list(ActionCategory)[self.current_category_index]
                actions = self.available_actions.get(current_category, [])
                print(f"Category changed to: {current_category.value}, {len(actions)} actions available")
                
            # Any vertical movement opens the action menu
            elif direction in [InputDirection.UP, InputDirection.DOWN]:
                self.ui_state = UIState.ACTION_MENU
                # Initialize selected action to -1 (no selection)
                self.selected_action_index = -1
                
        # Action menu state
        elif self.ui_state == UIState.ACTION_MENU:
            # Direction keys highlight the corresponding action
            if direction in [InputDirection.UP, InputDirection.DOWN, InputDirection.LEFT, InputDirection.RIGHT]:
                # Map directions to action indices (up=0, right=1, down=2, left=3)
                direction_index_map = {
                    InputDirection.UP: 0,
                    InputDirection.RIGHT: 1,
                    InputDirection.DOWN: 2,
                    InputDirection.LEFT: 3
                }
                
                new_index = direction_index_map[direction]
                
                # Get current category and ensure we have actions before setting
                current_category = list(ActionCategory)[self.current_category_index]
                actions = self.available_actions.get(current_category, [])
                
                # Only set if the index is valid (within the available actions)
                if new_index < len(actions):
                    self.selected_action_index = new_index
                    
                    # Debug print the selected action
                    action = actions[self.selected_action_index]
                    print(f"Selected action: {action.name} ({action.action_points} AP)")

        # Exit confirmation state
        elif self.ui_state == UIState.EXIT_CONFIRM:
            if direction == InputDirection.LEFT:
                self.selected_index = 0  # No (don't exit)
            elif direction == InputDirection.RIGHT:
                self.selected_index = 1  # Yes (exit)
        
        return True

    def _handle_confirm(self):
        """Handle confirmation button press."""
        if self.ui_state == UIState.SIDE_SELECT:
            self.selected_side = self.sides[self.selected_index]
            self.ui_state = UIState.FACTION_SELECT
            self.selected_index = 0
            return True

        elif self.ui_state == UIState.FACTION_SELECT:
            # Get the correct faction from the faction group for the selected side
            selected_faction = self.faction_groups[self.selected_side][self.selected_index]
            self.game_state = GameState(selected_faction)
            
            # Initialize available actions for the selected faction
            self._update_available_actions()
            
            # Debug printout of available actions
            print(f"Available actions for {selected_faction.value}:")
            for category in ActionCategory:
                actions = self.available_actions.get(category, [])
                print(f"  {category.value}: {len(actions)} actions")
                for action in actions:
                    print(f"    - {action.name} ({action.action_points} AP)")
            
            self.ui_state = UIState.MAIN_GAME
            return True
            
        # Action menu - execute the highlighted action if one is selected
        elif self.ui_state == UIState.ACTION_MENU and hasattr(self, 'selected_action_index'):
            if self.selected_action_index >= 0:
                current_category = list(ActionCategory)[self.current_category_index]
                actions = self.available_actions.get(current_category, [])
                
                if 0 <= self.selected_action_index < len(actions):
                    action = actions[self.selected_action_index]
                    self._execute_action(action)
                    return True
            
            # If no action is selected, do nothing on confirm
            return False

        elif self.ui_state == UIState.EXIT_CONFIRM:
            # Handle confirmation in exit screen
            if self.selected_index == 1:
                self.running = False  # Exit the game if "Yes" selected
            else:
                self.ui_state = UIState.MAIN_GAME  # Return to game if "No" selected
            return True
            
        return True

    def _execute_action(self, action):
        """Execute an action and update game state."""
        if not self.game_state:
            print("No game state to execute action on!")
            return
            
        # Check if we have enough action points
        if action.action_points > self.game_state.action_points:
            print(f"Not enough action points! Need {action.action_points}, have {self.game_state.action_points}")
            return
            
        # Execute the action (simulate success/failure)
        success = random.random() < action.success_chance
        
        # Apply effects based on success
        effects = []
        if success:
            for effect in action.effects:
                effects.append(effect.value)
                # Apply each effect (could be more detailed in a real implementation)
                if effect.value == "TRUST_INCREASE":
                    self.game_state.trust_level = min(1.0, self.game_state.trust_level + 0.1)
                elif effect.value == "TENSION_DECREASE":
                    self.game_state.tension_level = max(0.0, self.game_state.tension_level - 0.1)
                elif effect.value == "TACTICAL_ADVANTAGE":
                    # This would do something specific in the real game
                    pass
        
        # Update game state
        self.game_state.action_points -= action.action_points
        
        # Add to game history
        self.game_state.game_history.append({
            "turn": self.game_state.turn,
            "action": action.name,
            "success": success,
            "effects": effects
        })
        
        # Add dialogue if applicable
        if hasattr(action, 'dialogue_text') and action.dialogue_text:
            dialogue_text = action.dialogue_text
        else:
            # Create default dialogue message if none exists
            dialogue_text = f"Executing: {action.name}"
            
        # Add the dialogue message
        self._add_dialogue_message(self.game_state.player_faction.value, dialogue_text, success)
        
        # Print debug info
        print(f"Action executed: {action.name} - Success: {success}")
        print(f"  Effects: {effects}")
        print(f"  Remaining AP: {self.game_state.action_points}")
            
        # Update the UI state
        self.ui_state = UIState.MAIN_GAME
        
        # Check if we've used all action points and need to end the turn
        if self.game_state.action_points <= 0:
            self._end_turn()

    def _add_dialogue_message(self, speaker, text, success=True):
        """Add a message to the dialogue history."""
        if not self.game_state:
            return
            
        message = {
            "turn": self.game_state.turn,
            "speaker": speaker,
            "text": text,
            "success": success,
            "timestamp": pygame.time.get_ticks()  # Add timestamp for sorting
        }
        
        # Add to dialogue history
        self.game_state.dialogue_history.append(message)
        
        # Debug print
        print(f"COMMS: {speaker}: {text}")
        
    def _end_turn(self):
        """End the current turn and move to the next one."""
        if not self.game_state:
            return
            
        # Increment turn counter
        self.game_state.turn += 1
        
        # Reset action points
        self.game_state.action_points = 3  # Standard AP
        
        # Apply any extra AP gained during the previous turn
        if hasattr(self.game_state, 'next_turn_extra_ap') and self.game_state.next_turn_extra_ap > 0:
            self.game_state.action_points += self.game_state.next_turn_extra_ap
            self.game_state.next_turn_extra_ap = 0
        
        # Update available actions for the new turn
        self._update_available_actions()
        
        # Add turn transition message to dialogue
        self._add_dialogue_message("SYSTEM", f"Turn {self.game_state.turn} begins. You have {self.game_state.action_points} action points.")
        
        print(f"Turn ended. Now turn {self.game_state.turn} with {self.game_state.action_points} AP.")

    def _update_available_actions(self):
        """Update the available actions based on the current game state."""
        if not self.game_state or not self.action_system:
            return
            
        # Reset available actions
        self.available_actions = {}
        
        # Initialize all categories
        for category in ActionCategory:
            self.available_actions[category] = []
            
        # Get actions from action system for the player's faction
        faction_actions = self.action_system.get_available_actions(self.game_state)
        
        # Add actions to their respective categories
        for category in ActionCategory:
            if category in faction_actions:
                self.available_actions[category] = faction_actions[category]
                
        # Debug print the available actions
        print("\nUpdated available actions:")
        for category, actions in self.available_actions.items():
            print(f"Category {category.value}: {len(actions)} actions available")
            for action in actions:
                print(f"  - {action.name} ({action.action_points} AP)")
                
        # Reset category index if needed
        if self.current_category_index >= len(ActionCategory):
            self.current_category_index = 0
            
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
            
        return False

    def _handle_controller_events(self, events):
        """Handle controller input events."""
        # Initialize controllers if available
        has_controllers = self._setup_controllers()
        if not has_controllers:
            return False
            
        # Track if any controller input was handled
        handled = False
        
        # Get current time for handling input cooldown
        current_time = pygame.time.get_ticks()
        
        # Process events
        for event in events:
            # Handle controller button presses
            if event.type == pygame.JOYBUTTONDOWN:
                # Print button info for debugging
                button_id = event.button
                print(f"Button pressed: {button_id}")
                
                # Check if this button is in cooldown
                if current_time - self.last_button_press.get(button_id, 0) <= self.button_cooldown:
                    print(f"Button {button_id} in cooldown, ignoring...")
                    continue
                
                # Update the last press time for this button
                self.last_button_press[button_id] = current_time
                
                # D-pad as button detection for Xbox Elite 2 Controller
                # Button mapping may vary by controller and platform
                if button_id == 11:  # D-pad UP
                    print("D-pad UP button pressed")
                    if self._handle_direction(InputDirection.UP):
                        handled = True
                        return handled
                elif button_id == 12:  # D-pad DOWN
                    print("D-pad DOWN button pressed")
                    if self._handle_direction(InputDirection.DOWN):
                        handled = True
                        return handled
                elif button_id == 13:  # D-pad LEFT
                    print("D-pad LEFT button pressed")
                    if self._handle_direction(InputDirection.LEFT):
                        handled = True
                        return handled
                elif button_id == 14:  # D-pad RIGHT
                    print("D-pad RIGHT button pressed")
                    if self._handle_direction(InputDirection.RIGHT):
                        handled = True
                        return handled
                
                # A button (typically button 0) for confirmation
                if button_id == 0:  # A button (confirm)
                    print("A button pressed - confirming selection")
                    self._handle_confirm()
                    handled = True
                    
                # B button (typically button 1) for back/cancel
                elif button_id == 1:  # B button (back)
                    print("B button pressed - going back")
                    handled = self._handle_back_button()
                
                # X/Y buttons (typically 2/3) for category selection
                elif button_id == 2:  # X button - previous category
                    print("X button pressed - previous category")
                    if self.ui_state in [UIState.MAIN_GAME, UIState.ACTION_MENU]:
                        num_categories = len(ActionCategory)
                        self.current_category_index = (self.current_category_index - 1) % num_categories
                        # Reset action selection when changing category
                        self.selected_action_index = -1
                        
                        # Debug prints
                        current_category = list(ActionCategory)[self.current_category_index]
                        actions = self.available_actions.get(current_category, [])
                        print(f"X button - Category changed to: {current_category.value}, {len(actions)} actions available")
                    handled = True
                    
                elif button_id == 3:  # Y button - next category
                    print("Y button pressed - next category")
                    if self.ui_state in [UIState.MAIN_GAME, UIState.ACTION_MENU]:
                        num_categories = len(ActionCategory)
                        self.current_category_index = (self.current_category_index + 1) % num_categories
                        # Reset action selection when changing category
                        self.selected_action_index = -1
                        
                        # Debug prints
                        current_category = list(ActionCategory)[self.current_category_index]
                        actions = self.available_actions.get(current_category, [])
                        print(f"Y button - Category changed to: {current_category.value}, {len(actions)} actions available")
                    handled = True
                
                # Shoulder buttons (LB/RB - 4/5) for category navigation
                elif button_id == 4:  # LB - previous category
                    print("LB button pressed - previous category")
                    if self.ui_state in [UIState.MAIN_GAME, UIState.ACTION_MENU]:
                        num_categories = len(ActionCategory)
                        self.current_category_index = (self.current_category_index - 1) % num_categories
                        # Reset action selection when changing category
                        self.selected_action_index = -1
                        
                        # Debug prints
                        current_category = list(ActionCategory)[self.current_category_index]
                        actions = self.available_actions.get(current_category, [])
                        print(f"LB - Category changed to: {current_category.value}, {len(actions)} actions available")
                    handled = True
                
                elif button_id == 5:  # RB - next category
                    print("RB button pressed - next category")
                    if self.ui_state in [UIState.MAIN_GAME, UIState.ACTION_MENU]:
                        num_categories = len(ActionCategory)
                        self.current_category_index = (self.current_category_index + 1) % num_categories
                        # Reset action selection when changing category
                        self.selected_action_index = -1
                        
                        # Debug prints
                        current_category = list(ActionCategory)[self.current_category_index]
                        actions = self.available_actions.get(current_category, [])
                        print(f"RB - Category changed to: {current_category.value}, {len(actions)} actions available")
                    handled = True
                
                # Start button (typically button 7) for exit
                elif button_id == 7:  # Start button (exit)
                    print("Start button pressed - exit menu")
                    if self.ui_state not in [UIState.SIDE_SELECT, UIState.FACTION_SELECT, UIState.EXIT_CONFIRM]:
                        self.ui_state = UIState.EXIT_CONFIRM
                        self.selected_index = 0  # Default to 'No'
                    handled = True
            
            # Handle D-pad input (hat motion) with high priority
            elif event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                print(f"Hat motion detected: {hat_x}, {hat_y}")
                
                if hat_x != 0 or hat_y != 0:
                    # Convert hat values to InputDirection
                    direction_handled = False
                    
                    if hat_y > 0:
                        print("D-pad UP from hat motion")
                        direction_handled = self._handle_direction(InputDirection.UP)
                    elif hat_y < 0:
                        print("D-pad DOWN from hat motion")
                        direction_handled = self._handle_direction(InputDirection.DOWN)
                    elif hat_x > 0:
                        print("D-pad RIGHT from hat motion")
                        direction_handled = self._handle_direction(InputDirection.RIGHT)
                    elif hat_x < 0:
                        print("D-pad LEFT from hat motion")
                        direction_handled = self._handle_direction(InputDirection.LEFT)
                    
                    if direction_handled:
                        handled = True
                        return handled
                    
            # Handle analog stick input
            elif event.type == pygame.JOYAXISMOTION:
                # Left analog stick (typically axes 0 and 1)
                if event.axis in [0, 1]:
                    # Only process if outside cooldown period
                    if current_time - self.last_input_time > self.input_cooldown:
                        # Check if axis value exceeds deadzone
                        if abs(event.value) > self.stick_deadzone:
                            direction_handled = False
                            
                            if event.axis == 0:  # Horizontal axis
                                if event.value > self.stick_deadzone:
                                    print("Stick RIGHT detected")
                                    direction_handled = self._handle_direction(InputDirection.RIGHT)
                                elif event.value < -self.stick_deadzone:
                                    print("Stick LEFT detected")
                                    direction_handled = self._handle_direction(InputDirection.LEFT)
                            elif event.axis == 1:  # Vertical axis
                                if event.value > self.stick_deadzone:
                                    print("Stick DOWN detected")
                                    direction_handled = self._handle_direction(InputDirection.DOWN)
                                elif event.value < -self.stick_deadzone:
                                    print("Stick UP detected")
                                    direction_handled = self._handle_direction(InputDirection.UP)
                            
                            if direction_handled:
                                self.last_input_time = current_time
                                handled = True
                                return handled
                
                # Right analog stick for category navigation (axes 2 and 3 typically)
                elif event.axis in [2, 3] and self.ui_state in [UIState.MAIN_GAME, UIState.ACTION_MENU]:
                    # Only process if outside cooldown period
                    if current_time - self.last_input_time > self.input_cooldown:
                        # Only use horizontal movement for category navigation
                        if event.axis == 2:  # Horizontal axis of right stick
                            if abs(event.value) > self.stick_deadzone:
                                num_categories = len(ActionCategory)
                                if event.value > self.stick_deadzone:
                                    # Right - next category
                                    self.current_category_index = (self.current_category_index + 1) % num_categories
                                    # Reset action selection when changing category
                                    self.selected_action_index = -1
                                    print("Right Stick RIGHT - Next Category")
                                elif event.value < -self.stick_deadzone:
                                    # Left - previous category
                                    self.current_category_index = (self.current_category_index - 1) % num_categories
                                    # Reset action selection when changing category
                                    self.selected_action_index = -1
                                    print("Right Stick LEFT - Previous Category")
                                
                                # Debug prints
                                current_category = list(ActionCategory)[self.current_category_index]
                                actions = self.available_actions.get(current_category, [])
                                print(f"Category changed to: {current_category.value}, {len(actions)} actions available")
                                
                                self.last_input_time = current_time
                                handled = True

        return handled

    def _poll_controllers(self):
        """Actively poll controller inputs including D-pad regardless of events."""
        if not self.controllers:
            return False
            
        # Get current time
        current_time = pygame.time.get_ticks()
        
        # Only poll if outside cooldown period
        if current_time - self.last_dpad_input_time <= self.dpad_cooldown:
            return False
            
        # Track if any input was handled
        handled = False
            
        # For Xbox Elite and similar controllers where D-pad is buttons
        # First check for button presses that might be D-pad
        for joystick in self.controllers:
            # Check D-pad as buttons - specifically for Xbox Elite 2 controller
            if joystick.get_numbuttons() >= 15:  # Make sure it has enough buttons
                # Check specific D-pad buttons (for Xbox Elite 2)
                if joystick.get_button(11):  # UP
                    print("Polling detected D-pad UP")
                    if self._handle_direction(InputDirection.UP):
                        self.last_dpad_input_time = current_time
                        return True
                elif joystick.get_button(12):  # DOWN
                    print("Polling detected D-pad DOWN")
                    if self._handle_direction(InputDirection.DOWN):
                        self.last_dpad_input_time = current_time
                        return True
                elif joystick.get_button(13):  # LEFT
                    print("Polling detected D-pad LEFT")
                    if self._handle_direction(InputDirection.LEFT):
                        self.last_dpad_input_time = current_time
                        return True
                elif joystick.get_button(14):  # RIGHT
                    print("Polling detected D-pad RIGHT")
                    if self._handle_direction(InputDirection.RIGHT):
                        self.last_dpad_input_time = current_time
                        return True
            
            # Check hat-based D-pads (traditional controllers)
            if joystick.get_numhats() > 0:
                for hat_idx in range(joystick.get_numhats()):
                    hat_x, hat_y = joystick.get_hat(hat_idx)
                    
                    if hat_x != 0 or hat_y != 0:
                        # Convert hat values to InputDirection
                        if hat_y > 0:
                            print("Polling detected D-pad UP via hat")
                            if self._handle_direction(InputDirection.UP):
                                self.last_dpad_input_time = current_time
                                return True
                        elif hat_y < 0:
                            print("Polling detected D-pad DOWN via hat")
                            if self._handle_direction(InputDirection.DOWN):
                                self.last_dpad_input_time = current_time
                                return True
                        elif hat_x > 0:
                            print("Polling detected D-pad RIGHT via hat")
                            if self._handle_direction(InputDirection.RIGHT):
                                self.last_dpad_input_time = current_time
                                return True
                        elif hat_x < 0:
                            print("Polling detected D-pad LEFT via hat")
                            if self._handle_direction(InputDirection.LEFT):
                                self.last_dpad_input_time = current_time
                                return True
                    
        # If we get here, no D-pad input was detected
        return False

    def run(self):
        """Run the main game loop."""
        self.running = True
        
        while self.running:
            events = pygame.event.get()
            
            # Check for quit event
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break
            
            # First actively poll D-pad inputs directly regardless of events
            dpad_handled = self._poll_controllers()
            
            # Handle controller events next (if D-pad polling didn't handle anything)
            controller_handled = dpad_handled or self._handle_controller_events(events)
            
            # Handle keyboard events if controller didn't handle anything
            if not controller_handled:
                for event in events:
                    self._handle_input(event)
            
            # Update game state
            # (in the future, this would include animations, timers, etc.)
            
            # Draw everything
            self.draw()
            
            # Cap framerate
            self.clock.tick(60)
        
        pygame.quit()

    def _draw_exit_confirm(self):
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

def main():
    """Entry point for the tactical UI."""
    ui = TacticalUI()
    ui.run()

if __name__ == "__main__":
    main() 