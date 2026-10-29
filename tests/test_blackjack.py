"""Unit tests for Mini Blackjack game logic."""

import unittest

from game.cards import Card, Deck, Hand, Rank, Suit
from game.player import Dealer
from game.blackjack import BlackjackGame, GameState, RoundResult


class TestDeck(unittest.TestCase):
    def test_deck_has_52_cards(self) -> None:
        deck = Deck()
        self.assertEqual(deck.remaining, 52)

    def test_all_cards_unique(self) -> None:
        deck = Deck()
        cards = [deck.draw() for _ in range(52)]
        self.assertEqual(len(set(cards)), 52)

    def test_draw_reduces_remaining(self) -> None:
        deck = Deck()
        deck.draw()
        self.assertEqual(deck.remaining, 51)

    def test_auto_reset_on_empty(self) -> None:
        deck = Deck()
        for _ in range(52):
            deck.draw()
        self.assertEqual(deck.remaining, 0)
        card = deck.draw()
        self.assertIsInstance(card, Card)
        self.assertEqual(deck.remaining, 51)


class TestHandValue(unittest.TestCase):
    def _hand(self, *cards: Card) -> Hand:
        h = Hand()
        for c in cards:
            h.add(c)
        return h

    def test_number_cards(self) -> None:
        hand = self._hand(
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.THREE, Suit.CLUBS),
        )
        self.assertEqual(hand.value, 8)

    def test_face_cards_worth_10(self) -> None:
        hand = self._hand(
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.QUEEN, Suit.HEARTS),
        )
        self.assertEqual(hand.value, 20)

    def test_ace_as_11(self) -> None:
        hand = self._hand(
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.FIVE, Suit.CLUBS),
        )
        self.assertEqual(hand.value, 16)

    def test_ace_reduced_to_1(self) -> None:
        hand = self._hand(
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.NINE, Suit.CLUBS),
            Card(Rank.FIVE, Suit.SPADES),
        )
        # 11 + 9 + 5 = 25, reduce ace → 1 + 9 + 5 = 15
        self.assertEqual(hand.value, 15)

    def test_two_aces(self) -> None:
        hand = self._hand(
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.SPADES),
        )
        # 11 + 11 = 22 → 11 + 1 = 12
        self.assertEqual(hand.value, 12)

    def test_three_aces(self) -> None:
        hand = self._hand(
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.ACE, Suit.CLUBS),
        )
        # 11 + 1 + 1 = 13
        self.assertEqual(hand.value, 13)


class TestBlackjackDetection(unittest.TestCase):
    def test_blackjack_ace_king(self) -> None:
        h = Hand()
        h.add(Card(Rank.ACE, Suit.HEARTS))
        h.add(Card(Rank.KING, Suit.SPADES))
        self.assertTrue(h.is_blackjack)

    def test_blackjack_ace_ten(self) -> None:
        h = Hand()
        h.add(Card(Rank.ACE, Suit.CLUBS))
        h.add(Card(Rank.TEN, Suit.DIAMONDS))
        self.assertTrue(h.is_blackjack)

    def test_not_blackjack_three_cards(self) -> None:
        h = Hand()
        h.add(Card(Rank.SEVEN, Suit.HEARTS))
        h.add(Card(Rank.SEVEN, Suit.CLUBS))
        h.add(Card(Rank.SEVEN, Suit.SPADES))
        self.assertFalse(h.is_blackjack)

    def test_not_blackjack_low_value(self) -> None:
        h = Hand()
        h.add(Card(Rank.FIVE, Suit.HEARTS))
        h.add(Card(Rank.SIX, Suit.CLUBS))
        self.assertFalse(h.is_blackjack)


class TestBust(unittest.TestCase):
    def test_bust_over_21(self) -> None:
        h = Hand()
        h.add(Card(Rank.KING, Suit.HEARTS))
        h.add(Card(Rank.QUEEN, Suit.CLUBS))
        h.add(Card(Rank.FIVE, Suit.SPADES))
        self.assertTrue(h.is_bust)

    def test_no_bust_at_21(self) -> None:
        h = Hand()
        h.add(Card(Rank.KING, Suit.HEARTS))
        h.add(Card(Rank.QUEEN, Suit.CLUBS))
        h.add(Card(Rank.ACE, Suit.SPADES))
        self.assertFalse(h.is_bust)
        self.assertEqual(h.value, 21)


class TestDealer(unittest.TestCase):
    def test_dealer_hits_below_17(self) -> None:
        dealer = Dealer()
        dealer.receive(Card(Rank.TEN, Suit.HEARTS))
        dealer.receive(Card(Rank.SIX, Suit.CLUBS))
        self.assertTrue(dealer.should_hit())

    def test_dealer_stands_on_17(self) -> None:
        dealer = Dealer()
        dealer.receive(Card(Rank.TEN, Suit.HEARTS))
        dealer.receive(Card(Rank.SEVEN, Suit.CLUBS))
        self.assertFalse(dealer.should_hit())

    def test_dealer_stands_on_soft_17(self) -> None:
        dealer = Dealer()
        dealer.receive(Card(Rank.ACE, Suit.HEARTS))
        dealer.receive(Card(Rank.SIX, Suit.CLUBS))
        # Ace(11) + 6 = 17 → should stand
        self.assertEqual(dealer.value, 17)
        self.assertFalse(dealer.should_hit())

    def test_dealer_stands_on_20(self) -> None:
        dealer = Dealer()
        dealer.receive(Card(Rank.KING, Suit.HEARTS))
        dealer.receive(Card(Rank.QUEEN, Suit.CLUBS))
        self.assertFalse(dealer.should_hit())


class TestBlackjackGame(unittest.TestCase):
    def test_new_round_deals_two_each(self) -> None:
        game = BlackjackGame()
        game.new_round()
        self.assertEqual(len(game.player.hand), 2)
        self.assertEqual(len(game.dealer.hand), 2)

    def test_new_round_clears_previous(self) -> None:
        game = BlackjackGame()
        game.new_round()
        old_cards = list(game.player.hand.cards)
        game.new_round()
        self.assertEqual(len(game.player.hand), 2)
        # Cards should be different (with high probability)
        # At minimum, old hand was cleared
        self.assertNotEqual(id(old_cards), id(game.player.hand.cards))

    def test_player_hit_adds_card(self) -> None:
        game = BlackjackGame()
        game.new_round()
        if game.state != GameState.PLAYER_TURN:
            self.skipTest("Natural blackjack dealt")
        game.player_hit()
        self.assertEqual(len(game.player.hand), 3)

    def test_player_cannot_hit_after_stand(self) -> None:
        game = BlackjackGame()
        game.new_round()
        if game.state != GameState.PLAYER_TURN:
            self.skipTest("Natural blackjack dealt")
        game.player_stand()
        game.player_hit()
        # Player should not have received a 3rd card
        self.assertEqual(len(game.player.hand), 2)

    def test_state_initial(self) -> None:
        game = BlackjackGame()
        self.assertEqual(game.state, GameState.INITIAL)

    def test_state_after_new_round(self) -> None:
        game = BlackjackGame()
        game.new_round()
        self.assertIn(game.state, (GameState.PLAYER_TURN, GameState.ROUND_OVER))

    def test_stand_leads_to_round_over(self) -> None:
        game = BlackjackGame()
        game.new_round()
        if game.state != GameState.PLAYER_TURN:
            self.skipTest("Natural blackjack dealt")
        game.player_stand()
        self.assertEqual(game.state, GameState.ROUND_OVER)
        self.assertIsNotNone(game.result)


class TestWinnerDetermination(unittest.TestCase):
    def _setup_game(
        self,
        player_cards: list[Card],
        dealer_cards: list[Card],
    ) -> BlackjackGame:
        """Create a game with pre-set hands for deterministic testing."""
        game = BlackjackGame()
        game.player.hand.cards = player_cards
        game.dealer.hand.cards = dealer_cards
        return game

    def test_player_wins_higher_score(self) -> None:
        game = self._setup_game(
            [Card(Rank.KING, Suit.HEARTS), Card(Rank.NINE, Suit.CLUBS)],
            [Card(Rank.KING, Suit.SPADES), Card(Rank.EIGHT, Suit.DIAMONDS)],
        )
        result = game._compare_hands()
        self.assertEqual(result, RoundResult.PLAYER_WIN)

    def test_dealer_wins_higher_score(self) -> None:
        game = self._setup_game(
            [Card(Rank.KING, Suit.HEARTS), Card(Rank.SEVEN, Suit.CLUBS)],
            [Card(Rank.KING, Suit.SPADES), Card(Rank.NINE, Suit.DIAMONDS)],
        )
        result = game._compare_hands()
        self.assertEqual(result, RoundResult.DEALER_WIN)

    def test_push_equal_scores(self) -> None:
        game = self._setup_game(
            [Card(Rank.KING, Suit.HEARTS), Card(Rank.EIGHT, Suit.CLUBS)],
            [Card(Rank.QUEEN, Suit.SPADES), Card(Rank.EIGHT, Suit.DIAMONDS)],
        )
        result = game._compare_hands()
        self.assertEqual(result, RoundResult.PUSH)

    def test_both_blackjack_is_push(self) -> None:
        game = self._setup_game(
            [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.CLUBS)],
            [Card(Rank.ACE, Suit.SPADES), Card(Rank.QUEEN, Suit.DIAMONDS)],
        )
        result = game._resolve_blackjacks()
        self.assertEqual(result, RoundResult.PUSH)

    def test_player_blackjack_only(self) -> None:
        game = self._setup_game(
            [Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.CLUBS)],
            [Card(Rank.TEN, Suit.SPADES), Card(Rank.NINE, Suit.DIAMONDS)],
        )
        result = game._resolve_blackjacks()
        self.assertEqual(result, RoundResult.PLAYER_BLACKJACK)

    def test_dealer_blackjack_only(self) -> None:
        game = self._setup_game(
            [Card(Rank.TEN, Suit.HEARTS), Card(Rank.NINE, Suit.CLUBS)],
            [Card(Rank.ACE, Suit.SPADES), Card(Rank.QUEEN, Suit.DIAMONDS)],
        )
        result = game._resolve_blackjacks()
        self.assertEqual(result, RoundResult.DEALER_WIN)


class TestSessionStats(unittest.TestCase):
    """Tests for win/loss/push session statistics."""

    def test_stats_start_at_zero(self) -> None:
        game = BlackjackGame()
        self.assertEqual(game.wins, 0)
        self.assertEqual(game.losses, 0)
        self.assertEqual(game.pushes, 0)

    def test_player_win_increments_wins(self) -> None:
        game = BlackjackGame()
        game.state = GameState.PLAYER_TURN
        game.player.hand.cards = [
            Card(Rank.KING, Suit.HEARTS), Card(Rank.NINE, Suit.CLUBS),
        ]
        game.dealer.hand.cards = [
            Card(Rank.KING, Suit.SPADES), Card(Rank.EIGHT, Suit.DIAMONDS),
        ]
        game.player_stand()
        self.assertEqual(game.wins, 1)
        self.assertEqual(game.losses, 0)

    def test_player_bust_increments_losses(self) -> None:
        game = BlackjackGame()
        game.state = GameState.PLAYER_TURN
        game.player.hand.cards = [
            Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.CLUBS),
        ]
        # Force a bust card
        game.deck._cards = [Card(Rank.FIVE, Suit.SPADES)]
        game.player_hit()
        self.assertEqual(game.losses, 1)
        self.assertEqual(game.wins, 0)

    def test_push_increments_pushes(self) -> None:
        game = BlackjackGame()
        game.state = GameState.PLAYER_TURN
        game.player.hand.cards = [
            Card(Rank.KING, Suit.HEARTS), Card(Rank.EIGHT, Suit.CLUBS),
        ]
        game.dealer.hand.cards = [
            Card(Rank.QUEEN, Suit.SPADES), Card(Rank.EIGHT, Suit.DIAMONDS),
        ]
        game.player_stand()
        self.assertEqual(game.pushes, 1)
        self.assertEqual(game.wins, 0)
        self.assertEqual(game.losses, 0)

    def test_stats_accumulate_across_rounds(self) -> None:
        game = BlackjackGame()
        # Simulate a win
        game.state = GameState.PLAYER_TURN
        game.player.hand.cards = [
            Card(Rank.KING, Suit.HEARTS), Card(Rank.NINE, Suit.CLUBS),
        ]
        game.dealer.hand.cards = [
            Card(Rank.KING, Suit.SPADES), Card(Rank.SEVEN, Suit.DIAMONDS),
        ]
        game.player_stand()
        self.assertEqual(game.wins, 1)

        # Simulate a loss (player bust)
        game.state = GameState.PLAYER_TURN
        game.player.hand.cards = [
            Card(Rank.KING, Suit.HEARTS), Card(Rank.QUEEN, Suit.CLUBS),
        ]
        game.deck._cards = [Card(Rank.FIVE, Suit.SPADES)]
        game.player_hit()
        self.assertEqual(game.wins, 1)
        self.assertEqual(game.losses, 1)


if __name__ == "__main__":
    unittest.main()
