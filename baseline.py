"""Seeded baseline for the decision code, to prove a refactor doesn't change results.

Usage:
    python baseline.py record   # run scenarios, save results to baseline.json
    python baseline.py check    # run scenarios again, compare with baseline.json

Record BEFORE moving the decision code, check AFTER. Every scenario reseeds
`random` right before each call, so results are exactly reproducible.

When you migrate the decision code, only edit the three adapter functions
below (ev_raise, ev_call, equity). Scenarios and everything else stay the same.
"""
import json
import os
import random
import sys

# Some code iterates over sets of strings (e.g. the deck in equity_calculator),
# and Python randomizes string hashing per process, so set order -- and therefore
# which cards random.sample picks -- would differ between runs even with a seed.
# Pin the hash seed by re-launching this script once with PYTHONHASHSEED set.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

import game
import game_decision

BASELINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline.json")
N_SIMS = 200


# ---------------------------------------------------------------------------
# ADAPTERS: the only place that knows how to reach the decision code.
# After the migration, change these bodies (e.g. build g.to_snapshot() and
# call game_decision.<function>) and leave the rest of the file alone.
# ---------------------------------------------------------------------------
def ev_raise(g, bet, betting_round, seat=None, hand=None):
    return game_decision.calculate_ev_raise(g.to_snapshot(), bet, betting_round, seat, hand, n_sims=N_SIMS)


def ev_call(g, equity_value, cost_to_call):
    return game_decision.calculate_ev_call(g.to_snapshot(), equity_value, cost_to_call)


def equity(g, seat=None, hand=None):
    return game_decision.get_equity(g.to_snapshot(), seat=seat, hand=hand, n_sims=N_SIMS)


# ---------------------------------------------------------------------------
# Scenario setup
# ---------------------------------------------------------------------------
def make_game(num_players, own_hand, board=None, own_pos="BTN", stack=1000):
    seats = list(range(1, num_players + 1))
    g = game.PokerGame(
        own_hand, 1, seats, {s: stack for s in seats},
        list(board) if board else [], own_pos=own_pos,
    )
    g.post_blinds(5, 10)
    return g


def scenarios():
    """Yield (name, function that takes no args and returns a number)."""
    # 1. Six-handed preflop, button with AKo, several bet sizes
    g = make_game(6, ["Ah", "Kd"])
    for bet in (20, 30, 100, 500, 1000):
        yield f"6max_preflop_AKo_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))
    yield "6max_preflop_AKo_equity", (lambda g=g: equity(g))

    # 2. Six-handed preflop, weak hand
    g = make_game(6, ["7c", "2d"])
    for bet in (30, 200):
        yield f"6max_preflop_72o_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))

    # 3. Heads-up preflop
    g = make_game(2, ["Qs", "Jh"])
    for bet in (20, 100, 990):
        yield f"headsup_preflop_QJs_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))
    yield "headsup_preflop_equity", (lambda g=g: equity(g))

    # 4. Three-handed with an all-in opponent (seat 2 has no chips behind)
    g = make_game(3, ["Ac", "Qc"])
    g.stacks[2] = 0
    for bet in (30, 150):
        yield f"3way_allin_opp_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))

    # 5. Short-stacked opponent (seat 3 has only 25 behind)
    g = make_game(4, ["9h", "9d"])
    g.stacks[3] = 25
    for bet in (30, 120):
        yield f"4way_short_stack_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))

    # 6. Flop, wet board, six-handed
    g = make_game(6, ["Jh", "Th"], board=["9h", "8h", "2c"])
    for bet in (15, 60, 200):
        yield f"6max_flop_wet_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 1))
    yield "6max_flop_wet_equity", (lambda g=g: equity(g))

    # 7. Flop, dry board, heads-up
    g = make_game(2, ["Ks", "Qd"], board=["2c", "7d", "Js"])
    for bet in (15, 60):
        yield f"headsup_flop_dry_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 1))

    # 8. Different opponent traits (loose seat 2, tight seat 3)
    g = make_game(4, ["Ad", "Jd"])
    g.update_traits(2, 1.4)
    g.update_traits(3, 0.6)
    for bet in (30, 120):
        yield f"4way_traits_raise_{bet}", (lambda g=g, bet=bet: ev_raise(g, bet, 0))

    # 9. Turn with a river-ish board, checking a non-default seat and hand
    g = make_game(5, ["Ah", "Kd"], board=["Qs", "Js", "2d", "5c"])
    yield "5way_turn_seat3_equity", (lambda g=g: equity(g, seat=3, hand=["Th", "9h"]))
    yield "5way_turn_seat3_raise_80", (lambda g=g: ev_raise(g, 80, 2, 3, ["Th", "9h"]))

    # 10. EV of calling (pure arithmetic, but it moves with the code)
    g = make_game(6, ["Ah", "Kd"])
    yield "ev_call_0.4_cost_20", (lambda g=g: ev_call(g, 0.4, 20))
    yield "ev_call_0.25_cost_100", (lambda g=g: ev_call(g, 0.25, 100))


def run_all():
    results = {}
    for i, (name, fn) in enumerate(scenarios()):
        random.seed(1000 + i)  # reseed before every call so each result is independent
        results[name] = fn()
    return results


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    if mode not in ("record", "check"):
        print(__doc__)
        sys.exit(2)

    results = run_all()

    if mode == "record":
        with open(BASELINE_FILE, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Recorded {len(results)} results to {BASELINE_FILE}")
        return

    if not os.path.exists(BASELINE_FILE):
        print("No baseline.json yet. Run: python baseline.py record")
        sys.exit(2)
    with open(BASELINE_FILE) as f:
        expected = json.load(f)

    mismatches = []
    for name in sorted(set(expected) | set(results)):
        if name not in results:
            mismatches.append((name, expected[name], "MISSING"))
        elif name not in expected:
            mismatches.append((name, "MISSING", results[name]))
        elif results[name] != expected[name]:
            mismatches.append((name, expected[name], results[name]))

    if not mismatches:
        print(f"OK: all {len(results)} results match the baseline exactly.")
        return
    print(f"MISMATCH in {len(mismatches)} of {len(results)} scenarios:")
    for name, old, new in mismatches:
        print(f"  {name}: baseline={old} now={new}")
    sys.exit(1)


if __name__ == "__main__":
    main()
