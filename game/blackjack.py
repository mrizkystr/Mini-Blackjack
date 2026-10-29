"""Blackjack game logic and state management."""

from __future__ import annotations

from enum import Enum, auto

from game.cards import Deck
from game.player import Player, Dealer


class GameState(Enum):
    INITIAL = auto()
    PLAYER_TURN = auto()
    DEALER_TURN = auto()
    ROUND_OVER = auto()


class RoundResult(Enum):
    PLAYER_WIN = "You win!"
    DEALER_WIN = "Dealer wins!"
    PUSH = "Push!"
    PLAYER_BLACKJACK = "Blackjack! You win!"
    PLAYER_BUST = "Bust! Dealer wins!"
    DEALER_BUST = "Dealer busts! You win!"


class BlackjackGame:
    def __init__(self) -> None:
        self.deck = Deck()
        self.player = Player()
        self.dealer = Dealer()
        self.state = GameState.INITIAL
        self.result: RoundResult | None = None
        # Session statistics
        self.wins = 0
        self.losses = 0
        self.pushes = 0

    def new_round(self) -> None:
        """Start a new round: reset hands, deal two cards each."""
        self.player.clear_hand()
        self.dealer.clear_hand()
        self.result = None

        if self.deck.remaining < 15:
            self.deck.reset()

        for _ in range(2):
            self.player.receive(self.deck.draw())
            self.dealer.receive(self.deck.draw())

        # Check for natural blackjacks
        if self.player.has_blackjack or self.dealer.has_blackjack:
            self.state = GameState.ROUND_OVER
            self.result = self._resolve_blackjacks()
            self._record_result()
        else:
            self.state = GameState.PLAYER_TURN

    def _record_result(self) -> None:
        """Update session statistics based on round result."""
        if self.result is None:
            return
        if self.result in (
            RoundResult.PLAYER_WIN,
            RoundResult.PLAYER_BLACKJACK,
            RoundResult.DEALER_BUST,
        ):
            self.wins += 1
        elif self.result == RoundResult.PUSH:
            self.pushes += 1
        else:
            self.losses += 1

    def player_hit(self) -> None:
        """Player draws a card."""
        if self.state != GameState.PLAYER_TURN:
            return
        self.player.receive(self.deck.draw())
        if self.player.is_bust:
            self.state = GameState.ROUND_OVER
            self.result = RoundResult.PLAYER_BUST
            self._record_result()

    def player_stand(self) -> None:
        """Player ends their turn; dealer plays."""
        if self.state != GameState.PLAYER_TURN:
            return
        self.state = GameState.DEALER_TURN
        self._dealer_play()

    def _dealer_play(self) -> None:
        """Dealer draws until 17+."""
        while self.dealer.should_hit():
            self.dealer.receive(self.deck.draw())

        self.state = GameState.ROUND_OVER

        if self.dealer.is_bust:
            self.result = RoundResult.DEALER_BUST
        else:
            self.result = self._compare_hands()

        self._record_result()

    def _resolve_blackjacks(self) -> RoundResult:
        if self.player.has_blackjack and self.dealer.has_blackjack:
            return RoundResult.PUSH
        if self.player.has_blackjack:
            return RoundResult.PLAYER_BLACKJACK
        return RoundResult.DEALER_WIN

    def _compare_hands(self) -> RoundResult:
        pv, dv = self.player.value, self.dealer.value
        if pv > dv:
            return RoundResult.PLAYER_WIN
        if dv > pv:
            return RoundResult.DEALER_WIN
        return RoundResult.PUSH

    @property
    def is_player_turn(self) -> bool:
        return self.state == GameState.PLAYER_TURN

    @property
    def is_round_over(self) -> bool:
        return self.state == GameState.ROUND_OVER

    @property
    def show_dealer_hole(self) -> bool:
        """Whether the dealer's hidden card should be revealed."""
        return self.state in (GameState.DEALER_TURN, GameState.ROUND_OVER)
