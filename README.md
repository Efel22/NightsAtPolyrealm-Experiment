# NightsAtPolyrealm-Experimental



## Overview

This project is a first-person action-RPG framework built entirely in Python using the **Ursina Engine**. It aims to integrate procedural world generation mechanics with dynamic entity systems and structured player progression. The core focus is on creating scalable, interconnected gameplay loops (exploration, combat, and growth) within an infinite, noise-driven environment.

## System Architecture

### 🌍 World & Biome Generation
* **Procedural Terrain:** Infinite, chunk-based terrain using Perlin noise.
* **Biome Logic:** Includes Ocean, Beach, Forest, Desert, Taiga, Aspen, and Mountain biomes with localized vegetation and tree placement.
* **Dynamic Environment:** Integrated day/night cycle that scales enemy spawn intervals and difficulty based on the `night_tracker`.

### 👾 Entity AI & Spawning
* **Modular AI Archetypes:** Specialized enemy behaviors including:
    * **Turrets:** Stationary ranged units.
    * **Summoners:** Entities that generate reinforcements during combat.
    * **Tanks/Chasers:** Pathfinding-based units with varied health and speed.
* **Structure Integration:** World-spawned structures that act as localized spawn points for enemies.

### ⚔️ Player Mechanics
* **Progression System:** XP-driven leveling that triggers ability selection and stat increases.
* **Combat Framework:** Swappable melee and ranged weapon classes with distinct logic (e.g., Sword/Bow).
* **Ability Manager:** Handles passive buffs and active movement skills like Double Jump.
* **State Management:** Integrated health, stamina, and "safe spawn" logic to handle player death and world repositioning.

### 🛠️ Utilities
* **Audio:** Basic `play_sound` implementation for game events (jumps, hits, etc.).
* **UI:** Functional HUD for player stats (XP, health, stamina) and death screens.

## Installation & Running

### Prerequisites
* [Python 3.7+](https://www.python.org/downloads/)
* [Ursina Engine](https://www.ursinaengine.org/)


### Quick Start

Run the project by launching:

```bash
python main.py
```

# NightsAtPolyrealm-Experiment
Procedural FPS-RPG in Ursina. Features noise-based biomes, structure-linked spawning, modular AI archetypes, and an XP-driven ability/weapon progression system.