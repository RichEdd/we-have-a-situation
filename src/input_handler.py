import pygame
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

class InputType(Enum):
    KEYBOARD = auto()
    CONTROLLER = auto()

class InputHandler:
    def __init__(self):
        # Input settings
        self.input_cooldown = 150  # ms
        self.last_input_time = 0
        self.stick_deadzone = 0.2
        
        # Controller state
        self.controller = None
        self.input_type = InputType.KEYBOARD
        
        # Initialize controller if available
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            self.input_type = InputType.CONTROLLER
    
    def _check_cooldown(self) -> bool:
        """Check if enough time has passed since last input."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_input_time >= self.input_cooldown:
            self.last_input_time = current_time
            return True
        return False
    
    def get_dpad_values(self) -> Tuple[int, int]:
        """Get D-pad input values."""
        if not self.controller:
            return (0, 0)
        
        # Get D-pad values
        try:
            x = self.controller.get_hat(0)[0]  # -1 (left) to 1 (right)
            y = -self.controller.get_hat(0)[1]  # -1 (up) to 1 (down)
            return (x, y)
        except pygame.error:
            return (0, 0)
    
    def get_stick_values(self) -> Tuple[float, float]:
        """Get analog stick input values with deadzone."""
        if not self.controller:
            return (0.0, 0.0)
        
        try:
            # Get raw stick values
            x = self.controller.get_axis(0)  # -1 (left) to 1 (right)
            y = self.controller.get_axis(1)  # -1 (up) to 1 (down)
            
            # Apply deadzone
            x = 0.0 if abs(x) < self.stick_deadzone else x
            y = 0.0 if abs(y) < self.stick_deadzone else y
            
            return (x, y)
        except pygame.error:
            return (0.0, 0.0)
    
    def get_movement(self) -> Tuple[int, int]:
        """Get combined keyboard/controller movement."""
        x, y = 0, 0
        
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            x = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            y = 1
        
        # Check controller if no keyboard input
        if x == 0 and y == 0 and self.controller:
            # Check D-pad first
            x, y = self.get_dpad_values()
            
            # If no D-pad input, check stick
            if x == 0 and y == 0:
                stick_x, stick_y = self.get_stick_values()
                x = int(round(stick_x)) if abs(stick_x) > self.stick_deadzone else 0
                y = int(round(stick_y)) if abs(stick_y) > self.stick_deadzone else 0
        
        return (x, y)
    
    def get_action_press(self) -> bool:
        """Check for action button press (Enter/Space/A)."""
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            return True
        
        # Check controller
        if self.controller:
            try:
                return self.controller.get_button(0)  # A button
            except pygame.error:
                pass
        
        return False
    
    def get_cancel_press(self) -> bool:
        """Check for cancel button press (Esc/B)."""
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return True
        
        # Check controller
        if self.controller:
            try:
                return self.controller.get_button(1)  # B button
            except pygame.error:
                pass
        
        return False
    
    def get_special_press(self) -> bool:
        """Check for special button press (Tab/Y)."""
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_TAB]:
            return True
        
        # Check controller
        if self.controller:
            try:
                return self.controller.get_button(3)  # Y button
            except pygame.error:
                pass
        
        return False
    
    def get_fullscreen_press(self) -> bool:
        """Check for fullscreen toggle press (F11)."""
        keys = pygame.key.get_pressed()
        return keys[pygame.K_F11]
    
    def update_input_type(self, event: pygame.event.Event):
        """Update the current input type based on the event."""
        if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
            self.input_type = InputType.KEYBOARD
        elif event.type in [pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION]:
            self.input_type = InputType.CONTROLLER 