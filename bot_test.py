import game

test_hands = [["Ad", "Ah"], ["Ah", "Kh"], ["Kd", "Kh"], 
              ["Qd", "Qh"], ["Ad", "Qd"], ["Jd", "Jh"],
              ["7d", "6d",], ["5d", "5h"], ["Td", "9d"],
              ["7d", "2h"], ["Jd", "3h"]]

# vary board texture too
test_board_cards = [[], ["2c", "8d", "Ks"], ["Ac", "Kd", "2s"], ["8c", "9d", "Th"], ["2h", "7h", "Kh"],["9h", "Th", "Jh"],["2c", "8d", "Ks"]]

# Driest: rainbow, disconnected, mixed rank — ["2c", "8d", "Ks"]. All three components near their low end.
# - Wettest: monotone, tightly connected, high cards — ["9h", "Th", "Jh"]. Maxes out all three components at once (flush-possible, straight-possible, big cards).
# - Isolate the suit axis: monotone but spread-out/disconnected ranks — ["2h", "7h", "Kh"]. Tests whether a flush-heavy-but-not-straighty board is scored as meaningfully "wet" on its own.
# - Isolate the rank axis: connected ranks but rainbow suits — ["8c", "9d", "Th"]. Tests the straight-heavy-but-no-flush case in isolation.
# - High cards, low connectivity: e.g. ["Ac", "Kd", "2s"] — big cards but spread out and rainbow, to see how much the high-card-ness term alone moves the score.


# vary num opponents:


for own_hand in test_hands:
    for cards in test_board_cards:

        pg = game.PokerGame(
            own_hand=own_hand,      
            own_pos="BTN", own_seat=1,
            occupied_seats=[1, 2, 3, 4],
            stacks={1: 200, 2: 200, 3: 200, 4: 200},
            board_cards=cards
        )
        pg.pot.add_contribution(2, 2)  # simulate some preflop action into the pot

        for bet in [4, 10, 20, 50, 100, 200]:
            if len(cards) == 0:
                print(bet, pg.calculate_ev_raise(bet, betting_round=0, seat=1, hand=own_hand))
            else:
                print(bet, pg.calculate_ev_raise(bet, betting_round=0, seat=1, hand=own_hand))