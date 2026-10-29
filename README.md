# Mini Blackjack

A lightweight single-player Blackjack card game built with Python and Pygame. Features a minimalist dark casino aesthetic, card deal animations, responsive window resizing, and session statistics.

## Features

- Classic Blackjack rules against a dealer
- Polished card rendering with suit colors (red/black) and card-back design
- Card dealing animations with eased motion
- Button hover feedback and result fade-in effects
- Resizable window with proportional scaling
- Win/Loss/Push session statistics
- Natural Blackjack detection and immediate resolution

## Technologies

- Python 3.11+
- Pygame 2.5+

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd Mini-Blackjack

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## How to Run

```bash
python main.py
```

## Game Controls

| Action        | Input              |
|---------------|--------------------|
| **Hit**       | Click the Hit button — draw another card |
| **Stand**     | Click the Stand button — end your turn |
| **New Round** | Click New Round after a result is shown |

Buttons are disabled when the corresponding action is unavailable.

## Blackjack Rules

- Beat the dealer by getting closer to 21 without going over.
- Number cards are worth their face value.
- Face cards (J, Q, K) are worth 10.
- Aces count as 11 or 1, whichever avoids busting.
- Dealer must hit on 16 or below and stands on 17+.
- Natural Blackjack (Ace + 10-value on first two cards) wins immediately, unless the dealer also has one (push).

## Running Tests

```bash
# Using unittest
python -m unittest discover -s tests -v

# Or with pytest (if installed)
python -m pytest tests/ -v
```
