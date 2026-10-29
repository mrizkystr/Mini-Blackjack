"""Player and Dealer participants."""

from __future__ import annotations

from game.cards import Hand, Card


class Player:
    def __init__(self, name: str = "Player") -> None:
        self.name = name
        self.hand = Hand()

    def receive(self, card: Card) -> None:
        self.hand.add(card)

    def clear_hand(self) -> None:
        self.hand.clear()

    @property
    def value(self) -> int:
        return self.hand.value

    @property
    def is_bust(self) -> bool:
        return self.hand.is_bust

    @property
    def has_blackjack(self) -> bool:
        return self.hand.is_blackjack


class Dealer(Player):
    def __init__(self) -> None:
        super().__init__(name="Dealer")

    def should_hit(self) -> bool:
        """Dealer must hit on 16 or below, stand on 17+."""
        return self.value < 17
