import pot

board = ["2c", "7d", "9h", "Js", "3c"]

def run(contribs, hands):
    p = pot.Pot()
    for seat, amt in contribs.items():
        p.add_contribution(seat, amt)
    result = dict(p.calculate_payout(hands, board))
    assert sum(result.values()) == sum(contribs.values()), "chips lost or created"
    return result

aces, kings, queens = ["Ah", "Ad"], ["Kh", "Kd"], ["Qh", "Qd"]

# 1: one winner, equal contributions
print(run({1: 100, 2: 100, 3: 100}, {1: aces, 2: kings, 3: queens}))  # {1: 300}
# 2: short stack wins main pot only
print(run({1: 50, 2: 100, 3: 100}, {1: aces, 2: kings, 3: queens}))   # {1: 150, 2: 100}
# 3: tie with an odd chip
print(run({1: 1, 2: 1, 3: 1}, {1: ["Ah", "Kd"], 2: ["As", "Kc"], 3: ["6h", "4d"]}))  # {1: 2, 2: 1}
# 4: uncalled bet refunded
print(run({1: 100, 2: 40}, {1: kings, 2: aces}))  # {2: 80, 1: 60}