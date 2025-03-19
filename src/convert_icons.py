import pygame
import os

def create_icon(name, size=24, color=(0, 255, 170)):
    """Create an icon using pygame primitives."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    if name == 'hostage':
        # Draw a person figure
        center = size // 2
        head_radius = size // 6
        body_height = size // 2
        
        # Head
        pygame.draw.circle(surface, color, (center, center - body_height//3), head_radius)
        
        # Body
        pygame.draw.line(surface, color, 
                        (center, center - body_height//3 + head_radius),
                        (center, center + body_height//2), 2)
        
        # Arms
        pygame.draw.line(surface, color,
                        (center - size//4, center),
                        (center + size//4, center), 2)
        
        # Legs
        pygame.draw.line(surface, color,
                        (center, center + body_height//2),
                        (center - size//4, center + body_height), 2)
        pygame.draw.line(surface, color,
                        (center, center + body_height//2),
                        (center + size//4, center + body_height), 2)
    
    elif name == 'terrorist':
        # Draw a threatening figure
        center = size // 2
        head_radius = size // 6
        body_height = size // 2
        
        # Head
        pygame.draw.circle(surface, color, (center, center - body_height//3), head_radius)
        
        # Body (wider)
        pygame.draw.line(surface, color, 
                        (center, center - body_height//3 + head_radius),
                        (center, center + body_height//2), 3)
        
        # Arms (raised)
        pygame.draw.line(surface, color,
                        (center - size//4, center - size//6),
                        (center + size//4, center - size//6), 2)
        
        # Legs (wider stance)
        pygame.draw.line(surface, color,
                        (center, center + body_height//2),
                        (center - size//3, center + body_height), 2)
        pygame.draw.line(surface, color,
                        (center, center + body_height//2),
                        (center + size//3, center + body_height), 2)
    
    elif name == 'camera':
        # Draw a surveillance camera
        margin = size // 6
        body_width = size - 2 * margin
        body_height = size // 2
        center = size // 2
        
        # Camera body
        pygame.draw.rect(surface, color, 
                        (margin, center - body_height//2,
                         body_width, body_height))
        
        # Lens
        pygame.draw.circle(surface, color, 
                         (size - margin, center),
                         size//6)
        
        # Mount
        pygame.draw.rect(surface, color,
                        (margin, size - margin,
                         size//4, margin//2))
    
    elif name == 'exit':
        # Draw an exit sign
        margin = size // 6
        arrow_size = size // 2
        
        # Door frame
        pygame.draw.rect(surface, color,
                        (margin, margin,
                         size - 2*margin, size - 2*margin), 2)
        
        # Arrow
        points = [
            (size//2 - arrow_size//2, size//2),
            (size//2 + arrow_size//2, size//2),
            (size//2, size//2 - arrow_size//2)
        ]
        pygame.draw.polygon(surface, color, points)
    
    return surface

def main():
    """Create and save all icons."""
    pygame.init()
    
    # Ensure Assets directory exists
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Assets')
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    # Create icons
    icons = ['hostage', 'terrorist', 'camera', 'exit']
    size = 24
    color = (0, 255, 170)  # Bright cyan color
    
    for name in icons:
        icon = create_icon(name, size, color)
        path = os.path.join(assets_dir, f'{name}.png')
        pygame.image.save(icon, path)
        print(f'Created {path}')

if __name__ == '__main__':
    main() 