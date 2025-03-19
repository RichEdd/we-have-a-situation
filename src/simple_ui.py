import pygame
import sys
import math
import random
from game_core import GameState, ActionSystem, ActionType, GamePhase
from icon_loader import IconManager

# Window dimensions
WINDOW_WIDTH = 1600  # Increased for more space
WINDOW_HEIGHT = 900  # Increased for more space

# UI Layout
SIDEBAR_WIDTH = 400  # Increased from 350 for more message space
MAIN_PANEL_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
ACTION_MENU_WIDTH = 500

# Colors
COLORS = {
    'background': (10, 20, 30),
    'panel_bg': (15, 25, 35),
    'panel_dark': (8, 16, 24),
    'text': (0, 255, 170),
    'text_dim': (0, 155, 100),
    'highlight': (255, 255, 255),
    'warning': (255, 200, 0),
    'critical': (255, 60, 60),
    'success': (0, 255, 100),
    'morale': (30, 144, 255),  # Dodger Blue color for morale
    'panel_border': (0, 255, 170, 50),
    'icon': (0, 255, 170),     # Color for icons
    'icon_dim': (0, 155, 100)  # Dimmed icon color
}

# Tactical Icons (Using Unicode symbols)
ICONS = {
    'ap': '⚡'          # Lightning bolt for action points
}

class SimpleUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Crisis Negotiator")
        
        # Initialize fonts - slightly larger
        self.title_font = pygame.font.Font(None, 56)
        self.main_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
        # Try to load a font that supports Unicode icons
        try:
            self.icon_font = pygame.font.SysFont('segoeuisymbol', 32)  # Font that supports Unicode icons
        except:
            self.icon_font = self.main_font  # Fallback to main font if special font not available
        
        # Initialize icon manager
        self.icon_manager = IconManager(icon_size=24)  # 24px icons
        
        # Initialize game systems
        self.game_state = GameState()
        self.action_system = ActionSystem()
        
        # UI state
        self.selected_type = None
        self.selected_action = 0
        self.show_menu = False
        self.menu_animation = 0
        self.last_menu_time = 0
        self.in_submenu = False
        self.show_exit_confirm = False  # New flag for exit confirmation
        
        # Visual feedback state
        self.screen_shake = 0
        self.flash_timer = 0
        self.shake_offset = (0, 0)
        self.ap_warning_timer = 0  # New timer for AP warning message
        self.ap_warning_text = ""  # Text to display for AP warning
    
    def draw_text(self, text, font, x, y, color=COLORS['text'], center=False):
        """Draw text on the screen."""
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.centerx = x
            rect.y = y
        else:
            rect.x = x
            rect.y = y
        self.screen.blit(surface, rect)
        return rect.bottom
    
    def draw_panel(self, rect, title=None):
        """Draw a standard panel with background and border."""
        pygame.draw.rect(self.screen, COLORS['panel_bg'], rect)
        pygame.draw.rect(self.screen, COLORS['panel_border'], rect, 2)
        
        if title:
            title_surf = self.main_font.render(title, True, COLORS['text'])
            title_rect = title_surf.get_rect(
                midtop=(rect.centerx, rect.top + 10)
            )
            self.screen.blit(title_surf, title_rect)
            return title_rect.bottom + 10
        return rect.top + 10
    
    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width."""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_surface = font.render(word + ' ', True, COLORS['text'])
            word_width = word_surface.get_width()
            
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def draw_stat(self, icon_name, value, x, y):
        """Draw a stat with an icon and value."""
        icon_size = 24  # Updated to match IconManager size
        
        # Draw icon background with padding
        bg_padding = 4  # Add padding around the icon
        bg_size = icon_size + (bg_padding * 2)
        icon_rect = pygame.Rect(x, y, bg_size, bg_size)
        
        # Draw background
        pygame.draw.rect(self.screen, COLORS['panel_dark'], icon_rect, border_radius=4)
        
        # Draw icon centered in the background
        icon = self.icon_manager.get_icon(icon_name)
        if icon:
            # Draw the actual icon
            icon_x = x + bg_padding
            icon_y = y + bg_padding
            self.screen.blit(icon, (icon_x, icon_y))
        else:
            # Fallback to Unicode icon if PNG not loaded
            icon_surf = self.icon_font.render(ICONS.get(icon_name, '?'), True, COLORS['icon'])
            icon_rect = icon_surf.get_rect(center=(x + bg_size//2, y + bg_size//2))
            self.screen.blit(icon_surf, icon_rect)
        
        # Draw value with adjusted spacing
        value_surf = self.main_font.render(str(value), True, COLORS['text'])
        self.screen.blit(value_surf, (x + bg_size + 8, y + (bg_size - value_surf.get_height())//2))

    def draw_status(self):
        """Draw the game status information."""
        # Draw sidebar background
        sidebar = pygame.Rect(0, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], sidebar)
        pygame.draw.line(self.screen, COLORS['panel_border'], 
                        (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, WINDOW_HEIGHT), 2)
        
        # Draw turn number
        y = 20
        self.draw_text(f"Turn {self.game_state.turn}", self.main_font, SIDEBAR_WIDTH//2, y, center=True)
        
        # Draw meters panel (without title)
        y += 30
        meter_panel = pygame.Rect(20, y, SIDEBAR_WIDTH - 40, 110)  # Reduced height since no title
        pygame.draw.rect(self.screen, COLORS['panel_bg'], meter_panel)
        pygame.draw.rect(self.screen, COLORS['panel_border'], meter_panel, 2)
        
        # Draw meters with tighter spacing
        y += 15  # Start meters a bit lower in the panel
        self.draw_meter("Trust", self.game_state.trust, y, COLORS['success'])
        y += 25
        self.draw_meter("Tension", self.game_state.tension, y, COLORS['critical'])
        y += 25
        self.draw_meter("Morale", self.game_state.morale, y, COLORS['morale'])
        
        # Personnel info with smaller icons
        y = meter_panel.bottom + 20  # Ensure consistent spacing after meter panel
        personnel_panel = pygame.Rect(20, y, SIDEBAR_WIDTH - 40, 140)  # Increased height to 140 for larger icons
        y = self.draw_panel(personnel_panel, "PERSONNEL")
        y += 20
        
        # Draw personnel stats in two columns with icons
        col_width = (SIDEBAR_WIDTH - 80) // 2
        left_col = 40
        right_col = left_col + col_width + 20
        row_height = 40  # Increased from 30 to 40 to accommodate larger icons
        
        # Left column
        self.draw_stat('hostage', self.game_state.hostages, left_col, y)
        y += row_height
        self.draw_stat('terrorist', self.game_state.terrorists, left_col, y)
        
        # Right column
        y -= row_height
        self.draw_stat('exit', self.game_state.exits, right_col, y)
        y += row_height
        self.draw_stat('camera', self.game_state.cameras, right_col, y)
        
        # Action Points (simplified to AP)
        y += row_height + 10
        ap_panel = pygame.Rect(20, y, SIDEBAR_WIDTH - 40, 40)  # Reduced height
        pygame.draw.rect(self.screen, COLORS['panel_bg'], ap_panel)
        pygame.draw.rect(self.screen, COLORS['panel_border'], ap_panel, 2)
        
        # Draw AP with icon and value inline
        ap_text = f"AP:{self.game_state.ap}"
        ap_value = self.main_font.render(ap_text, True, COLORS['text'])
        ap_rect = ap_value.get_rect(center=(ap_panel.centerx, ap_panel.centery))
        self.screen.blit(ap_value, ap_rect)
        
        # Game History
        y += 50
        history_panel = pygame.Rect(20, y, SIDEBAR_WIDTH - 40, WINDOW_HEIGHT - y - 20)
        y = self.draw_panel(history_panel, "GAME HISTORY")
        y += 10
        
        # Calculate maximum width for wrapped text
        max_width = SIDEBAR_WIDTH - 60  # Leave some padding
        
        # Display messages with scrolling if needed
        for msg in self.game_state.message_history[-10:]:  # Show last 10 messages
            wrapped_lines = self.wrap_text(msg, self.small_font, max_width)
            for line in wrapped_lines:
                y = self.draw_text(line, self.small_font, 30, y, COLORS['text_dim']) + 5

    def draw_radial_menu(self):
        """Draw the radial action menu."""
        if not self.show_menu:
            return

        # Calculate center of screen and menu radius
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        radius = 200 * self.menu_animation  # Increased radius for better spacing
        
        # Draw semi-transparent background
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 0, 0, 128 * self.menu_animation), (center_x, center_y), radius + 100)
        self.screen.blit(s, (0, 0))
        
        if not self.in_submenu:
            # Draw the four directional options
            directions = [
                ("NEGOTIATE", 0, ActionType.NEGOTIATE),      # Right
                ("SPECIAL", -90, ActionType.SPECIAL),      # Up
                ("TACTICAL", 180, ActionType.TACTICAL),     # Left
                ("FORCE", 90, ActionType.FORCE)          # Down
            ]
            
            for action_name, angle, action_type in directions:
                # Calculate position
                rad_angle = math.radians(angle)
                x = center_x + math.cos(rad_angle) * radius
                y = center_y + math.sin(rad_angle) * radius
                
                # Determine if this option is selected
                is_selected = (action_type == self.selected_type)
                
                # Draw selection indicator
                if is_selected:
                    pygame.draw.circle(self.screen, COLORS['panel_dark'], (int(x), int(y)), 60)
                
                # Draw text
                text_surf = self.main_font.render(action_name, True, 
                                                COLORS['highlight'] if is_selected else COLORS['text'])
                text_rect = text_surf.get_rect(center=(x, y))
                self.screen.blit(text_surf, text_rect)
        
        # If we're in a submenu, draw the actions
        if self.selected_type and self.in_submenu:
            self.draw_submenu(center_x, center_y, radius)

    def draw_submenu(self, center_x, center_y, radius):
        """Draw the submenu for the selected action type."""
        actions = self.action_system.get_actions(self.selected_type)
        if not actions:
            return
        
        # In submenu mode, draw actions in a cross pattern with increased spacing
        directions = [
            (0, -1, "Up"),    # Up
            (1, 0, "Right"),  # Right
            (0, 1, "Down"),   # Down
            (-1, 0, "Left")   # Left
        ]
        
        for i, action in enumerate(actions[:4]):
            if i >= len(directions):
                break
                
            dx, dy, _ = directions[i]
            x = center_x + dx * radius * 1.2
            y = center_y + dy * radius * 1.2
            
            # Draw selection indicator
            if i == self.selected_action:
                pygame.draw.circle(self.screen, COLORS['panel_dark'], (int(x), int(y)), 70)
            
            # Determine if action is affordable
            can_afford = self.game_state.ap >= action.ap_cost
            text_color = COLORS['highlight'] if i == self.selected_action else COLORS['text']
            if not can_afford:
                text_color = COLORS['text_dim']  # Dim color for unaffordable actions
            
            # Draw action name
            text = f"{action.name}"
            text_surf = self.main_font.render(text, True, text_color)
            text_rect = text_surf.get_rect(center=(x, y - 15))
            self.screen.blit(text_surf, text_rect)
            
            # Draw AP cost
            ap_text = f"({action.ap_cost} AP)"
            ap_surf = self.small_font.render(ap_text, True, text_color)
            ap_rect = ap_surf.get_rect(midtop=(x, y + 15))
            self.screen.blit(ap_surf, ap_rect)
            
            # Draw strikethrough for unaffordable actions
            if not can_afford:
                start_pos = (text_rect.left, text_rect.centery)
                end_pos = (text_rect.right, text_rect.centery)
                pygame.draw.line(self.screen, text_color, start_pos, end_pos, 2)
        
        # Draw selected action description in the center
        if 0 <= self.selected_action < len(actions):
            action = actions[self.selected_action]
            desc_lines = self.wrap_text(action.description, self.small_font, 300)
            y_offset = -20 * (len(desc_lines) // 2)
            for line in desc_lines:
                text_surf = self.small_font.render(line, True, COLORS['text_dim'])
                text_rect = text_surf.get_rect(center=(center_x, center_y + y_offset))
                self.screen.blit(text_surf, text_rect)
                y_offset += 25
            
            # Draw success chance
            chance_text = f"{int(action.success_chance*100)}% Success"
            chance_surf = self.small_font.render(chance_text, True, COLORS['text'])
            chance_rect = chance_surf.get_rect(center=(center_x, center_y + y_offset + 20))
            self.screen.blit(chance_surf, chance_rect)

    def draw_exit_confirmation(self):
        """Draw the exit confirmation dialog."""
        if not self.show_exit_confirm:
            return
            
        # Draw semi-transparent background
        s = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 192))  # Dark overlay
        self.screen.blit(s, (0, 0))
        
        # Draw confirmation box
        box_width = 400
        box_height = 200
        box_x = (WINDOW_WIDTH - box_width) // 2
        box_y = (WINDOW_HEIGHT - box_height) // 2
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Draw box background and border
        pygame.draw.rect(self.screen, COLORS['panel_bg'], box_rect)
        pygame.draw.rect(self.screen, COLORS['panel_border'], box_rect, 2)
        
        # Draw text
        title = "Exit Game?"
        title_surf = self.main_font.render(title, True, COLORS['text'])
        title_rect = title_surf.get_rect(centerx=WINDOW_WIDTH//2, top=box_y + 40)
        self.screen.blit(title_surf, title_rect)
        
        # Draw instructions
        confirm_text = "Press Y to exit, N to continue"
        confirm_surf = self.small_font.render(confirm_text, True, COLORS['text_dim'])
        confirm_rect = confirm_surf.get_rect(centerx=WINDOW_WIDTH//2, top=box_y + 100)
        self.screen.blit(confirm_surf, confirm_rect)

    def draw_meter(self, label, value, y, color):
        """Draw a meter with label and value."""
        # Draw label (shorter to save space)
        label_width = 60
        self.draw_text(f"{label}:", self.small_font, 30, y + 4)  # Adjusted y for better alignment
        
        # Draw meter background (adjusted position and size)
        meter_rect = pygame.Rect(label_width + 35, y, 160, 20)  # Made meter shorter and more compact
        pygame.draw.rect(self.screen, COLORS['panel_dark'], meter_rect)
        
        # Draw meter fill
        if value > 0:
            fill_width = int((value / 100) * meter_rect.width)  # Calculate width based on percentage
            fill_rect = pygame.Rect(meter_rect.left, y, fill_width, 20)
            pygame.draw.rect(self.screen, color, fill_rect)
        
        # Draw value (moved closer)
        value_text = f"{value}%"
        value_surf = self.small_font.render(value_text, True, COLORS['text'])
        value_rect = value_surf.get_rect(midleft=(meter_rect.right + 10, y + 10))
        self.screen.blit(value_surf, value_rect)

    def update_visual_effects(self):
        """Update visual effects like screen shake and flash."""
        # Update screen shake - reduced intensity
        if self.screen_shake > 0:
            self.screen_shake -= 1
            if self.screen_shake > 0:
                self.shake_offset = (
                    random.randint(-2, 2),  # Reduced from -5,5 to -2,2
                    random.randint(-2, 2)
                )
            else:
                self.shake_offset = (0, 0)
        
        # Update flash effect - faster fade
        if self.flash_timer > 0:
            self.flash_timer -= 2  # Faster fade
        
        # Update AP warning message
        if self.ap_warning_timer > 0:
            self.ap_warning_timer -= 1

    def trigger_ap_feedback(self, action_name):
        """Trigger visual feedback for insufficient AP."""
        self.screen_shake = 3  # Even shorter shake duration
        self.flash_timer = 3   # Even shorter flash duration
        self.ap_warning_timer = 60  # Show warning for 1 second (60 frames)
        self.ap_warning_text = f"Insufficient AP for {action_name}!"
        # Add message to game history
        self.game_state.add_message(f"Not enough AP to perform {action_name}")

    def handle_input(self):
        """Handle user input."""
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.show_exit_confirm = True
                return True
            
            if event.type == pygame.KEYDOWN:
                # Handle exit confirmation dialog
                if self.show_exit_confirm:
                    if event.key == pygame.K_y:
                        return False
                    elif event.key == pygame.K_n:
                        self.show_exit_confirm = False
                    return True
                
                # Normal input handling
                if event.key == pygame.K_ESCAPE:
                    if self.in_submenu:
                        self.in_submenu = False
                    elif self.show_menu:
                        self.show_menu = False
                        self.selected_type = None
                
                elif event.key == pygame.K_q:
                    self.show_exit_confirm = True
                
                elif event.key == pygame.K_SPACE:
                    if not self.show_menu:
                        self.show_menu = True
                        self.menu_animation = 0
                        self.last_menu_time = current_time
                        self.selected_type = None
                        self.in_submenu = False
                    elif self.selected_type and not self.in_submenu:
                        self.in_submenu = True
                    elif self.in_submenu:
                        # Execute selected action
                        actions = self.action_system.get_actions(self.selected_type)
                        if actions and self.selected_action < len(actions):
                            action = actions[self.selected_action]
                            if self.game_state.ap < action.ap_cost:
                                self.trigger_ap_feedback(action.name)
                            else:
                                success, msg = self.action_system.execute_action(action, self.game_state)
                                self.show_menu = False
                                self.in_submenu = False
                                if self.game_state.ap <= 0:
                                    self.end_turn()
                
                elif self.show_menu:
                    if not self.in_submenu:
                        # Main menu navigation
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.selected_type = ActionType.SPECIAL
                            self.selected_action = 0
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected_type = ActionType.FORCE
                            self.selected_action = 0
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.selected_type = ActionType.TACTICAL
                            self.selected_action = 0
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.selected_type = ActionType.NEGOTIATE
                            self.selected_action = 0
                    else:
                        # Submenu navigation
                        actions = self.action_system.get_actions(self.selected_type)
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.selected_action = 0
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.selected_action = 1
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.selected_action = 2
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.selected_action = 3
                        # Ensure selected_action is valid
                        self.selected_action = min(self.selected_action, len(actions) - 1)
        
        # Update menu animation
        if self.show_menu and self.menu_animation < 1:
            self.menu_animation = min(1, (current_time - self.last_menu_time) / 200)
        elif not self.show_menu and self.menu_animation > 0:
            self.menu_animation = max(0, 1 - (current_time - self.last_menu_time) / 200)
        
        return True
    
    def end_turn(self):
        """Process end of turn."""
        self.game_state.turn += 1
        self.game_state.ap = 3
        self.show_menu = False
    
    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()
        main_surface = pygame.display.get_surface()
        
        while running:
            # Handle input
            running = self.handle_input()
            
            # Update effects
            self.update_visual_effects()
            
            # Create a fresh surface for this frame
            self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            
            # Draw
            self.screen.fill(COLORS['background'])
            
            # Draw game elements
            self.draw_status()
            self.draw_radial_menu()
            self.draw_exit_confirmation()
            
            # Draw flash effect - more transparent
            if self.flash_timer > 0:
                flash_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 0, 0, min(64, self.flash_timer * 12)))
                self.screen.blit(flash_surface, (0, 0))
            
            # Draw AP warning message
            if self.ap_warning_timer > 0:
                warning_surf = self.main_font.render(self.ap_warning_text, True, COLORS['critical'])
                warning_rect = warning_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 100))
                # Draw semi-transparent background for better readability
                bg_rect = warning_rect.inflate(20, 10)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 128))
                self.screen.blit(bg_surface, bg_rect)
                self.screen.blit(warning_surf, warning_rect)
            
            # Apply screen shake and update display
            if self.screen_shake > 0:
                main_surface.blit(self.screen, self.shake_offset)
            else:
                main_surface.blit(self.screen, (0, 0))
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit() 