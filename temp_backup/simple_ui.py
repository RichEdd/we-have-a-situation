import pygame
import sys

class SimpleUI:
    def __init__(self):
        # Initialize Pygame and other components
        self.screen = pygame.display.set_mode((1920, 1080))
        pygame.display.set_caption("Crisis Negotiator")
        self.main_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.show_exit_confirm = False  # Track if the exit confirmation screen is active

    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()

        while running:
            # Handle input
            running = self.handle_input()

            # Draw the game or exit confirmation screen
            self.screen.fill((10, 20, 30))  # Background color
            if self.show_exit_confirm:
                self.draw_exit_confirmation()
            else:
                self.draw_game_ui()

            # Update the display
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_input(self):
        """Handle user input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:  # Change exit key to Q
                    self.show_exit_confirm = True  # Show exit confirmation screen
                elif event.key == pygame.K_y and self.show_exit_confirm:  # Confirm exit
                    return False
                elif event.key == pygame.K_n and self.show_exit_confirm:  # Cancel exit
                    self.show_exit_confirm = False

        return True

    def draw_game_ui(self):
        """Draw the main game UI."""
        # Example placeholder for the game UI
        text = self.main_font.render("Game is running. Press Q to exit.", True, (255, 255, 255))
        text_rect = text.get_rect(center=(960, 540))
        self.screen.blit(text, text_rect)

    def draw_exit_confirmation(self):
        """Draw the exit confirmation screen."""
        # Draw semi-transparent background
        overlay = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with transparency
        self.screen.blit(overlay, (0, 0))

        # Draw confirmation text
        text = self.main_font.render("Are you sure you want to quit? (Y/N)", True, (255, 255, 255))
        text_rect = text.get_rect(center=(960, 540))
        self.screen.blit(text, text_rect)