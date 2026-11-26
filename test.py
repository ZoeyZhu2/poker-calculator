"""Unit tests for bot.bot.decision.

These use a stub game whose calculate_ev_raise is a plain function of the bet
size, so results are exact and repeatable (no equity simulations). Run with:

    python test.py

(also works under pytest, since every check is a test_* function).
"""
import random
import bot

BB = 10
POT = 100


class StubGame:
    """Stands in for PokerGame: bot.decision only calls calculate_ev_raise."""

    def __init__(self, ev_fn):
        self.ev_fn = ev_fn

    def calculate_ev_raise(self, bet, betting_round, seat=None, hand=None, n_sims=1000):
        return self.ev_fn(bet)


def decide(ev_fn, *, volatility=0.0, aggressiveness=0.0, looseness=1.0, bet_sizing=0.5,
           stack=1000, ev_call=0.0, pot=POT, cost_to_call=0, big_blind=BB):
    """Build a bot with the given traits and return its (action, amount)."""
    b = bot.bot(volatility, aggressiveness, looseness, bet_sizing)
    return b.decision(StubGame(ev_fn), 1, ["Ah", "Kh"], stack, ev_call, 1, pot, cost_to_call, big_blind)


def peaked(center, height=50.0, slope=0.01):
    """EV that is highest at `center` and falls off slowly on both sides."""
    return lambda bet: height - slope * abs(bet - center)


def flat(value):
    return lambda bet: value


# ---------- stack guards ----------

def test_zero_stack_is_side_pot():
    assert decide(flat(10), stack=0) == ("side pot", 0)


def test_negative_stack_exits():
    assert decide(flat(10), stack=-5) == ("exit", 0)


# ---------- fold / call / check ----------

def test_never_folds_when_nothing_to_call():
    # everything is terrible, but folding is illegal when cost_to_call == 0
    action, amount = decide(flat(-100), ev_call=-100, cost_to_call=0)
    assert action == "check" and amount == 0


def test_folds_when_everything_is_losing():
    action, _ = decide(flat(-5), ev_call=-3, cost_to_call=10)
    assert action == "fold"


def test_calls_when_call_is_best():
    action, amount = decide(flat(-5), ev_call=4, cost_to_call=10)
    assert (action, amount) == ("call", 10)


def test_call_is_capped_at_stack_and_has_no_raise():
    # cost_to_call (50) > stack (5): calling is all-in, so no raise exists
    action, amount = decide(flat(1000), ev_call=3, cost_to_call=50, stack=5)
    assert (action, amount) == ("call", 5)


# ---------- raise legality ----------

def test_raise_respects_min_raise_and_stack():
    for stack in (15, 40, 120, 1000):
        for cost in (0, 10, 30):
            action, amount = decide(flat(20), ev_call=0, cost_to_call=cost, stack=stack, aggressiveness=1.0)
            if action == "raise":
                min_raise = cost + BB
                assert amount <= stack
                assert amount >= min_raise or amount == stack, (stack, cost, amount)


def test_all_in_is_always_a_candidate():
    # EV grows with bet size, so the biggest candidate (all-in) should win
    action, amount = decide(lambda bet: bet * 0.1, ev_call=0, stack=500)
    assert (action, amount) == ("raise", 500)


# ---------- aggressiveness ----------

def test_aggressiveness_flips_call_into_raise():
    ev_fn = peaked(50, height=4.5)  # best raise EV 4.5, just under the call EV of 5
    passive, _ = decide(ev_fn, ev_call=5, cost_to_call=10, aggressiveness=0.0)
    aggressive, _ = decide(ev_fn, ev_call=5, cost_to_call=10, aggressiveness=1.0)
    assert passive == "call"
    assert aggressive == "raise"


def test_aggressiveness_never_makes_losing_raise_beat_fold():
    for aggressiveness in (0.0, 0.5, 1.0):
        action, _ = decide(flat(-1), ev_call=-3, cost_to_call=10, aggressiveness=aggressiveness)
        assert action == "fold", aggressiveness


# ---------- looseness ----------

def test_loose_bot_calls_what_tight_bot_folds():
    # marginal spot: call EV is a little below zero, raises are clearly bad
    tight, _ = decide(flat(-50), ev_call=-3, cost_to_call=10, looseness=0.5)
    loose, _ = decide(flat(-50), ev_call=-3, cost_to_call=10, looseness=1.5)
    assert tight == "fold", "tight bot should fold a slightly -EV call"
    assert loose == "call", "loose bot should call a slightly -EV call"


def test_tight_bot_folds_what_normal_bot_calls_when_ev_is_small_positive():
    tight, _ = decide(flat(-50), ev_call=3, cost_to_call=10, looseness=0.5)
    normal, _ = decide(flat(-50), ev_call=3, cost_to_call=10, looseness=1.0)
    assert normal == "call"
    assert tight == "fold"


def test_looseness_also_gates_raising():
    # a tight bot should not raise a marginal spot that a loose bot would raise
    ev_fn = flat(3)
    tight, _ = decide(ev_fn, ev_call=-50, cost_to_call=10, looseness=0.5)
    loose, _ = decide(ev_fn, ev_call=-50, cost_to_call=10, looseness=1.5)
    assert tight == "fold"
    assert loose == "raise"


# ---------- volatility ----------

def test_zero_volatility_is_deterministic():
    results = {decide(peaked(50), ev_call=0.2, cost_to_call=14) for _ in range(30)}
    assert len(results) == 1


def test_volatility_flips_borderline_decisions():
    random.seed(0)
    actions = {decide(flat(-50), volatility=1.0, ev_call=0.5, cost_to_call=14)[0] for _ in range(200)}
    assert actions == {"fold", "call"}, actions


def test_bigger_big_blind_means_more_noise():
    random.seed(1)

    def flips(bb):
        n = 0
        for _ in range(300):
            action, _ = decide(flat(-1000), volatility=1.0, ev_call=3, cost_to_call=14, big_blind=bb)
            n += action == "fold"
        return n

    # ev_call = 3 vs noise of +/- bb: a tiny bb rarely flips it, a big one often does
    assert flips(1) < flips(50)


# ---------- bet sizing ----------

def chosen_raise(bet_sizing, ev_fn=None, **kw):
    ev_fn = ev_fn or peaked(50)
    action, amount = decide(ev_fn, bet_sizing=bet_sizing, ev_call=0, **kw)
    assert action == "raise", action
    return amount


def test_bet_sizing_baseline_picks_max_ev_size():
    assert chosen_raise(0.5) == 50


def test_bet_sizing_moves_size_in_the_right_direction():
    small, mid, big = chosen_raise(0.0), chosen_raise(0.5), chosen_raise(1.0)
    assert small < mid < big, (small, mid, big)


def test_bet_sizing_cannot_rescue_a_terrible_size():
    # every size is nearly equal except all-in, which is awful
    ev_fn = lambda bet: -100 if bet == 1000 else 50 - 0.01 * abs(bet - 50)
    assert chosen_raise(1.0, ev_fn) != 1000


def test_bet_sizing_does_not_leak_into_raise_vs_call():
    # best raise EV (4.5) is below call EV (5). A high bet_sizing must only change
    # WHICH raise size is picked, never turn the call into a raise.
    ev_fn = peaked(50, height=4.5)
    for bet_sizing in (0.0, 0.5, 1.0):
        action, _ = decide(ev_fn, bet_sizing=bet_sizing, ev_call=5, cost_to_call=10)
        assert action == "call", bet_sizing


# ---------- randomized legality sweep ----------

def test_random_situations_are_always_legal():
    random.seed(42)
    legal_actions = {"fold", "check", "call", "raise"}
    for _ in range(2000):
        bb = random.choice([2, 10, 50, 200])
        stack = random.randint(1, 5000)
        pot = random.randint(bb, 3000)
        cost = random.choice([0, random.randint(1, 2 * bb), random.randint(1, 6000)])
        ev_table = {}
        ev_fn = lambda bet: ev_table.setdefault(bet, random.uniform(-3 * bb, 3 * bb))
        action, amount = decide(
            ev_fn,
            volatility=random.random(), aggressiveness=random.random(),
            looseness=random.uniform(0.5, 1.5), bet_sizing=random.random(),
            stack=stack, ev_call=random.uniform(-3 * bb, 3 * bb),
            pot=pot, cost_to_call=cost, big_blind=bb,
        )
        info = dict(stack=stack, pot=pot, cost=cost, bb=bb, action=action, amount=amount)
        assert action in legal_actions, info
        capped = min(cost, stack)
        if action == "fold":
            assert cost > 0, info
        elif action == "check":
            assert cost == 0 and amount == 0, info
        elif action == "call":
            assert cost > 0 and amount == capped, info
        else:
            assert stack > capped, info
            assert amount <= stack, info
            assert amount >= capped + bb or amount == stack, info


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            failed.append(name)
            print(f"FAIL  {name}  {e}")
        except Exception as e:  # a crash is also a failure, but keep running the rest
            failed.append(name)
            print(f"ERROR {name}  {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
