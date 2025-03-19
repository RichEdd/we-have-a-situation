import pygame
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

class InputType(Enum):
    KEYBOARD = auto()
    CONTROLLER = auto()

class InputHandler:
    """Handles input from both keyboard and controller."""
    
    def __init__(self):
        # Initialize state variables
        self.x_movement = 0
        self.y_movement = 0
        self.action_pressed = False
        self.cancel_pressed = False
        self.special_pressed = False
        
        # Input settings
        self.dead_zone = 0.5  # Increased from 0.2
        self.cooldown = 200  # Increased from 150ms
        self.last_input_time = 0
        
        # Track last used input type
        self.last_input_type = None  # 'keyboard' or 'controller'
        
        # Initialize controller if available
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            self.input_type = InputType.CONTROLLER
    
    def _check_cooldown(self) -> bool:
        """Check if enough time has passed since last input."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_input_time >= self.cooldown:
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
            x = 0.0 if abs(x) < self.dead_zone else x
            y = 0.0 if abs(y) < self.dead_zone else y
            
            return (x, y)
        except pygame.error:
            return (0.0, 0.0)
    
    def update_input_type(self, event):
        """Update the last used input type based on event."""
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            self.last_input_type = 'keyboard'
        elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, 
                          pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
            self.last_input_type = 'controller'
    
    def get_movement(self) -> Tuple[int, int]:
        """Get movement input from keyboard or controller.
        Returns:
            Tuple[int, int]: (x, y) movement values (-1, 0, or 1)
        """
        current_time = pygame.time.get_ticks()
        
        # Reset movement if enough time has passed
        if current_time - self.last_input_time >= self.cooldown:
            self.x_movement = 0
            self.y_movement = 0
            
            # Check keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x_movement = -1
                self.last_input_time = current_time
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x_movement = 1
                self.last_input_time = current_time
            
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.y_movement = -1  # Up is negative
                self.last_input_time = current_time
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.y_movement = 1  # Down is positive
                self.last_input_time = current_time
            
            # Check controller input
            for joy in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]:
                # D-pad
                hat = joy.get_hat(0)
                if hat[0] != 0:  # Left/Right
                    self.x_movement = hat[0]
                    self.last_input_time = current_time
                if hat[1] != 0:  # Up/Down
                    self.y_movement = -hat[1]  # Invert Y axis to match keyboard
                    self.last_input_time = current_time
                
                # Analog stick
                x_axis = joy.get_axis(0)
                y_axis = joy.get_axis(1)
                
                if abs(x_axis) > self.dead_zone:
                    self.x_movement = 1 if x_axis > 0 else -1
                    self.last_input_time = current_time
                
                if abs(y_axis) > self.dead_zone:
                    self.y_movement = 1 if y_axis > 0 else -1  # Y axis is already inverted
                    self.last_input_time = current_time
        
        return self.x_movement, self.y_movement
    
    def get_action_press(self) -> bool:
        """Check if action button (Enter/Space/A) is pressed."""
        self.action_pressed = False
        
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            self.action_pressed = True
        
        # Check controller
        for joy in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]:
            if joy.get_button(0):  # A button
                self.action_pressed = True
        
        return self.action_pressed
    
    def get_cancel_press(self) -> bool:
        """Check if cancel button (Esc/B) is pressed."""
        self.cancel_pressed = False
        
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.cancel_pressed = True
        
        # Check controller
        for joy in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]:
            if joy.get_button(1):  # B button
                self.cancel_pressed = True
        
        return self.cancel_pressed
    
    def get_special_press(self) -> bool:
        """Check if special ability button (Y) is pressed."""
        self.special_pressed = False
        
        # Check keyboard
        keys = pygame.key.get_pressed()
        if keys[pygame.K_y]:
            self.special_pressed = True
        
        # Check controller
        for joy in [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]:
            if joy.get_button(3):  # Y button
                self.special_pressed = True
        
        return self.special_pressed
    
    def get_fullscreen_press(self) -> bool:
        """Check for fullscreen toggle press (F11)."""
        keys = pygame.key.get_pressed()
        return keys[pygame.K_F11] 