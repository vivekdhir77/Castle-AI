# Palace Card Game Implementation

![Training and Test Run](Train_Text.mov)

This repository contains two implementations of the Palace card game: a traditional player-vs-computer version (`main.py`) and an AI-powered version using Deep Q-Learning (`palace_dqn.py`).

## Overview

Palace is a card game where players aim to get rid of all their cards by playing them onto a central pile. Each player starts with:
- 3 face-down cards (unknown)
- 3 face-up cards (visible to all)
- 3 cards in hand

## Files

### main.py
A traditional implementation of the Palace card game featuring:

- Human vs Human gameplay
- Human vs Computer gameplay (with basic AI)
- Complete rule implementation including:
  - Special card effects (2, 7, 10)
  - Hand management
  - Face-down card mechanics
  - Pile pickup rules

Key Features:
- Interactive command-line interface
- Card validation and rule enforcement
- Flexible game modes
- Deck management and card distribution
- Turn-based gameplay system

### palace_dqn.py
An advanced implementation using Deep Q-Learning Neural Networks featuring:

- Sophisticated AI agents that learn through gameplay
- Deep Q-Network (DQN) architecture with:
  - Input Layer: 91 neurons
  - Hidden Layer 1: 128 neurons (ReLU)
  - Hidden Layer 2: 64 neurons (ReLU)
  - Output Layer: 3 neurons

Key Features:
- State representation (91-dimensional vector)
- Experience replay memory
- ε-greedy exploration strategy
- Reward system for reinforcement learning
- PyTorch implementation of neural networks

## Requirements

numpy
pytorch




## Usage

### Traditional Game (main.py)



Follow the prompts to:
1. Choose game mode (Human vs Human or Human vs Computer)
2. Play cards by entering suit and rank
3. Choose to pick up pile when necessary

### AI Training (palace_dqn.py)

This will:
1. Initialize two AI agents
2. Train them through 1000 episodes
3. Display final test game results

## Game Rules

1. Players must play cards of equal or higher rank than the top card
2. Special cards:
   - 2: Resets pile, play again
   - 7: Next player must play 7 or lower
   - 10: Burns pile, play again

3. Card hierarchy:
   - 2-10: Face value
   - Jack: 11
   - Queen: 12
   - King: 13
   - Ace: 14
   - Joker: 15

## AI Implementation Details

### State Representation
- 15 dimensions × 3 types for Player 1
- 15 dimensions × 3 types for Player 2
- 15 dimensions for pile top card
- 1 dimension for special rules

### Reinforcement Learning Parameters
- Learning Rate (α): 0.001
- Discount Factor (γ): 0.99
- Initial Exploration Rate (ε): 1.0
- Exploration Decay: 0.995
- Minimum Exploration: 0.01

### Reward Structure
- +10: Winning the game
- +1: Valid play
- -5: Invalid play
- -10: Picking up pile