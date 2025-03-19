import os
import pygame
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from io import BytesIO

class IconManager:
    def __init__(self, icon_size=24):
        self.icon_size = icon_size
        self.icons = {}
        print("\n=== Icon Manager Initialization ===")
        print(f"Icon size: {icon_size}x{icon_size}")
        # Get the absolute path to the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Project root: {self.project_root}")
        print(f"Current file: {__file__}")
        self.load_icons()
    
    def load_svg(self, path, size):
        """Load an SVG file and convert it to a Pygame surface."""
        print(f"\nAttempting to load SVG: {path}")
        try:
            if not os.path.exists(path):
                print(f"File not found: {path}")
                return None

            # Convert SVG to ReportLab graphics
            drawing = svg2rlg(path)
            if drawing is None:
                print(f"Failed to convert SVG: {path}")
                return None

            # Convert to PNG in memory
            bio = BytesIO()
            renderPM.drawToFile(drawing, bio, fmt="PNG", dpi=72 * (size / drawing.width))
            bio.seek(0)

            # Load into pygame
            image = pygame.image.load(bio)
            scaled = pygame.transform.scale(image, (size, size))
            print(f"SVG loaded and scaled successfully")
            return scaled
            
        except Exception as e:
            print(f"Error loading SVG {path}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_icons(self):
        """Load all icon images."""
        print("\n=== Loading Icons ===")
        icon_files = {
            'hostage': os.path.join(self.project_root, 'Assets', 'hostage.svg'),
            'terrorist': os.path.join(self.project_root, 'Assets', 'terrorist.svg'),
            'camera': os.path.join(self.project_root, 'Assets', 'camera.svg'),
            'exit': os.path.join(self.project_root, 'Assets', 'exit.svg'),
            'ap': None  # We'll keep the Unicode lightning bolt for AP
        }
        
        # Print current working directory and project root
        print(f"Current working directory: {os.getcwd()}")
        print(f"Project root directory: {self.project_root}")
        
        for name, path in icon_files.items():
            if path:
                print(f"\nLoading {name} icon from {path}")
                self.icons[name] = self.load_svg(path, self.icon_size)
                if self.icons[name] is None:
                    print(f"Failed to load {name} icon")
                else:
                    print(f"Successfully loaded {name} icon")
            else:
                self.icons[name] = None
    
    def get_icon(self, name):
        """Get the icon surface for the given name."""
        icon = self.icons.get(name)
        if icon is None:
            print(f"Warning: No icon found for {name}")
        return icon