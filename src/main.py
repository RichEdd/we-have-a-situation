#!/usr/bin/env python3
"""
We Have a Situation! - A Tactical Hostage Negotiation Game
"""

import sys
import os
from tactical_ui import TacticalUI

def main():
    """Main entry point."""
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize and run the game
    ui = TacticalUI()
    ui.run()

if __name__ == "__main__":
    main() 