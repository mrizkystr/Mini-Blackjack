"""Card, Hand, and Deck classes for Blackjack."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Suit(Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Rank(Enum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


RANK_DISPLAY: dict[Rank, str] = {
    Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
    Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
    Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K",
    Rank.ACE: "A",
}

SUIT_SYMBOL: dict[Suit, str] = {
    Suit.HEARTS: "♥", Suit.DIAMONDS: "♦",
    Suit.CLUBS: "♣", Suit.SPADES: "♠",
}

SUIT_COLOR: dict[Suit, str] = {
    Suit.HEARTS: "red", Suit.DIAMONDS: "red",
    Suit.CLUBS: "black", Suit.SPADES: "black",
}


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def blackjack_value(self) -> int:
        """Non-ace face value for Blackjack (Ace handled separately)."""
        if self.rank == Rank.ACE:
            return 11
        if self.rank.value >= 10:  # 10, J, Q, K
            return 10
        return self.rank.value

    @property
    def is_ace(self) -> bool:
        return self.rank == Rank.ACE

    @property
    def display(self) -> str:
        return f"{RANK_DISPLAY[self.rank]}{SUIT_SYMBOL[self.suit]}"

    def __repr__(self) -> str:
        return self.display


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)

    def add(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def value(self) -> int:
        total = sum(c.blackjack_value for c in self.cards)
        aces = sum(1 for c in self.cards if c.is_ace)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def is_bust(self) -> bool:
        return self.value > 21

    @property
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.value == 21

    def clear(self) -> None:
        self.cards.clear()

    def __len__(self) -> int:
        return len(self.cards)


class Deck:
    def __init__(self) -> None:
        self._cards: list[Card] = []
        self.reset()

    def reset(self) -> None:
        self._cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self) -> None:
        random.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            self.reset()
        return self._cards.pop()

    @property
    def remaining(self) -> int:
        return len(self._cards)
