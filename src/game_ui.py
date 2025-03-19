import pygame
import pygame.gfxdraw
import sys
import math
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple
from core.dialogue_system import (DialogueSystem, ActionSystem, GameState,
                                Faction, ActionCategory, GameAction)
from scenarios.base_scenario import create_bank_scenario
from config import Config

# Initialize Pygame
pygame.init()
pygame.joystick.init()

# Constants
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 60
TOOLTIP_PADDING = 10
TOOLTIP_FONT_SIZE = 20
DIALOG_FONT_SIZE = 18
HUD_FONT_SIZE = 24
TITLE_FONT_SIZE = 48
MENU_FONT_SIZE = 32

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
    'highlight': (0, 255, 100),  # Bright green
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
    FACTION_SELECT = 1
    MAIN_GAME = 2
    ACTION_MENU = 3
    SPECIAL_MENU = 4

class GameUI:
    def __init__(self):
        # Initialize basic display
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("We Have a Situation!")
        self.clock = pygame.time.Clock()
        
        # Initialize game components
        self.action_system = ActionSystem()
        self.dialogue_system = DialogueSystem()
        self.scenario = create_bank_scenario()
        
        # UI state
        self.ui_state = UIState.FACTION_SELECT
        self.selected_index = 0
        self.game_state = None
        
        # Controller setup
        self.controllers = []
        self._setup_controllers()
        
        # Load assets
        self._load_assets()
        
        # Menu items
        self.faction_options = [
            Faction.FBI.value,
            Faction.CIA.value,
            Faction.LOCAL_PD.value
        ]
        
        # Action categories and lists
        self.current_category_index = 0
        self.categories = list(ActionCategory)
        self.available_actions: Dict[ActionCategory, List[GameAction]] = {}
        self.special_actions: List[GameAction] = []
        
        # Input settings
        self.COOLDOWN_DURATION = 150  # ms
        self.dead_zone = 0.2
        self.last_input_time = 0
    
    def _setup_controllers(self):
        """Initialize game controllers."""
        self.controllers = [pygame.joystick.Joystick(i) 
                          for i in range(pygame.joystick.get_count())]
        for controller in self.controllers:
            controller.init()
    
    def _load_assets(self):
        """Load game assets (logo, fonts, etc.)."""
        # Load logo
        try:
            self.logo = pygame.image.load("assets/WHAS-logo.png")
            self.logo = pygame.transform.scale(self.logo, (600, 300))
        except:
            print("Warning: Could not load logo")
            self.logo = None
        
        # Initialize fonts
        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.menu_font = pygame.font.Font(None, MENU_FONT_SIZE)
        self.hud_font = pygame.font.Font(None, HUD_FONT_SIZE)
        self.tooltip_font = pygame.font.Font(None, TOOLTIP_FONT_SIZE)
        
        # Load control hints
        self.control_hints = {
            UIState.FACTION_SELECT: [
                ("↑/↓/L↕", "Select Faction"),
                ("Enter/A", "Confirm")
            ],
            UIState.MAIN_GAME: [
                ("←/→/L↔", "Change Category"),
                ("Enter/A", "Open Actions"),
                ("Y", "Special Abilities"),
                ("Esc", "Exit")
            ],
            UIState.ACTION_MENU: [
                ("←/→/L↔", "Select Action"),
                ("Enter/A", "Confirm"),
                ("Esc/B", "Back")
            ]
        }
    
    def _draw_faction_select(self):
        """Draw faction selection screen."""
        self.screen.fill(COLORS['background'])
        
        # Draw logo
        if self.logo:
            logo_rect = self.logo.get_rect(centerx=WINDOW_WIDTH//2, y=50)
            self.screen.blit(self.logo, logo_rect)
        
        # Draw title
        title = self.title_font.render("Choose Your Faction", True, COLORS['text'])
        title_rect = title.get_rect(centerx=WINDOW_WIDTH//2, y=400)
        self.screen.blit(title, title_rect)
        
        # Draw faction options
        for i, faction in enumerate(self.faction_options):
            color = COLORS['selected'] if i == self.selected_index else COLORS['text']
            text = self.menu_font.render(faction, True, color)
            rect = text.get_rect(centerx=WINDOW_WIDTH//2, y=500 + i*60)
            self.screen.blit(text, rect)
    
    def _draw_tooltip(self, text: str, pos: Tuple[int, int]):
        """Draw a tooltip at the given position."""
        # Render text
        tooltip_surface = self.tooltip_font.render(text, True, COLORS['text'])
        
        # Create background rect with padding
        bg_rect = tooltip_surface.get_rect(topleft=pos)
        bg_rect.inflate_ip(TOOLTIP_PADDING * 2, TOOLTIP_PADDING * 2)
        
        # Ensure tooltip stays on screen
        if bg_rect.right > WINDOW_WIDTH:
            bg_rect.right = WINDOW_WIDTH - 5
        if bg_rect.bottom > WINDOW_HEIGHT:
            bg_rect.bottom = WINDOW_HEIGHT - 5
        
        # Draw background
        pygame.draw.rect(self.screen, COLORS['tooltip_bg'], bg_rect, border_radius=5)
        
        # Draw text
        text_pos = (bg_rect.left + TOOLTIP_PADDING, bg_rect.top + TOOLTIP_PADDING)
        self.screen.blit(tooltip_surface, text_pos)
    
    def _draw_control_hints(self):
        """Draw control hints for current state."""
        hints = self.control_hints.get(self.ui_state, [])
        y = WINDOW_HEIGHT - 150  # Moved up from bottom
        x = WINDOW_WIDTH - 250   # Fixed x position
        
        # Draw background panel for all hints
        total_height = len(hints) * 30 + 20
        panel_rect = pygame.Rect(x - 20, y - 10, 250, total_height)
        pygame.draw.rect(self.screen, COLORS['tooltip_bg'], panel_rect, border_radius=5)
        
        for control, action in hints:
            text = f"{control}: {action}"
            hint_surf = self.hud_font.render(text, True, COLORS['text'])
            hint_rect = hint_surf.get_rect(topright=(x + 210, y))
            self.screen.blit(hint_surf, hint_rect)
            y += 30
    
    def _draw_radial_menu(self, center: Tuple[int, int], radius: int, 
                         items: List[str], selected: int):
        """Draw a radial menu for actions."""
        if not items:
            return
        
        # Draw central hub
        pygame.draw.circle(self.screen, COLORS['menu_bg'], center, RADIAL_MENU_INNER_RADIUS)
        
        angle_step = 360 / len(items)
        for i, item in enumerate(items):
            angle_rad = math.radians(i * angle_step - 90)  # Start at top
            
            # Calculate positions using sin/cos
            direction_x = math.cos(angle_rad)
            direction_y = math.sin(angle_rad)
            
            inner_pos = (
                int(center[0] + RADIAL_MENU_INNER_RADIUS * direction_x),
                int(center[1] + RADIAL_MENU_INNER_RADIUS * direction_y)
            )
            outer_pos = (
                int(center[0] + radius * direction_x),
                int(center[1] + radius * direction_y)
            )
            
            # Draw connecting line
            if i == selected:
                pygame.draw.line(self.screen, COLORS['highlight'], inner_pos, outer_pos, 3)
            else:
                pygame.draw.line(self.screen, COLORS['menu_bg'], inner_pos, outer_pos, 2)
            
            # Draw selection indicator and text background
            if i == selected:
                # Draw arc segment
                start_angle = math.radians(i * angle_step - angle_step/2 - 90)
                end_angle = math.radians(i * angle_step + angle_step/2 - 90)
                rect = pygame.Rect(center[0] - radius, center[1] - radius,
                                 radius * 2, radius * 2)
                pygame.draw.arc(self.screen, COLORS['highlight'], rect,
                              start_angle, end_angle, 3)
                
                # Draw text background
                text = self.menu_font.render(item, True, COLORS['selected'])
                text_rect = text.get_rect(center=outer_pos)
                bg_rect = text_rect.inflate(20, 10)
                pygame.draw.rect(self.screen, COLORS['highlight'], bg_rect, border_radius=5)
            
            # Draw text
            text = self.menu_font.render(item, True, 
                                       COLORS['selected'] if i == selected else COLORS['text'])
            text_rect = text.get_rect(center=outer_pos)
            self.screen.blit(text, text_rect)
            
            # Draw tooltip for selected item
            if i == selected:
                action = self.available_actions[self.categories[self.current_category_index]][i]
                tooltip_text = f"Success: {action.success_chance*100:.0f}% | Cost: {action.action_points} AP"
                self._draw_tooltip(tooltip_text, (text_rect.centerx - 100, text_rect.bottom + 10))
    
    def _draw_hud(self):
        """Draw the game HUD."""
        if not self.game_state:
            return
        
        # Draw AP
        ap_text = f"AP: {self.game_state.action_points}"
        ap_surf = self.hud_font.render(ap_text, True, COLORS['ap'])
        self.screen.blit(ap_surf, (20, 20))
        
        # Draw faction name
        faction_text = f"Faction: {self.game_state.player_faction.value}"
        faction_surf = self.hud_font.render(faction_text, True, COLORS['text'])
        self.screen.blit(faction_surf, (20, 60))
        
        # Draw meters
        meters = [
            ("Trust", self.game_state.trust_level, COLORS['trust']),
            ("Tension", self.game_state.tension_level, COLORS['tension']),
            ("Intel", self.game_state.intel_level, COLORS['intel'])
        ]
        
        for i, (name, value, color) in enumerate(meters):
            # Draw label
            label = self.hud_font.render(name, True, color)
            self.screen.blit(label, (20, 100 + i*40))
            
            # Draw meter
            meter_rect = pygame.Rect(100, 105 + i*40, 200, 20)
            pygame.draw.rect(self.screen, (50, 50, 50), meter_rect)
            fill_rect = pygame.Rect(meter_rect.left, meter_rect.top,
                                  meter_rect.width * value, meter_rect.height)
            pygame.draw.rect(self.screen, color, fill_rect)
        
        # Draw resources
        resource_x = 320
        for resource, amount in self.game_state.resources.items():
            text = f"{resource.capitalize()}: {amount}"
            res_surf = self.hud_font.render(text, True, COLORS['text'])
            self.screen.blit(res_surf, (resource_x, 20))
            resource_x += 200
    
    def _draw_game_screen(self):
        """Draw the main game screen."""
        self.screen.fill(COLORS['background'])
        
        # Draw tactical grid background
        self._draw_tactical_grid()
        
        # Draw side panels
        self._draw_left_panel()   # Dialogue and objectives
        self._draw_right_panel()  # Game history and tactical info
        
        # Draw top HUD
        self._draw_top_hud()
        
        # Draw bottom HUD
        self._draw_bottom_hud()
        
        # Draw action menu if active
        if self.ui_state == UIState.ACTION_MENU:
            self._draw_action_menu()
        
        # Draw control hints
        self._draw_control_hints()
    
    def _draw_tactical_grid(self):
        """Draw background tactical grid."""
        # Draw vertical lines
        for x in range(0, WINDOW_WIDTH, UI_ELEMENTS['grid_size']):
            alpha = 255 if x % (UI_ELEMENTS['grid_size'] * 4) == 0 else 100
            color = (*COLORS['grid'], alpha)
            pygame.draw.line(self.screen, color, (x, 0), (x, WINDOW_HEIGHT))
        
        # Draw horizontal lines
        for y in range(0, WINDOW_HEIGHT, UI_ELEMENTS['grid_size']):
            alpha = 255 if y % (UI_ELEMENTS['grid_size'] * 4) == 0 else 100
            color = (*COLORS['grid'], alpha)
            pygame.draw.line(self.screen, color, (0, y), (WINDOW_WIDTH, y))
    
    def _draw_left_panel(self):
        """Draw left panel with dialogue and objectives."""
        panel_rect = pygame.Rect(20, TOP_HUD_HEIGHT + 20, 
                               SIDE_PANEL_WIDTH, WINDOW_HEIGHT - TOP_HUD_HEIGHT - BOTTOM_HUD_HEIGHT - 40)
        
        # Draw panel background
        pygame.draw.rect(self.screen, COLORS['panel_bg'], panel_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
        pygame.draw.rect(self.screen, COLORS['border'], panel_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'],
                        width=UI_ELEMENTS['border_width'])
        
        # Draw objectives section
        objectives_height = 200
        objectives_rect = pygame.Rect(panel_rect.left, panel_rect.top,
                                    panel_rect.width, objectives_height)
        self._draw_objectives(objectives_rect)
        
        # Draw dialogue section
        dialogue_rect = pygame.Rect(panel_rect.left, panel_rect.top + objectives_height + 10,
                                  panel_rect.width, panel_rect.height - objectives_height - 10)
        self._draw_dialogue(dialogue_rect)
    
    def _draw_objectives(self, rect):
        """Draw mission objectives."""
        if not self.game_state:
            return
            
        # Draw section title
        title = self.menu_font.render("OBJECTIVES", True, COLORS['text'])
        title_rect = title.get_rect(topleft=(rect.left + 10, rect.top + 10))
        self.screen.blit(title, title_rect)
        
        # Draw objectives
        y = rect.top + 50
        for obj in self.game_state.get_objectives():
            # Draw priority indicator
            priority_color = COLORS['critical'] if obj['priority'] == 1 else (
                           COLORS['warning'] if obj['priority'] == 2 else COLORS['text_dim'])
            pygame.draw.circle(self.screen, priority_color,
                             (rect.left + 20, y + 10), 5)
            
            # Draw objective text
            color = COLORS['success'] if obj['complete'] else (
                    COLORS['failure'] if obj['failed'] else COLORS['text'])
            text = self.hud_font.render(obj['text'], True, color)
            self.screen.blit(text, (rect.left + 40, y))
            y += 30
    
    def _draw_dialogue(self, rect):
        """Draw dialogue history."""
        if not self.game_state:
            return
            
        # Draw section title
        title = self.menu_font.render("COMMS", True, COLORS['text'])
        title_rect = title.get_rect(topleft=(rect.left + 10, rect.top + 10))
        self.screen.blit(title, title_rect)
        
        # Draw messages
        y = rect.top + 50
        for entry in self.game_state.dialogue_history[-8:]:
            # Draw speaker
            speaker_color = COLORS['success'] if entry.get('success', True) else COLORS['failure']
            speaker = self.hud_font.render(f"{entry['speaker']}:", True, speaker_color)
            self.screen.blit(speaker, (rect.left + 10, y))
            
            # Draw message
            text = self.tooltip_font.render(entry['text'], True, COLORS['text'])
            text_rect = text.get_rect(topleft=(rect.left + 20, y + 25))
            self.screen.blit(text, text_rect)
            
            y += 45
    
    def _draw_right_panel(self):
        """Draw right panel with game history and tactical info."""
        panel_rect = pygame.Rect(WINDOW_WIDTH - SIDE_PANEL_WIDTH - 20,
                               TOP_HUD_HEIGHT + 20,
                               SIDE_PANEL_WIDTH,
                               WINDOW_HEIGHT - TOP_HUD_HEIGHT - BOTTOM_HUD_HEIGHT - 40)
        
        # Draw panel background
        pygame.draw.rect(self.screen, COLORS['panel_bg'], panel_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
        pygame.draw.rect(self.screen, COLORS['border'], panel_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'],
                        width=UI_ELEMENTS['border_width'])
        
        # Draw tactical info section
        tactical_height = 200
        tactical_rect = pygame.Rect(panel_rect.left, panel_rect.top,
                                  panel_rect.width, tactical_height)
        self._draw_tactical_info(tactical_rect)
        
        # Draw history section
        history_rect = pygame.Rect(panel_rect.left, panel_rect.top + tactical_height + 10,
                                 panel_rect.width, panel_rect.height - tactical_height - 10)
        self._draw_history(history_rect)
    
    def _draw_tactical_info(self, rect):
        """Draw tactical information."""
        if not self.game_state:
            return
            
        # Draw section title
        title = self.menu_font.render("TACTICAL", True, COLORS['text'])
        title_rect = title.get_rect(topleft=(rect.left + 10, rect.top + 10))
        self.screen.blit(title, title_rect)
        
        # Draw tactical positions
        y = rect.top + 50
        for pos, active in self.game_state.tactical_positions.items():
            color = COLORS['success'] if active else COLORS['inactive']
            text = self.hud_font.render(pos.replace('_', ' ').title(), True, color)
            self.screen.blit(text, (rect.left + 20, y))
            y += 30
    
    def _draw_history(self, rect):
        """Draw game history."""
        if not self.game_state:
            return
            
        # Draw section title
        title = self.menu_font.render(f"TURN {self.game_state.turn}", True, COLORS['text'])
        title_rect = title.get_rect(topleft=(rect.left + 10, rect.top + 10))
        self.screen.blit(title, title_rect)
        
        # Draw history entries
        y = rect.top + 50
        for entry in self.game_state.game_history[-6:]:
            # Draw turn number
            turn_text = f"T{entry['turn']}"
            turn_surf = self.hud_font.render(turn_text, True, COLORS['text_dim'])
            self.screen.blit(turn_surf, (rect.left + 10, y))
            
            # Draw action
            success = entry.get('success', False)
            color = COLORS['success'] if success else COLORS['failure']
            action_surf = self.hud_font.render(entry['action'], True, color)
            self.screen.blit(action_surf, (rect.left + 60, y))
            
            # Draw effects
            if entry.get('effects'):
                effects_text = ", ".join(e['type'] for e in entry['effects'])
                effects_surf = self.tooltip_font.render(effects_text, True, COLORS['text_dim'])
                self.screen.blit(effects_surf, (rect.left + 20, y + 25))
            
            y += 50
    
    def _draw_top_hud(self):
        """Draw the top HUD with core metrics and resources."""
        if not self.game_state:
            return
        
        # Draw HUD background
        hud_rect = pygame.Rect(0, 0, WINDOW_WIDTH, TOP_HUD_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], hud_rect)
        pygame.draw.line(self.screen, COLORS['border'],
                        (0, TOP_HUD_HEIGHT),
                        (WINDOW_WIDTH, TOP_HUD_HEIGHT),
                        width=UI_ELEMENTS['border_width'])
        
        # Draw faction and AP
        faction_text = f"{self.game_state.player_faction.value}"
        faction_surf = self.hud_font.render(faction_text, True, COLORS['text'])
        self.screen.blit(faction_surf, (20, 10))
        
        ap_text = f"AP: {self.game_state.action_points}"
        ap_surf = self.hud_font.render(ap_text, True, COLORS['ap'])
        self.screen.blit(ap_surf, (20, 40))
        
        # Draw core metrics
        metrics = [
            ("TRUST", self.game_state.trust_level, COLORS['trust']),
            ("TENSION", self.game_state.tension_level, COLORS['tension']),
            ("INTEL", self.game_state.intel_level, COLORS['intel'])
        ]
        
        meter_width = 150
        x = WINDOW_WIDTH//2 - (meter_width * len(metrics))//2
        for name, value, color in metrics:
            # Draw label
            label = self.hud_font.render(name, True, color)
            self.screen.blit(label, (x, 10))
            
            # Draw meter background
            meter_rect = pygame.Rect(x, 40, meter_width, UI_ELEMENTS['meter_height'])
            pygame.draw.rect(self.screen, COLORS['meter_bg'], meter_rect,
                           border_radius=UI_ELEMENTS['panel_border_radius'])
            
            # Draw meter fill
            fill_rect = pygame.Rect(meter_rect.left, meter_rect.top,
                                  meter_rect.width * value, meter_rect.height)
            pygame.draw.rect(self.screen, color, fill_rect,
                           border_radius=UI_ELEMENTS['panel_border_radius'])
            
            x += meter_width + 50
        
        # Draw resources
        resource_x = WINDOW_WIDTH - 500
        for resource, amount in self.game_state.resources.items():
            text = f"{resource.upper()}: {amount}"
            res_surf = self.hud_font.render(text, True, COLORS['text'])
            self.screen.blit(res_surf, (resource_x, 25))
            resource_x += 120
    
    def _draw_bottom_hud(self):
        """Draw the bottom HUD with current category and controls."""
        # Draw HUD background
        hud_rect = pygame.Rect(0, WINDOW_HEIGHT - BOTTOM_HUD_HEIGHT,
                             WINDOW_WIDTH, BOTTOM_HUD_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], hud_rect)
        pygame.draw.line(self.screen, COLORS['border'],
                        (0, hud_rect.top),
                        (WINDOW_WIDTH, hud_rect.top),
                        width=UI_ELEMENTS['border_width'])
        
        if self.ui_state == UIState.MAIN_GAME:
            # Draw current category
            category = self.categories[self.current_category_index].value
            cat_text = self.menu_font.render(category, True, COLORS['text'])
            cat_rect = cat_text.get_rect(center=(WINDOW_WIDTH//2, hud_rect.centery))
            self.screen.blit(cat_text, cat_rect)
            
            # Draw category selection indicators
            arrow_color = COLORS['text']
            left_arrow = "◄" if self.current_category_index > 0 else "  "
            right_arrow = "►" if self.current_category_index < len(self.categories)-1 else "  "
            
            left_surf = self.menu_font.render(left_arrow, True, arrow_color)
            right_surf = self.menu_font.render(right_arrow, True, arrow_color)
            
            self.screen.blit(left_surf, (cat_rect.left - 40, cat_rect.top))
            self.screen.blit(right_surf, (cat_rect.right + 10, cat_rect.top))
    
    def _draw_action_menu(self):
        """Draw the action selection menu."""
        if not self.game_state:
            return
            
        actions = self.available_actions.get(self.categories[self.current_category_index], [])
        if not actions:
            return
        
        # Draw menu background
        menu_height = len(actions) * 50 + 20
        menu_rect = pygame.Rect(WINDOW_WIDTH//2 - 300, ACTION_MENU_Y,
                              600, menu_height)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], menu_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'])
        pygame.draw.rect(self.screen, COLORS['border'], menu_rect,
                        border_radius=UI_ELEMENTS['panel_border_radius'],
                        width=UI_ELEMENTS['border_width'])
        
        # Draw actions
        for i, action in enumerate(actions):
            selected = i == self.selected_index
            color = COLORS['highlight'] if selected else COLORS['text']
            
            # Draw selection background
            if selected:
                select_rect = pygame.Rect(menu_rect.left + 10,
                                        menu_rect.top + 10 + i*50,
                                        menu_rect.width - 20, 40)
                pygame.draw.rect(self.screen, COLORS['border'], select_rect,
                               border_radius=5)
            
            # Draw action name and cost
            text = f"{action.name} ({action.action_points} AP)"
            text_surf = self.menu_font.render(text, True, color)
            text_rect = text_surf.get_rect(midleft=(menu_rect.left + 30,
                                                   menu_rect.top + 30 + i*50))
            self.screen.blit(text_surf, text_rect)
            
            # Draw success chance
            chance_text = f"{int(action.success_chance*100)}%"
            chance_surf = self.hud_font.render(chance_text, True, color)
            chance_rect = chance_surf.get_rect(midright=(menu_rect.right - 30,
                                                       menu_rect.top + 30 + i*50))
            self.screen.blit(chance_surf, chance_rect)
            
            # Draw tooltip for selected action
            if selected:
                tooltip_text = action.description
                self._draw_tooltip(tooltip_text,
                                 (text_rect.left, text_rect.bottom + 10))
    
    def _handle_input(self):
        """Handle both controller and keyboard input."""
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle keyboard input
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.ui_state in (UIState.ACTION_MENU, UIState.SPECIAL_MENU):
                        self.ui_state = UIState.MAIN_GAME
                    else:
                        return False
                
                if current_time - self.last_input_time < self.COOLDOWN_DURATION:
                    continue
                
                if self.ui_state == UIState.FACTION_SELECT:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected_index = (self.selected_index - 1) % len(self.faction_options)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected_index = (self.selected_index + 1) % len(self.faction_options)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._select_faction()
                
                elif self.ui_state == UIState.MAIN_GAME:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.current_category_index = (self.current_category_index - 1) % len(self.categories)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.current_category_index = (self.current_category_index + 1) % len(self.categories)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.ui_state = UIState.ACTION_MENU
                        self.selected_index = 0  # Reset selection when opening menu
                    elif event.key == pygame.K_y:
                        self.ui_state = UIState.SPECIAL_MENU
                        self.selected_index = 0  # Reset selection when opening menu
                
                elif self.ui_state in (UIState.ACTION_MENU, UIState.SPECIAL_MENU):
                    actions = self.available_actions.get(self.categories[self.current_category_index], [])
                    if not actions:
                        continue
                        
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.selected_index = (self.selected_index - 1) % len(actions)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.selected_index = (self.selected_index + 1) % len(actions)
                        self.last_input_time = current_time
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._execute_selected_action()
            
            # Handle D-pad input
            elif event.type == pygame.JOYHATMOTION:
                if current_time - self.last_input_time < self.COOLDOWN_DURATION:
                    continue
                
                x_value, y_value = event.value
                
                if self.ui_state == UIState.FACTION_SELECT:
                    if y_value > 0:  # Up
                        self.selected_index = (self.selected_index - 1) % len(self.faction_options)
                        self.last_input_time = current_time
                    elif y_value < 0:  # Down
                        self.selected_index = (self.selected_index + 1) % len(self.faction_options)
                        self.last_input_time = current_time
                
                elif self.ui_state == UIState.MAIN_GAME:
                    if x_value != 0:  # Left/Right
                        self.current_category_index = (self.current_category_index + x_value) % len(self.categories)
                        self.last_input_time = current_time
                
                elif self.ui_state in (UIState.ACTION_MENU, UIState.SPECIAL_MENU):
                    actions = self.available_actions.get(self.categories[self.current_category_index], [])
                    if not actions:
                        continue
                    
                    if x_value != 0:  # Left/Right
                        self.selected_index = (self.selected_index + x_value) % len(actions)
                        self.last_input_time = current_time
            
            # Handle controller buttons
            elif event.type == pygame.JOYBUTTONDOWN:
                if current_time - self.last_input_time < self.COOLDOWN_DURATION:
                    continue
                    
                if self.ui_state == UIState.FACTION_SELECT:
                    if event.button == 0:  # A button
                        self._select_faction()
                elif self.ui_state == UIState.MAIN_GAME:
                    if event.button == 0:  # A button
                        self.ui_state = UIState.ACTION_MENU
                        self.selected_index = 0  # Reset selection when opening menu
                    elif event.button == 3:  # Y button
                        self.ui_state = UIState.SPECIAL_MENU
                        self.selected_index = 0  # Reset selection when opening menu
                elif self.ui_state in (UIState.ACTION_MENU, UIState.SPECIAL_MENU):
                    if event.button == 0:  # A button
                        self._execute_selected_action()
                    elif event.button == 1:  # B button
                        self.ui_state = UIState.MAIN_GAME
                
                self.last_input_time = current_time
            
            # Handle analog stick input
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis < 2:  # Left stick
                    self._handle_stick_movement(event.value, event.axis, current_time)
        
        return True
    
    def _handle_stick_movement(self, value: float, axis: int, current_time: int):
        """Handle analog stick movement with improved sensitivity."""
        if abs(value) < self.dead_zone:
            return
            
        if current_time - self.last_input_time < self.COOLDOWN_DURATION:
            return
        
        if self.ui_state == UIState.FACTION_SELECT:
            if axis == 1:  # Vertical
                if value > 0:  # Down
                    self.selected_index = (self.selected_index + 1) % len(self.faction_options)
                    self.last_input_time = current_time
                elif value < 0:  # Up
                    self.selected_index = (self.selected_index - 1) % len(self.faction_options)
                    self.last_input_time = current_time
        
        elif self.ui_state == UIState.MAIN_GAME:
            if axis == 0:  # Horizontal
                if value > 0:  # Right
                    self.current_category_index = (self.current_category_index + 1) % len(self.categories)
                    self.last_input_time = current_time
                elif value < 0:  # Left
                    self.current_category_index = (self.current_category_index - 1) % len(self.categories)
                    self.last_input_time = current_time
        
        elif self.ui_state in (UIState.ACTION_MENU, UIState.SPECIAL_MENU):
            actions = self.available_actions.get(self.categories[self.current_category_index], [])
            if not actions:
                return
                
            if axis == 0:  # Horizontal
                if value > 0:  # Right
                    self.selected_index = (self.selected_index + 1) % len(actions)
                    self.last_input_time = current_time
                elif value < 0:  # Left
                    self.selected_index = (self.selected_index - 1) % len(actions)
                    self.last_input_time = current_time
    
    def _select_faction(self):
        """Handle faction selection."""
        selected_faction = next(f for f in Faction 
                              if f.value == self.faction_options[self.selected_index])
        self.game_state = GameState(selected_faction)
        self.ui_state = UIState.MAIN_GAME
        self._update_available_actions()
    
    def _update_available_actions(self):
        """Update available actions based on game state."""
        if not self.game_state:
            return
        
        self.available_actions = self.action_system.get_available_actions(self.game_state)
        self.special_actions = [
            action for actions in self.available_actions.values()
            for action in actions if action.is_special
        ]
    
    def _execute_selected_action(self):
        """Execute the currently selected action."""
        if self.ui_state == UIState.ACTION_MENU:
            actions = self.available_actions.get(self.categories[self.current_category_index], [])
            if not actions or self.selected_index >= len(actions):
                return
            
            action = actions[self.selected_index]
            if action.action_points <= self.game_state.action_points:
                result = self.action_system.perform_action(action, self.game_state)
                self.game_state.action_points -= action.action_points
                self._update_available_actions()
                
                if self.game_state.action_points <= 0:
                    self._end_turn()
        
        self.ui_state = UIState.MAIN_GAME
    
    def _end_turn(self):
        """Handle end of turn."""
        # Player turn ends
        self.game_state.action_points = 3
        self.game_state.used_special_abilities.clear()
        
        # Hostage taker's turn
        self._execute_hostage_taker_turn()
        
        # Next turn begins
        self.game_state.turn += 1
        self._update_available_actions()
    
    def _execute_hostage_taker_turn(self):
        """Execute the hostage taker's turn."""
        # Simulate hostage taker decision making
        tension = self.game_state.tension_level
        trust = self.game_state.trust_level
        
        # Choose action based on game state
        if tension > 0.7:
            # High tension - likely to take aggressive action
            action_text = "The situation is escalating. One wrong move and this ends badly!"
            self.game_state.dialogue_history.append({
                'turn': self.game_state.turn,
                'speaker': 'Hostage Taker',
                'text': action_text,
                'success': True
            })
            self.game_state.tension_level = min(1.0, self.game_state.tension_level + 0.1)
            
        elif trust > 0.6:
            # High trust - might release a hostage
            action_text = "I'm willing to show good faith. One hostage can go free."
            self.game_state.dialogue_history.append({
                'turn': self.game_state.turn,
                'speaker': 'Hostage Taker',
                'text': action_text,
                'success': True
            })
            self.game_state.hostages_released += 1
            self.game_state.trust_level = max(0.0, self.game_state.trust_level - 0.1)
            
        else:
            # Neutral state - make demands
            action_text = "Time is running out! Meet our demands or face the consequences!"
            self.game_state.dialogue_history.append({
                'turn': self.game_state.turn,
                'speaker': 'Hostage Taker',
                'text': action_text,
                'success': True
            })
            self.game_state.tension_level = min(1.0, self.game_state.tension_level + 0.05)
        
        # Add to game history
        self.game_state.game_history.append({
            'turn': self.game_state.turn,
            'action': 'Hostage Taker Action',
            'success': True,
            'effects': [{'type': 'hostage_taker_turn'}]
        })
    
    def run(self):
        """Main game loop."""
        running = True
        while running:
            # Handle input
            running = self._handle_input()
            
            # Draw current screen
            if self.ui_state == UIState.FACTION_SELECT:
                self._draw_faction_select()
            else:
                self._draw_game_screen()
            
            # Draw control hints
            self._draw_control_hints()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

def main():
    game = GameUI()
    game.run()

if __name__ == "__main__":
    main() 