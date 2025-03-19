import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    def __init__(self):
        self.config_dir = Path.home() / '.whas'
        self.config_file = self.config_dir / 'config.json'
        self.default_config = {
            'window': {
                'x': None,  # None means center on screen
                'y': None,
                'width': 1920,
                'height': 1080,
                'fullscreen': False
            },
            'controls': {
                'stick_deadzone': 0.5,
                'input_cooldown': 150
            }
        }
        self.current_config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if it doesn't exist."""
        try:
            if not self.config_dir.exists():
                self.config_dir.mkdir(parents=True)
            
            if not self.config_file.exists():
                return self.save_config(self.default_config)
            
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.current_config = config
            return config
        except Exception as e:
            print(f"Error saving config: {e}")
            return self.default_config.copy()
    
    def get_window_pos(self) -> Optional[tuple[int, int]]:
        """Get the saved window position."""
        x = self.current_config['window']['x']
        y = self.current_config['window']['y']
        if x is not None and y is not None:
            return (x, y)
        return None
    
    def save_window_pos(self, x: int, y: int):
        """Save the current window position."""
        self.current_config['window']['x'] = x
        self.current_config['window']['y'] = y
        self.save_config(self.current_config)
    
    def get_window_size(self) -> tuple[int, int]:
        """Get the window size."""
        return (
            self.current_config['window']['width'],
            self.current_config['window']['height']
        )
    
    def is_fullscreen(self) -> bool:
        """Check if fullscreen mode is enabled."""
        return self.current_config['window']['fullscreen']
    
    def set_fullscreen(self, fullscreen: bool):
        """Set fullscreen mode."""
        self.current_config['window']['fullscreen'] = fullscreen
        self.save_config(self.current_config)
    
    def get_control_settings(self) -> Dict[str, float]:
        """Get control-related settings."""
        return self.current_config['controls'] 