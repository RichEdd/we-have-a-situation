# We Have a Situation

A turn-based hostage negotiation simulator that puts players in the roles of either hostage negotiators or hostage takers. Experience intense psychological warfare, resource management, and strategic decision-making in various realistic scenarios.

## Features

- **Turn-based Gameplay**: Strategic decision-making with no real-time pressure
- **Psychological Warfare**: Complex dialogue system with various approaches (empathy, threats, deception, etc.)
- **Resource Management**: Manage your available assets and personnel
- **Multiple Scenarios**: Different locations with unique challenges and characteristics
- **Hidden Objectives**: Each side has secret goals they must achieve
- **Dynamic Environment**: Location features affect gameplay strategies
- **Affiliation System**: Choose from different organizations with unique advantages

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/we-have-a-situation.git
cd we-have-a-situation
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

To start the game, run:
```bash
python src/main.py
```

## Game Structure

- `src/core/`: Core game mechanics and systems
  - `game_engine.py`: Main game logic and state management
  - `dialogue_system.py`: Dialogue and negotiation mechanics
- `src/scenarios/`: Game scenarios and locations
  - `base_scenario.py`: Base scenario class and scenario definitions
- `src/entities/`: Game entities (players, hostages, etc.)
- `src/utils/`: Utility functions and helpers

## Development Status

This is currently a prototype version focusing on core mechanics. Future development plans include:

- [ ] 3D graphics and animations
- [ ] More sophisticated AI behavior
- [ ] Additional scenarios and locations
- [ ] Extended dialogue options
- [ ] Multiplayer support
- [ ] Save/Load game functionality
- [ ] Tutorial system
- [ ] Achievement system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 