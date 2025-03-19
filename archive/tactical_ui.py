import pygame
import pygame.gfxdraw
import sys
import math
from typing import Dict, List, Optional, Tuple
from enum import Enum
from core.dialogue_system import Faction, ActionCategory, GameAction, ActionSystem, DialogueSystem, GameState
from input_handler import InputHandler

# Constants
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 60

# Layout
SIDE_PANEL_WIDTH = 500
TOP_HUD_HEIGHT = 80
BOTTOM_HUD_HEIGHT = 100
DIALOG_HEIGHT = 400
ACTION_MENU_Y = WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT - 300

# Colors - Military/Tech Theme
COLORS = {
    'background': (10, 15, 25),  # Dark blue-black
    'panel_bg': (20, 30, 40, 220),  # Dark blue-grey, semi-transparent
    'panel_border': (0, 255, 170),  # Bright cyan-green
    'text': (0, 255, 170),  # Bright cyan-green
    'text_dim': (0, 155, 100),  # Dimmer cyan-green
    'highlight': (255, 255, 255),  # White
    'selector': (0, 255, 170, 30),  # Semi-transparent cyan-green
    'warning': (255, 200, 0),  # Bright yellow
    'critical': (255, 60, 60),  # Bright red
    'success': (0, 255, 100),  # Bright green
    'failure': (255, 60, 60),  # Bright red
    'inactive': (40, 45, 55),  # Dark blue-grey
    'meter_bg': (15, 20, 30),  # Slightly lighter than background
    'trust': (0, 255, 100),  # Bright green
    'tension': (255, 60, 0),  # Bright orange-red
    'intel': (0, 150, 255),  # Bright blue
    'ap': (255, 200, 0),  # Gold
    'grid': (0, 255, 170, 15),  # Very transparent cyan-green
    'border': (0, 255, 170),  # Bright cyan-green
    'grid_highlight': (0, 255, 170, 30),  # Semi-transparent cyan-green
}

# UI Elements
UI_ELEMENTS = {
    'panel_border_radius': 8,
    'meter_height': 16,
    'grid_size': 40,
    'border_width': 2,
    'glow_radius': 20,
    'panel_spacing': 20,  # Space between panels
    'text_padding': 15,   # Padding inside panels
    'menu_item_height': 40  # Height of menu items
}

# Resource symbols
RESOURCE_SYMBOLS = {
    'personnel': '👥',
    'equipment': '🔧',
    'intel': '📡',
    'medical': '🏥'
}

class UIState(Enum):
    FACTION_SELECT = 1
    MAIN_GAME = 2
    ACTION_MENU = 3
    SPECIAL_MENU = 4

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
        self.ui_state = UIState.FACTION_SELECT
        self.selected_index = 0
        self.current_category_index = 0
        self.game_state = None
        
        # Initialize input handler
        self.input_handler = InputHandler()
        
        # Initialize controller support
        self.controllers = []
        self._setup_controllers()
        
        # Action categories
        self.categories = list(ActionCategory)
        self.available_actions = {}
        
        # Input settings
        self.input_cooldown = 150  # ms
        self.last_input_time = 0
        self.stick_deadzone = 0.2
    
    def _init_fonts(self):
        """Initialize fonts for different UI elements."""
        self.title_font = pygame.font.Font(None, 48)
        self.menu_font = pygame.font.Font(None, 32)
        self.hud_font = pygame.font.Font(None, 24)
        self.dialog_font = pygame.font.Font(None, 18)
    
    def _setup_controllers(self):
        """Initialize game controllers."""
        self.controllers = [pygame.joystick.Joystick(i) 
                          for i in range(pygame.joystick.get_count())]
        for controller in self.controllers:
            controller.init()
    
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
    
    def _get_scaled_pos(self, pos):
        """Convert a position from base resolution to current window size."""
        x = pos[0] * (self.screen.get_width() / WINDOW_WIDTH)
        y = pos[1] * (self.screen.get_height() / WINDOW_HEIGHT)
        return (int(x), int(y))
    
    def _draw_top_hud(self):
        """Draw the top HUD with game information."""
        if not self.game_state:
            return
        
        # Draw resource info in top right
        resources = [
            f"AP: {self.game_state.action_points}",
            f"Trust: {int(self.game_state.trust_level * 100)}%",
            f"Tension: {int(self.game_state.tension_level * 100)}%",
            f"Turn: {self.game_state.turn}"
        ]
        
        x_offset = WINDOW_WIDTH - 20
        y_offset = 20
        spacing = 120  # Increased spacing between resources
        
        for resource in reversed(resources):
            text_surf = self.hud_font.render(resource, True, COLORS['text'])
            text_rect = text_surf.get_rect(topright=self._get_scaled_pos((x_offset, y_offset)))
            self.screen.blit(text_surf, text_rect)
            x_offset -= spacing  # Move left by spacing amount
    
    def _draw_objectives_panel(self):
        """Draw the objectives panel."""
        if not self.game_state:
            return
            
        # Draw panel background - wider panel
        panel_rect = pygame.Rect(10, 60, 400, 250)  # Increased width and height
        pygame.draw.rect(self.screen, COLORS['panel_bg'], panel_rect)
        pygame.draw.rect(self.screen, COLORS['panel_border'], panel_rect, 2)
        
        # Draw title
        title = self.menu_font.render("OBJECTIVES", True, COLORS['text'])  # Larger font
        title_rect = title.get_rect(topleft=self._get_scaled_pos((20, 70)))
        self.screen.blit(title, title_rect)
        
        # Draw objectives
        y = 110  # Start lower to account for larger title
        for objective in self.game_state.get_objectives():
            status = "✓" if objective['complete'] else "✗" if objective['failed'] else "○"
            text = f"{status} {objective['text']}"
            color = COLORS['success'] if objective['complete'] else COLORS['failure'] if objective['failed'] else COLORS['text']
            
            text_surf = self.menu_font.render(text, True, color)  # Larger font
            text_rect = text_surf.get_rect(topleft=self._get_scaled_pos((25, y)))
            self.screen.blit(text_surf, text_rect)
            y += 35  # Increased spacing between objectives
    
    def _draw_dialogue_panel(self):
        """Draw the dialogue panel."""
        if not self.game_state:
            return
            
        rect = pygame.Rect(20, TOP_HUD_HEIGHT + 240,
                          SIDE_PANEL_WIDTH,
                          WINDOW_HEIGHT - TOP_HUD_HEIGHT - BOTTOM_HUD_HEIGHT - 260)
        self._draw_panel(rect, "COMMS")
        
        y = rect.top + 50
        for entry in self.game_state.dialogue_history[-8:]:
            # Speaker
            color = COLORS['success'] if entry.get('success', True) else COLORS['failure']
            speaker = self.hud_font.render(f"{entry['speaker']}:", True, color)
            self.screen.blit(speaker, (rect.left + 20, y))
            
            # Message
            text = self.dialog_font.render(entry['text'], True, COLORS['text'])
            self.screen.blit(text, (rect.left + 30, y + 25))
            y += 50
    
    def _draw_tactical_panel(self):
        """Draw the tactical information panel."""
        if not self.game_state:
            return
        
        # Wider panel for tactical info
        base_rect = pygame.Rect(20, 240, 400, 200)  # Increased width
        rect = self._get_scaled_rect(base_rect)
        self._draw_panel(rect, "Tactical Info")
        
        # Draw tactical information
        y_offset = rect.top + 40
        for info in self.game_state.tactical_info:
            text_surf = self.dialog_font.render(info, True, COLORS['text'])
            text_rect = text_surf.get_rect(topleft=(rect.left + 20, y_offset))
            self.screen.blit(text_surf, text_rect)
            y_offset += 30
    
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
                effects = ", ".join(e['type'] for e in entry['effects'])
                effects_surf = self.dialog_font.render(effects, True, COLORS['text_dim'])
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
        """Draw the action selection menu."""
        if not self.game_state:
            return
            
        actions = self.available_actions.get(self.categories[self.current_category_index], [])
        if not actions:
            return
        
        # Menu background - centered and above bottom HUD
        menu_height = min(len(actions) * 60 + 40, 400)  # Increased height per item
        base_rect = pygame.Rect(
            WINDOW_WIDTH//2 - 400,  # Wider menu
            WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT - menu_height - 20,
            800,  # Wider menu
            menu_height
        )
        rect = self._get_scaled_rect(base_rect)
        self._draw_panel(rect, self.categories[self.current_category_index].value)
        
        # Draw actions
        for i, action in enumerate(actions):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Selection background
            if selected:
                select_rect = pygame.Rect(
                    rect.left + 10,
                    rect.top + 40 + i*50,  # Start below title, more space between items
                    rect.width - 20,
                    40
                )
                pygame.draw.rect(self.screen, COLORS['selector'], select_rect,
                               border_radius=5)
            
            # Action name and cost
            text = f"{action.name} ({action.action_points} AP)"
            text_surf = self.menu_font.render(text, True, color)
            text_rect = text_surf.get_rect(
                midleft=(rect.left + 30,
                        rect.top + 60 + i*50)  # Aligned with selection background
            )
            self.screen.blit(text_surf, text_rect)
            
            # Success chance
            chance = f"{int(action.success_chance*100)}%"
            chance_surf = self.hud_font.render(chance, True, color)
            chance_rect = chance_surf.get_rect(
                midright=(rect.right - 30,
                         rect.top + 60 + i*50)  # Aligned with action name
            )
            self.screen.blit(chance_surf, chance_rect)
            
            # Description for selected action
            if selected:
                desc_surf = self.hud_font.render(action.description, True, COLORS['text_dim'])
                desc_rect = desc_surf.get_rect(
                    topleft=(text_rect.left,
                            text_rect.bottom + 5)
                )
                self.screen.blit(desc_surf, desc_rect)
    
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
        if self.ui_state == UIState.FACTION_SELECT:
            return [
                ("↑/↓", "Select"),
                ("Enter/A", "Confirm")
            ]
        elif self.ui_state == UIState.MAIN_GAME:
            return [
                ("←/→", "Category"),
                ("Enter/A", "Select"),
                ("Y", "Special"),
                ("Esc", "Menu")
            ]
        elif self.ui_state == UIState.ACTION_MENU:
            return [
                ("←/→", "Select"),
                ("Enter/A", "Confirm"),
                ("B/Esc", "Back")
            ]
        return []
    
    def draw(self):
        """Draw the current game state."""
        # Clear screen and draw background
        self.screen.fill(COLORS['background'])
        self._draw_tactical_grid()
        
        if self.ui_state == UIState.FACTION_SELECT:
            self._draw_faction_select()
        else:
            # Draw main game interface
            self._draw_top_hud()
            self._draw_objectives_panel()
            self._draw_dialogue_panel()
            self._draw_tactical_panel()
            self._draw_history_panel()
            self._draw_bottom_hud()
            
            if self.ui_state == UIState.ACTION_MENU:
                self._draw_action_menu()
            elif self.ui_state == UIState.SPECIAL_MENU:
                self._draw_special_menu()
        
        # Update display
        pygame.display.flip()
    
    def _draw_faction_select(self):
        """Draw the faction selection screen."""
        # Clear screen
        self.screen.fill(COLORS['background'])
        
        # Draw title
        title_text = "Select Your Faction"
        title_surf = self.title_font.render(title_text, True, COLORS['text'])
        title_rect = title_surf.get_rect(
            centerx=WINDOW_WIDTH//2,
            top=100
        )
        self.screen.blit(title_surf, title_rect)
        
        # Draw faction options
        y = 300
        factions = [Faction.FBI, Faction.CIA, Faction.LOCAL_PD]
        for i, faction in enumerate(factions):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Draw selection background
            if selected:
                select_rect = pygame.Rect(
                    WINDOW_WIDTH//2 - 200,
                    y - 10,
                    400,
                    50
                )
                pygame.draw.rect(self.screen, COLORS['selector'], select_rect,
                               border_radius=5)
            
            # Draw faction name
            text_surf = self.menu_font.render(faction.value, True, color)
            text_rect = text_surf.get_rect(
                centerx=WINDOW_WIDTH//2,
                centery=y
            )
            self.screen.blit(text_surf, text_rect)
            
            y += 60  # Space between options
    
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
    
    def _execute_selected_action(self):
        """Execute the currently selected action."""
        if not self.game_state:
            return
            
        actions = self.available_actions.get(self.categories[self.current_category_index], [])
        if not actions or self.selected_index >= len(actions):
            return
            
        action = actions[self.selected_index]
        
        # Check if we have enough action points
        if action.action_points > self.game_state.action_points:
            return
            
        # Execute the action through the action system
        result = self.action_system.perform_action(action, self.game_state)
        
        # Update game state
        if result.get('success', False):
            self.game_state.action_points -= action.action_points
            if action.is_special:
                self.game_state.used_special_abilities.append(action.name)
            
            # Add to game history
            self.game_state.add_history_entry({
                'turn': self.game_state.turn,
                'action': action.name,
                'success': True,
                'effects': result.get('effects', []),
                'dialogue_text': action.description  # Add dialogue text
            })
            
            # Update game state after action
            self.game_state.update_state_after_action(action, True)
            
            # Check if turn should end
            if self.game_state.action_points <= 0:
                self._end_turn()
            
            # Update available actions
            self._update_available_actions()
        else:
            # Handle failed action
            self.game_state.add_history_entry({
                'turn': self.game_state.turn,
                'action': action.name,
                'success': False,
                'effects': result.get('effects', []),
                'dialogue_text': f"Failed: {action.description}"
            })
            
            # Update game state for failed action
            self.game_state.update_state_after_action(action, False)
        
        # Return to main game view
        self.ui_state = UIState.MAIN_GAME

    def _update_available_actions(self):
        """Update the list of available actions based on current game state."""
        if self.game_state:
            self.available_actions = self.action_system.get_available_actions(self.game_state)

    def _select_faction(self):
        """Handle faction selection."""
        if self.selected_index == 0:
            faction = Faction.FBI
        elif self.selected_index == 1:
            faction = Faction.CIA
        else:
            faction = Faction.LOCAL_PD
        
        # Initialize game state with selected faction
        self.game_state = GameState(faction)
        
        # Initialize action system
        self.action_system = ActionSystem()
        self._update_available_actions()
        
        # Switch to main game view
        self.ui_state = UIState.MAIN_GAME

    def _handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input events and return whether to continue running."""
        # Handle window resize events
        if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
            try:
                self.windowed_size = event.size
                self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
                self.draw()
                pygame.display.flip()
            except Exception as e:
                print(f"Error handling resize: {e}")
        
        # Update input type
        self.input_handler.update_input_type(event)
        
        # Check for quit events
        if event.type == pygame.QUIT:
            return False
        
        # Check for fullscreen toggle (F11)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return True
        
        # Get movement input
        x, y = self.input_handler.get_movement()
        
        # Handle input based on UI state
        if self.ui_state == UIState.FACTION_SELECT:
            if y != 0:  # Up/Down to select faction
                self.selected_index = (self.selected_index - y) % 3
            elif self.input_handler.get_action_press():  # Enter/A to confirm
                self._select_faction()
        
        elif self.ui_state == UIState.MAIN_GAME:
            if x != 0:  # Left/Right to change category
                self.current_category_index = (
                    self.current_category_index + x
                ) % len(self.categories)
                self.selected_index = 0
                self._update_available_actions()  # Update actions when changing category
            elif self.input_handler.get_action_press():  # Enter/A to open action menu
                self.ui_state = UIState.ACTION_MENU
                self._update_available_actions()  # Refresh available actions
            elif self.input_handler.get_special_press():  # Y for special menu
                self.ui_state = UIState.SPECIAL_MENU
                self._update_special_actions()  # Get special abilities
            elif self.input_handler.get_cancel_press():  # Esc/B to quit
                return False
        
        elif self.ui_state == UIState.ACTION_MENU:
            actions = self.available_actions.get(
                self.categories[self.current_category_index], []
            )
            if not actions:
                self.ui_state = UIState.MAIN_GAME
                return True
            
            if y != 0:  # Up/Down to select action
                self.selected_index = (
                    self.selected_index - y
                ) % len(actions)
            elif self.input_handler.get_action_press():  # Enter/A to confirm
                self._execute_selected_action()
            elif self.input_handler.get_cancel_press():  # Esc/B to go back
                self.ui_state = UIState.MAIN_GAME
        
        elif self.ui_state == UIState.SPECIAL_MENU:
            if self.special_actions:
                if y != 0:  # Up/Down to select special ability
                    self.selected_index = (
                        self.selected_index - y
                    ) % len(self.special_actions)
                elif self.input_handler.get_action_press():  # Enter/A to confirm
                    self._execute_special_action()
            if self.input_handler.get_cancel_press():  # Esc/B to go back
                self.ui_state = UIState.MAIN_GAME
        
        return True
    
    def _update_special_actions(self):
        """Update the list of available special abilities."""
        if not self.game_state:
            return
        
        # Get all special actions from available actions
        self.special_actions = []
        for category_actions in self.available_actions.values():
            for action in category_actions:
                if action.is_special and action.name not in self.game_state.used_special_abilities:
                    self.special_actions.append(action)
        
        # Sort by level
        self.special_actions.sort(key=lambda x: x.special_level)
        self.selected_index = 0  # Reset selection

    def _execute_special_action(self):
        """Execute the selected special ability."""
        if not self.special_actions or self.selected_index >= len(self.special_actions):
            return
        
        action = self.special_actions[self.selected_index]
        
        # Check if we have enough action points
        if action.action_points > self.game_state.action_points:
            return
        
        # Execute the action through the action system
        result = self.action_system.perform_action(action, self.game_state)
        
        # Update game state
        if result.get('success', False):
            self.game_state.action_points -= action.action_points
            self.game_state.used_special_abilities.append(action.name)
            
            # Add to game history
            self.game_state.add_history_entry({
                'turn': self.game_state.turn,
                'action': action.name,
                'success': True,
                'effects': result.get('effects', []),
                'dialogue_text': action.description,
                'is_special': True
            })
            
            # Check if turn should end
            if self.game_state.action_points <= 0:
                self._end_turn()
            
            # Update available actions
            self._update_available_actions()
        else:
            # Handle failed action
            self.game_state.add_history_entry({
                'turn': self.game_state.turn,
                'action': action.name,
                'success': False,
                'effects': result.get('effects', []),
                'dialogue_text': f"Failed: {action.description}",
                'is_special': True
            })
        
        # Return to main game view
        self.ui_state = UIState.MAIN_GAME

    def _draw_special_menu(self):
        """Draw the special abilities menu."""
        if not self.game_state or not self.special_actions:
            return
        
        # Menu background - centered and above bottom HUD
        menu_height = min(len(self.special_actions) * 60 + 40, 400)  # Increased height per item
        base_rect = pygame.Rect(
            WINDOW_WIDTH//2 - 400,  # Wider menu
            WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT - menu_height - 20,
            800,  # Wider menu
            menu_height
        )
        rect = self._get_scaled_rect(base_rect)
        self._draw_panel(rect, "SPECIAL ABILITIES")
        
        # Draw actions
        for i, action in enumerate(self.special_actions):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Selection background
            if selected:
                select_rect = pygame.Rect(
                    rect.left + 10,
                    rect.top + 40 + i*50,  # Start below title, more space between items
                    rect.width - 20,
                    40
                )
                pygame.draw.rect(self.screen, COLORS['selector'], select_rect,
                               border_radius=5)
            
            # Action name and level
            text = f"[Lvl {action.special_level}] {action.name} ({action.action_points} AP)"
            text_surf = self.menu_font.render(text, True, color)
            text_rect = text_surf.get_rect(
                midleft=(rect.left + 30,
                        rect.top + 60 + i*50)  # Aligned with selection background
            )
            self.screen.blit(text_surf, text_rect)
            
            # Success chance
            chance = f"{int(action.success_chance*100)}%"
            chance_surf = self.hud_font.render(chance, True, color)
            chance_rect = chance_surf.get_rect(
                midright=(rect.right - 30,
                         rect.top + 60 + i*50)  # Aligned with action name
            )
            self.screen.blit(chance_surf, chance_rect)
            
            # Description for selected action
            if selected:
                desc_surf = self.hud_font.render(action.description, True, COLORS['text_dim'])
                desc_rect = desc_surf.get_rect(
                    topleft=(text_rect.left,
                            text_rect.bottom + 5)
                )
                self.screen.blit(desc_surf, desc_rect)

    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self._handle_input(event)
            
            # Draw current frame
            self.draw()
            
            # Cap framerate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

    def _end_turn(self):
        """End the current turn."""
        if not self.game_state:
            return
        
        # Process end of turn
        self.game_state.end_turn()
        
        # Update available actions for next turn
        self._update_available_actions()
        
        # Reset selection
        self.selected_index = 0

def main():
    ui = TacticalUI()
    ui.run()

if __name__ == "__main__":
    main() 