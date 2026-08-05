import itertools

DEFAULT_RANGES = {
    'UTG': 0.08,      # AA-TT, AK, AQ
    'UTG+1': 0.10,    # AA-99, AK, AQ, AJ
    'UTG+2': 0.12,    # AA-88, AK, AQ, AJ, KQ
    'LJ': 0.15,       # AA-77, AK, AQ, AJ, KQ, KJ
    'HJ': 0.18,       # AA-77, AK-AJ, KQ-KJ, QJ
    'CO': 0.25,       # AA-66, AK-AJ, KQ-KJ, QJ, JT
    'BTN': 0.35,      # AA-44, AK-AT, KQ-KJ, QJ-QT, JT-J9
    'SB': 0.50,       # Lots of hands
    'BB': 0.70        # Can call cheap
}

HEADS_UP_RANGES = {
    'BTN': 0.75,   # BTN/SB opens ~75% of hands heads-up
    'BB': 0.85     # BB defends very wide against that
}

# from https://www.preflophands.com/
HAND_STRENGTH = ["AA", "KK", "QQ", "AKs", "JJ", "AQs", "KQs", "AJs", "KJs", "TT", 
                 "AKo", "ATs", "QJs", "KTs", "QTs", "JTs", "99", "AQo", "A9s", "KQo", 
                 "88", "K9s", "T9s", "A8s", "Q9s", "J9s", "AJo", "A5s", "77", "A7s",
                 "KJo", "A4s", "A3s", "A6s", "QJo", "66", "K8s", "T8s", "A2s", "98s",
                 "J8s", "ATo", "Q8s", "K7s", "KTo", "55", "JTo", "87s", "QTo", "44", 
                 "33", "22", "K6s", "97s", "K5s", "76s", "T7s", "K4s", "K3s", "K2s",
                 "Q7s", "86s", "65s", "J7s", "54s", "Q6s", "75s", "96s", "Q5s", "64s", 
                 "Q4s", "Q3s", "T9o", "T6s", "Q2s", "A9o", "53s", "85s", "J6s", "J9o",
                 "K9o", "J5s", "Q9o", "43s", "74s", "J4s", "J3s", "95s", "J2s", "63s",
                 "A8o", "52s", "T5s", "84s", "T4s", "T3s", "42s", "T2s", "98o", "T8o",
                 "A5o", "A7o", "73s", "A4o", "32s", "94s", "93s", "J8o", "A3o", "62s",
                 "92s", "K8o", "A6o", "87o", "Q8o", "83s", "A2o", "82s", "97o", "72s",
                 "76o", "K7o", "65o", "T7o", "K6o", "86o", "54o", "K5o", "J7o", "75o",
                 "Q7o", "K4o", "K3o", "96o", "K2o", "64o", "Q6o", "53o", "85o", "T6o",
                 "Q5o", "43o", "Q4o", "Q3o", "74o", "Q2o", "J6o", "63o", "J5o", "95o",
                 "52o", "J4o", "J3o", "42o", "J2o", "84o", "T5o", "T4o", "32o", "T3o",
                 "73o", "T2o", "62o", "94o", "93o", "92o", "83o", "82o", "72o"]

DECK = {"2c", "3c", "4c", "5c", "6c", "7c", "8c", "9c", "Tc", "Jc", "Qc", "Kc", "Ac", 
        "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d", "Td", "Jd", "Qd", "Kd", "Ad",
        "2h", "3h", "4h", "5h", "6h", "7h", "8h", "9h", "Th", "Jh", "Qh", "Kh", "Ah", 
        "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "Ts", "Js", "Qs", "Ks", "As"}

def get_range_hands(position: str, heads_up=False, num_hands=1326):
    """Returns list of all hands in that percentile"""
    ranges = HEADS_UP_RANGES if heads_up else DEFAULT_RANGES
    max_index = (int)(169 * ranges[position])
    top_hands = HAND_STRENGTH[0:max_index]
    card_combos = []
    for hand in top_hands:
        card_combos.extend(hand_name_to_cards(hand))
    return card_combos

def hand_name_to_cards(hand):
    cards = []
    suits = ["c", "d", "h", "s"]
    if len(hand) == 2:
        suit_combos = itertools.combinations(suits, 2)
        for suit1, suit2 in suit_combos:
            cards.append([hand[0] + suit1, hand[0] + suit2])
    elif hand[2] == "s":
        for suit in suits:
            cards.append([hand[0] + suit, hand[1] + suit])
    else:
        for suit1 in suits:
            for suit2 in suits:
                if suit1 != suit2:
                    cards.append([hand[0] + suit1, hand[1] + suit2])
    return cards