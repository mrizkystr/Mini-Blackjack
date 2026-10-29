"""Mini Blackjack — Pygame entry point and renderer."""

from __future__ import annotations

import sys
import time

import pygame

from game.blackjack import BlackjackGame, GameState
from game.cards import Card, RANK_DISPLAY, SUIT_SYMBOL, SUIT_COLOR

# ── Constants ────────────────────────────────────────────────────────────────
DEFAULT_W, DEFAULT_H = 1100, 700
MIN_W, MIN_H = 800, 550
FPS = 60

# Colors — Minimalist Dark Casino palette
BG_GREEN = (18, 62, 34)
FELT_GREEN = (24, 78, 44)
OFF_WHITE = (235, 230, 220)
MUTED_GOLD = (195, 165, 75)
BRIGHT_GOLD = (220, 190, 90)
CARD_RED = (178, 42, 42)
CARD_BLACK = (30, 30, 30)
CARD_BG = (248, 246, 240)
CARD_BORDER = (180, 175, 165)
CARD_BACK_DARK = (35, 55, 90)
CARD_BACK_LIGHT = (50, 75, 120)
CARD_BACK_ACCENT = (70, 100, 150)
LABEL_DIM = (160, 155, 145)
BTN_NORMAL = (45, 50, 45)
BTN_HOVER = (60, 68, 58)
BTN_ACTIVE = (75, 85, 70)
BTN_DISABLED_BG = (50, 55, 50)
BTN_DISABLED_TEXT = (100, 100, 95)
RESULT_WIN = MUTED_GOLD
RESULT_LOSE = (170, 80, 70)
RESULT_PUSH = (150, 150, 140)
STATS_TEXT = (140, 138, 130)
DIVIDER_COLOR = (40, 85, 52)

# Card dimensions (base, scaled at runtime)
BASE_CARD_W, BASE_CARD_H = 82, 118
BASE_CARD_GAP = 16
CARD_RADIUS = 8

# Button dimensions (base)
BASE_BTN_W, BASE_BTN_H = 130, 44
BTN_RADIUS = 6

# Animation
DEAL_DURATION = 0.15  # seconds per card deal
RESULT_FADE_DURATION = 0.3


# ── Helpers ──────────────────────────────────────────────────────────────────
def card_color(card: Card) -> tuple[int, int, int]:
    return CARD_RED if SUIT_COLOR[card.suit] == "red" else CARD_BLACK


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation clamped to [0, 1]."""
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def ease_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) * (1.0 - t)


# ── Layout calculator ───────────────────────────────────────────────────────
class Layout:
    """Computes positions relative to current window size."""

    def __init__(self, w: int, h: int) -> None:
        self.w = w
        self.h = h
        self.scale = min(w / DEFAULT_W, h / DEFAULT_H)
        self.scale = max(self.scale, 0.6)  # floor

        self.card_w = int(BASE_CARD_W * self.scale)
        self.card_h = int(BASE_CARD_H * self.scale)
        self.card_gap = int(BASE_CARD_GAP * self.scale)
        self.btn_w = int(BASE_BTN_W * self.scale)
        self.btn_h = int(BASE_BTN_H * self.scale)

        # Vertical zones (proportional)
        self.title_y = int(h * 0.02)
        self.dealer_label_y = int(h * 0.10)
        self.dealer_score_y = self.dealer_label_y + int(26 * self.scale)
        self.dealer_cards_y = self.dealer_score_y + int(24 * self.scale)
        self.divider_y = int(h * 0.48)
        self.result_y = int(h * 0.50)
        self.player_label_y = int(h * 0.58)
        self.player_score_y = self.player_label_y + int(26 * self.scale)
        self.player_cards_y = self.player_score_y + int(24 * self.scale)
        self.btn_y = int(h * 0.90)
        self.stats_y = int(h * 0.02)

    def hand_start_x(self, n_cards: int) -> int:
        total = n_cards * self.card_w + max(0, n_cards - 1) * self.card_gap
        return (self.w - total) // 2

    def card_x(self, index: int, n_cards: int) -> int:
        return self.hand_start_x(n_cards) + index * (self.card_w + self.card_gap)


# ── Animated card slot ───────────────────────────────────────────────────────
class CardSlot:
    """Tracks a single card's deal animation."""

    def __init__(
        self, card: Card, target_x: int, target_y: int, face_up: bool,
        start_time: float,
    ) -> None:
        self.card = card
        self.target_x = target_x
        self.target_y = target_y
        self.face_up = face_up
        self.start_time = start_time
        # Cards fly in from above the window
        self.start_x = target_x
        self.start_y = target_y - 120

    def progress(self, now: float) -> float:
        elapsed = now - self.start_time
        return min(1.0, elapsed / DEAL_DURATION)

    def current_pos(self, now: float) -> tuple[int, int]:
        t = ease_out_quad(self.progress(now))
        x = int(lerp(self.start_x, self.target_x, t))
        y = int(lerp(self.start_y, self.target_y, t))
        return x, y

    def is_done(self, now: float) -> bool:
        return self.progress(now) >= 1.0


# ── Renderer ─────────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self._rebuild_fonts(screen.get_width(), screen.get_height())
        self.buttons: dict[str, pygame.Rect] = {}
        self.layout = Layout(screen.get_width(), screen.get_height())

        # Animation state
        self._dealer_slots: list[CardSlot] = []
        self._player_slots: list[CardSlot] = []
        self._last_dealer_count = 0
        self._last_player_count = 0
        self._result_show_time: float | None = None
        self._prev_state: GameState = GameState.INITIAL

    def _rebuild_fonts(self, w: int, h: int) -> None:
        scale = min(w / DEFAULT_W, h / DEFAULT_H)
        scale = max(scale, 0.6)
        self.font = pygame.font.SysFont("Arial", max(12, int(20 * scale)))
        self.small_font = pygame.font.SysFont("Arial", max(10, int(15 * scale)))
        self.title_font = pygame.font.SysFont("Arial", max(16, int(28 * scale)), bold=True)
        self.result_font = pygame.font.SysFont("Arial", max(14, int(26 * scale)), bold=True)
        self.card_font = pygame.font.SysFont("Arial", max(10, int(14 * scale)))
        self.card_center_font = pygame.font.SysFont("Arial", max(14, int(22 * scale)))
        self.stats_font = pygame.font.SysFont("Arial", max(10, int(13 * scale)))

    def on_resize(self, w: int, h: int) -> None:
        self.layout = Layout(w, h)
        self._rebuild_fonts(w, h)
        # Force slot rebuild on next draw
        self._dealer_slots.clear()
        self._player_slots.clear()
        self._last_dealer_count = 0
        self._last_player_count = 0

    # ── Card drawing ─────────────────────────────────────────────────────
    def _draw_card_face(self, card: Card, x: int, y: int) -> None:
        lay = self.layout
        rect = pygame.Rect(x, y, lay.card_w, lay.card_h)

        # Card body
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, CARD_BORDER, rect, width=1, border_radius=CARD_RADIUS)

        color = card_color(card)
        rank_str = RANK_DISPLAY[card.rank]
        suit_str = SUIT_SYMBOL[card.suit]

        # Top-left: rank then suit below
        tl_rank = self.card_font.render(rank_str, True, color)
        tl_suit = self.card_font.render(suit_str, True, color)
        pad = max(4, int(5 * lay.scale))
        self.screen.blit(tl_rank, (x + pad, y + pad))
        self.screen.blit(tl_suit, (x + pad, y + pad + tl_rank.get_height()))

        # Center suit (larger)
        center = self.card_center_font.render(suit_str, True, color)
        cr = center.get_rect(center=rect.center)
        self.screen.blit(center, cr)

        # Bottom-right: suit then rank (visually inverted)
        br_rank = self.card_font.render(rank_str, True, color)
        br_suit = self.card_font.render(suit_str, True, color)
        self.screen.blit(
            br_suit,
            (x + lay.card_w - pad - br_suit.get_width(),
             y + lay.card_h - pad - br_suit.get_height() - br_rank.get_height()),
        )
        self.screen.blit(
            br_rank,
            (x + lay.card_w - pad - br_rank.get_width(),
             y + lay.card_h - pad - br_rank.get_height()),
        )

    def _draw_card_back(self, x: int, y: int) -> None:
        lay = self.layout
        rect = pygame.Rect(x, y, lay.card_w, lay.card_h)

        # Outer
        pygame.draw.rect(self.screen, CARD_BACK_DARK, rect, border_radius=CARD_RADIUS)
        pygame.draw.rect(self.screen, CARD_BORDER, rect, width=1, border_radius=CARD_RADIUS)

        # Inner decorative rectangle
        inset = max(5, int(7 * lay.scale))
        inner = pygame.Rect(x + inset, y + inset, lay.card_w - 2 * inset, lay.card_h - 2 * inset)
        pygame.draw.rect(self.screen, CARD_BACK_LIGHT, inner, border_radius=4)
        pygame.draw.rect(self.screen, CARD_BACK_ACCENT, inner, width=1, border_radius=4)

        # Diamond pattern (simple crosshatch)
        cx, cy = rect.centerx, rect.centery
        size = int(8 * lay.scale)
        pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        pygame.draw.polygon(self.screen, CARD_BACK_ACCENT, pts, width=2)

    # ── Slot management ──────────────────────────────────────────────────
    def _sync_slots(
        self,
        slots: list[CardSlot],
        cards: list[Card],
        y: int,
        hide_second: bool,
        prev_count: int,
    ) -> int:
        """Add new CardSlots for newly dealt cards. Returns new count."""
        now = time.monotonic()
        n = len(cards)

        if n < prev_count:
            # Hand was cleared — reset
            slots.clear()
            return 0

        for i in range(prev_count, n):
            tx = self.layout.card_x(i, n)
            face_up = not (hide_second and i == 1)
            delay = (i - prev_count) * DEAL_DURATION * 0.6
            slot = CardSlot(cards[i], tx, y, face_up, now + delay)
            slots.append(slot)

        # Update target positions for all slots (window resize, new cards shift)
        for i, slot in enumerate(slots):
            slot.target_x = self.layout.card_x(i, n)
            slot.target_y = y
            slot.start_x = slot.target_x  # keep x stable
            if slot.is_done(now):
                # Already settled, just snap
                pass

        return n

    def _draw_slots(self, slots: list[CardSlot], hide_second: bool) -> None:
        now = time.monotonic()
        for i, slot in enumerate(slots):
            x, y = slot.current_pos(now)
            alpha = ease_out_quad(slot.progress(now))
            if alpha < 0.01:
                continue
            if hide_second and i == 1:
                self._draw_card_back(x, y)
            else:
                self._draw_card_face(slot.card, x, y)

    # ── Buttons ──────────────────────────────────────────────────────────
    def _draw_button(
        self,
        text: str,
        x: int,
        y: int,
        enabled: bool = True,
        mouse_pos: tuple[int, int] = (0, 0),
    ) -> pygame.Rect:
        lay = self.layout
        rect = pygame.Rect(x, y, lay.btn_w, lay.btn_h)
        hovering = enabled and rect.collidepoint(mouse_pos)

        if not enabled:
            bg = BTN_DISABLED_BG
            fg = BTN_DISABLED_TEXT
        elif hovering:
            bg = BTN_HOVER
            fg = MUTED_GOLD
        else:
            bg = BTN_NORMAL
            fg = OFF_WHITE

        pygame.draw.rect(self.screen, bg, rect, border_radius=BTN_RADIUS)
        # Subtle border
        border_col = MUTED_GOLD if hovering and enabled else (70, 75, 68)
        pygame.draw.rect(self.screen, border_col, rect, width=1, border_radius=BTN_RADIUS)

        label = self.font.render(text, True, fg)
        lr = label.get_rect(center=rect.center)
        self.screen.blit(label, lr)
        self.buttons[text] = rect
        return rect

    # ── Stats bar ────────────────────────────────────────────────────────
    def _draw_stats(self, game: BlackjackGame) -> None:
        lay = self.layout
        total = game.wins + game.losses + game.pushes
        if total == 0:
            return

        parts = [
            ("W: " + str(game.wins), MUTED_GOLD),
            ("L: " + str(game.losses), RESULT_LOSE),
            ("P: " + str(game.pushes), RESULT_PUSH),
        ]
        x = lay.w - int(16 * lay.scale)
        y = lay.stats_y
        for text, color in reversed(parts):
            surf = self.stats_font.render(text, True, color)
            x -= surf.get_width()
            self.screen.blit(surf, (x, y))
            x -= int(14 * lay.scale)

    # ── Full frame ───────────────────────────────────────────────────────
    def draw(self, game: BlackjackGame, mouse_pos: tuple[int, int]) -> None:
        lay = self.layout
        self.screen.fill(BG_GREEN)
        self.buttons.clear()

        # Felt area (subtle inner rect)
        felt_margin = int(12 * lay.scale)
        felt_rect = pygame.Rect(
            felt_margin, felt_margin,
            lay.w - 2 * felt_margin, lay.h - 2 * felt_margin,
        )
        pygame.draw.rect(self.screen, FELT_GREEN, felt_rect, border_radius=12)

        # Title
        title = self.title_font.render("Mini Blackjack", True, MUTED_GOLD)
        self.screen.blit(title, (lay.w // 2 - title.get_width() // 2, lay.title_y))

        # Stats
        self._draw_stats(game)

        if game.state == GameState.INITIAL:
            self._draw_initial(mouse_pos)
            self._prev_state = game.state
            return

        # Detect state transitions for animations
        if game.state != self._prev_state:
            if game.state == GameState.ROUND_OVER:
                self._result_show_time = time.monotonic()
            if self._prev_state == GameState.INITIAL or self._prev_state == GameState.ROUND_OVER:
                # New round started
                self._dealer_slots.clear()
                self._player_slots.clear()
                self._last_dealer_count = 0
                self._last_player_count = 0
                self._result_show_time = None

        hide = not game.show_dealer_hole

        # ── Sync card slots ──────────────────────────────────────────
        self._last_dealer_count = self._sync_slots(
            self._dealer_slots, game.dealer.hand.cards,
            lay.dealer_cards_y, hide, self._last_dealer_count,
        )
        self._last_player_count = self._sync_slots(
            self._player_slots, game.player.hand.cards,
            lay.player_cards_y, False, self._last_player_count,
        )

        # When hole card is revealed, update face_up
        if not hide:
            for slot in self._dealer_slots:
                slot.face_up = True

        # ── Dealer section ───────────────────────────────────────────
        dlabel = self.font.render("Dealer", True, OFF_WHITE)
        self.screen.blit(dlabel, (lay.w // 2 - dlabel.get_width() // 2, lay.dealer_label_y))

        if hide and len(game.dealer.hand.cards) >= 2:
            visible_val = game.dealer.hand.cards[0].blackjack_value
            val_text = "Showing: " + str(visible_val)
        else:
            val_text = "Hand: " + str(game.dealer.value)
        dval = self.small_font.render(val_text, True, LABEL_DIM)
        self.screen.blit(dval, (lay.w // 2 - dval.get_width() // 2, lay.dealer_score_y))

        self._draw_slots(self._dealer_slots, hide)

        # ── Divider ──────────────────────────────────────────────────
        div_pad = int(80 * lay.scale)
        pygame.draw.line(
            self.screen, DIVIDER_COLOR,
            (div_pad, lay.divider_y), (lay.w - div_pad, lay.divider_y), 1,
        )

        # ── Result message ───────────────────────────────────────────
        if game.is_round_over and game.result:
            self._draw_result(game)

        # ── Player section ───────────────────────────────────────────
        plabel = self.font.render("Player", True, OFF_WHITE)
        self.screen.blit(plabel, (lay.w // 2 - plabel.get_width() // 2, lay.player_label_y))

        pval = self.small_font.render("Hand: " + str(game.player.value), True, LABEL_DIM)
        self.screen.blit(pval, (lay.w // 2 - pval.get_width() // 2, lay.player_score_y))

        self._draw_slots(self._player_slots, False)

        # ── Buttons ──────────────────────────────────────────────────
        center_x = lay.w // 2

        if game.is_round_over:
            self._draw_button(
                "New Round", center_x - lay.btn_w // 2, lay.btn_y,
                enabled=True, mouse_pos=mouse_pos,
            )
        else:
            gap = int(16 * lay.scale)
            self._draw_button(
                "Hit", center_x - lay.btn_w - gap // 2, lay.btn_y,
                enabled=game.is_player_turn, mouse_pos=mouse_pos,
            )
            self._draw_button(
                "Stand", center_x + gap // 2, lay.btn_y,
                enabled=game.is_player_turn, mouse_pos=mouse_pos,
            )

        self._prev_state = game.state

    def _draw_result(self, game: BlackjackGame) -> None:
        lay = self.layout
        msg = game.result.value  # type: ignore[union-attr]
        msg_lower = msg.lower()

        if "win" in msg_lower or "blackjack" in msg_lower:
            color = RESULT_WIN
        elif "push" in msg_lower:
            color = RESULT_PUSH
        else:
            color = RESULT_LOSE

        # Fade in
        alpha = 1.0
        if self._result_show_time is not None:
            elapsed = time.monotonic() - self._result_show_time
            alpha = min(1.0, elapsed / RESULT_FADE_DURATION)

        # Render with opacity simulation via color blending against felt
        blended = tuple(
            int(lerp(FELT_GREEN[i], color[i], alpha)) for i in range(3)
        )
        txt = self.result_font.render(msg, True, blended)
        self.screen.blit(txt, (lay.w // 2 - txt.get_width() // 2, lay.result_y))

    def _draw_initial(self, mouse_pos: tuple[int, int]) -> None:
        lay = self.layout
        prompt = self.font.render("Press New Round to begin", True, LABEL_DIM)
        self.screen.blit(
            prompt,
            (lay.w // 2 - prompt.get_width() // 2, lay.h // 2 - int(30 * lay.scale)),
        )
        self._draw_button(
            "New Round",
            lay.w // 2 - lay.btn_w // 2,
            lay.h // 2 + int(15 * lay.scale),
            enabled=True,
            mouse_pos=mouse_pos,
        )


# ── Main loop ────────────────────────────────────────────────────────────────
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(
        (DEFAULT_W, DEFAULT_H), pygame.RESIZABLE,
    )
    pygame.display.set_caption("Mini Blackjack")
    clock = pygame.time.Clock()

    game = BlackjackGame()
    renderer = Renderer(screen)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                w = max(event.w, MIN_W)
                h = max(event.h, MIN_H)
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                renderer.screen = screen
                renderer.on_resize(w, h)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in renderer.buttons.items():
                    if rect.collidepoint(event.pos):
                        if name == "Hit" and game.is_player_turn:
                            game.player_hit()
                        elif name == "Stand" and game.is_player_turn:
                            game.player_stand()
                        elif name == "New Round":
                            game.new_round()

        renderer.draw(game, mouse_pos)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
