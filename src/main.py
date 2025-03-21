#!/usr/bin/env python3
"""
We Have a Situation! - A Tactical Hostage Negotiation Game
"""

import sys
import os
import pygame
from simple_ui import SimpleUI

def main():
    """Main entry point."""
    # Initialize Pygame
    pygame.init()
    pygame.joystick.init()
    
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize and run the game
    ui = SimpleUI()
    ui.run()

if __name__ == "__main__":
    main() 