# We Have a Situation!

A tactical hostage negotiation game where you play as one of three law enforcement agencies (FBI, CIA, or Local PD) managing a crisis situation. Make strategic decisions, manage resources, and navigate tense negotiations to achieve the best possible outcome.

## Features

- Three playable factions with unique abilities
- Six action categories: Dialogue, Resources, Force, Tech, Negotiation, and Threats
- Dynamic trust and tension system
- Resource management
- Tactical positioning
- Turn-based gameplay with action points
- Modern tactical UI with keyboard and controller support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whas.git
cd whas
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

Start the game by running:
```bash
python src/main.py
```

## Controls

### Keyboard
- Arrow keys / WASD: Navigate menus
- Enter / Space: Confirm selection
- Escape: Back / Cancel
- Tab: Special abilities menu
- F11: Toggle fullscreen

### Controller
- D-pad / Left stick: Navigate menus
- A: Confirm selection
- B: Back / Cancel
- Y: Special abilities menu

## Gameplay

1. Select your faction (FBI, CIA, or Local PD)
2. Each turn you have 3 action points to spend
3. Choose actions from six categories:
   - Dialogue: Communicate with hostage takers
   - Resources: Manage personnel and equipment
   - Force: Position tactical units
   - Tech: Deploy surveillance and technical solutions
   - Negotiation: Work towards peaceful resolution
   - Threats: Apply pressure when needed
4. Monitor trust level, tension, and intel
5. Complete objectives while maintaining control of the situation

## Development

The game is built with Python and Pygame. Key components:

- `src/tactical_ui.py`: Main game interface
- `src/core/game_state.py`: Game state management
- `src/core/dialogue_system.py`: Action and dialogue systems
- `src/input_handler.py`: Keyboard and controller input

## License

This project is licensed under the MIT License - see the LICENSE file for details. 