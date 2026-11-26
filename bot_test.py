"""Exploration script (real PokerGame, real equity simulations).

    python bot_test.py scan     # print raise EVs by hand / board / bet size
    python bot_test.py sweep    # sweep bot traits, report how decisions change

For exact pass/fail logic tests of bot.decision, see test.py (uses a stub game).
"""
import sys
from unittest import mock
import game
import bot
import game_decision

# bot.decision calls game_decision.calculate_ev_raise by module attribute, so the sweep swaps in a
# caching version while a decision runs. Keep a handle on the real one for the cache to call.
_real_calculate_ev_raise = game_decision.calculate_ev_raise

SMALL_BLIND = 100
BIG_BLIND = 200
STACK = 4000
N_SIMS = 500  # lower = faster but noisier EVs
RAISED_POT_CONTRIB = 400  # chips each player has in a "raised pot" scenario
FACING_BET = 800  # size of the bet the bot faces in "facing bet" scenarios

test_hands = [["Ad", "Ah"], ["Ah", "Kh"], ["Kd", "Kh"],
              ["Qd", "Qh"], ["Ad", "Qd"], ["Jd", "Jh"],
              ["7d", "6d"], ["5d", "5h"], ["Td", "9d"],
              ["7d", "2h"], ["Jd", "3h"]]

# vary board texture too (the first, empty board is preflop)
test_boards = {
    "preflop": [],
    "dry rainbow": ["2c", "8d", "Ks"],
    "high cards, rainbow": ["Ac", "Kd", "2s"],
    "rank-only wet": ["8c", "9d", "Th"],
    "suit-only wet": ["2h", "7h", "Kh"],
    "wet monotone straight": ["9h", "Th", "Jh"],
}

# Driest: rainbow, disconnected, mixed rank. Wettest: monotone, tightly connected, high cards.
# "suit-only wet" isolates the flush axis, "rank-only wet" isolates the straight axis,
# "high cards, rainbow" isolates the high-card term.

PLAYER_COUNTS = [2, 4, 6]  # vary number of opponents

# a subset of the above, so the trait sweep stays quick
sweep_hands = [["Ad", "Ah"], ["Ad", "Qd"], ["7d", "6d"], ["7d", "2h"]]
sweep_boards = ["preflop", "dry rainbow", "wet monotone straight"]


def betting_round_for(board):
    """0 preflop, 1 flop, 2 turn, 3 river."""
    return max(len(board) - 2, 0)


def overlaps(hand, board):
    return bool(set(hand) & set(board))


def make_game(hand, board, num_players, raised_pot=False, facing_bet=0):
    """Own seat 1 on the button.

    raised_pot: every player has put RAISED_POT_CONTRIB in preflop (a raised-and-called pot), instead of
        just the blinds. Needed for postflop tests: with only blinds in, the pot is smaller than the
        minimum raise, so every proportional bet size collapses to the same min-raise.
    facing_bet: seat 2 bets this many extra chips, so the bot is facing a bet.
    """
    seats = list(range(1, num_players + 1))
    pg = game.PokerGame(
        own_hand=hand, own_pos="BTN", own_seat=1,
        occupied_seats=seats,
        stacks={s: STACK for s in seats},
        board_cards=list(board),
    )
    if raised_pot:
        for s in seats:
            pg.player_bet(s, RAISED_POT_CONTRIB)
    else:
        pg.post_blinds(SMALL_BLIND, BIG_BLIND)
    if facing_bet:
        pg.player_bet(2, facing_bet)
    return pg


# ---------------------------------------------------------------- scan

def ev_scan():
    for num_players in PLAYER_COUNTS:
        for hand in test_hands:
            for board_name, board in test_boards.items():
                if overlaps(hand, board):
                    continue
                pg = make_game(hand, board, num_players, raised_pot=bool(board))
                rnd = betting_round_for(board)
                cost = pg.get_max_contribution() - pg.get_seat_contribution(1)
                min_raise = cost + BIG_BLIND
                pot = pg.get_pot()
                bets = sorted({max(int(p * pot), min_raise) for p in (0.5, 1.0)} | {STACK})
                evs = ", ".join(
                    f"{bet}: {game_decision.calculate_ev_raise(pg.to_snapshot(), bet, rnd, 1, hand, n_sims=N_SIMS):8.1f}" for bet in bets
                )
                print(f"{num_players}p  {' '.join(hand)}  {board_name:<22} pot={pot:<5} {evs}")


# ---------------------------------------------------------------- sweep

class CachedGame:
    """Wraps a PokerGame and remembers raise EVs, so every trait setting sees the same numbers.
    Without this, simulation noise between runs can swamp the effect of the trait being swept.

    bot.decision asks the game for a snapshot (to_snapshot) and passes it to
    game_decision.calculate_ev_raise. run_situation patches that function with
    self.calculate_ev_raise below, so the cache sits in between."""

    def __init__(self, pg):
        self.pg = pg
        self.cache = {}

    def to_snapshot(self):
        return self.pg.to_snapshot()

    def calculate_ev_raise(self, snapshot, bet, betting_round, seat=None, hand=None, n_sims=N_SIMS):
        key = (bet, betting_round, seat, tuple(hand) if hand else None)
        if key not in self.cache:
            self.cache[key] = _real_calculate_ev_raise(snapshot, bet, betting_round, seat, hand, n_sims=n_sims)
        return self.cache[key]


def build_situations():
    """(label, cached game, hand, round, ev_call, cost_to_call) for each hand/board/facing-a-bet combo.
    Preflop uses just the blinds; postflop uses a raised pot so there are real bet sizes to choose from."""
    situations = []
    for hand in sweep_hands:
        for board_name in sweep_boards:
            board = test_boards[board_name]
            if overlaps(hand, board):
                continue
            for facing in (False, True):
                pg = make_game(hand, board, 4, raised_pot=bool(board), facing_bet=FACING_BET if facing else 0)
                cost = pg.get_max_contribution() - pg.get_seat_contribution(1)
                equity = game_decision.get_equity(pg.to_snapshot(), seat=1, hand=hand, n_sims=N_SIMS)
                ev_call = game_decision.calculate_ev_call(pg.to_snapshot(), equity, cost)
                label = f"{' '.join(hand)} | {board_name} | {'facing bet' if facing else 'no bet'}"
                situations.append((label, CachedGame(pg), hand, betting_round_for(board), ev_call, cost))
    return situations


def run_situation(trait, value, situation):
    _, cg, hand, rnd, ev_call, cost = situation
    traits = dict(volatility=0.0, aggressiveness=0.5, looseness=1.0, bet_sizing=0.5)
    traits[trait] = value
    b = bot.bot(**traits)
    pg = cg.pg
    with mock.patch.object(game_decision, "calculate_ev_raise", cg.calculate_ev_raise):
        action, amount = b.decision(cg, 1, hand, pg.get_stack(1), ev_call, rnd, pg.get_pot(), cost, BIG_BLIND)
    return action, amount


def trait_sweep():
    print(f"building {len(sweep_hands) * len(sweep_boards) * 2} situations (equity sims)...")
    situations = build_situations()
    values = {
        "bet_sizing": [0.0, 0.25, 0.5, 0.75, 1.0],
        "aggressiveness": [0.0, 0.25, 0.5, 0.75, 1.0],
        "looseness": [0.5, 0.75, 1.0, 1.25, 1.5],
    }
    for trait, vals in values.items():
        print(f"\n=== {trait} (others fixed: volatility 0, aggressiveness 0.5, looseness 1, bet_sizing 0.5) ===")
        print(f"{'value':>6} {'fold%':>6} {'passive%':>9} {'raise%':>7} {'avg raise/pot':>14} {'avg EV given up (BB)':>21} {'not-max-EV%':>12}")
        for v in vals:
            counts = {"fold": 0, "passive": 0, "raise": 0}
            sizes, given_up = [], []
            for situation in situations:
                action, amount = run_situation(trait, v, situation)
                if action == "fold":
                    counts["fold"] += 1
                elif action == "raise":
                    counts["raise"] += 1
                    cg = situation[1]
                    evs = {key[0]: ev for key, ev in cg.cache.items()}
                    sizes.append(amount / cg.pg.get_pot())
                    given_up.append((max(evs.values()) - evs[amount]) / BIG_BLIND)
                else:
                    counts["passive"] += 1
            n = len(situations)
            avg_size = sum(sizes) / len(sizes) if sizes else float("nan")
            avg_given = sum(given_up) / len(given_up) if given_up else float("nan")
            off_best = 100 * sum(1 for g in given_up if g > 1e-9) / len(given_up) if given_up else float("nan")
            print(f"{v:>6} {100 * counts['fold'] / n:>6.0f} {100 * counts['passive'] / n:>9.0f} {100 * counts['raise'] / n:>7.0f} "
                  f"{avg_size:>14.2f} {avg_given:>21.3f} {off_best:>12.0f}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if mode == "scan":
        ev_scan()
    elif mode == "sweep":
        trait_sweep()
    else:
        print("usage: python bot_test.py [scan|sweep]")
