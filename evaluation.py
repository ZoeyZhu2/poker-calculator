from collections import Counter
import itertools


# Question: can I make this caching permanent?
# caching to reduce computation time as I run this a lot
parsed_cards = {}
cached_hands = {}
rank_map = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}

def parse_card(card:str):
    # card will be a two card string of the form "13h" (rank, suit)
    # ranks are as follows: 2 -> 14 for 2, 3, .. ., J, Q, K, A
    # suits are as follows: s, d, h, c for spades, diamonds, hearts, clubs
    # Throw an error if the card is not of the right format
    if card in parsed_cards:
        return parsed_cards[card]
    rank_key = card[:len(card) - 1]
    rank = rank_map[rank_key]
    suit = card[-1] 
    parsed_cards[card] = (rank, suit)
    return parsed_cards[card]

def parse_cards(cards):
    # indiv cards will be of the form "Ts" (rank suit)
    # cards will be a list of cards
    cards_parsed = []
    for card in cards:
        cards_parsed.append(parse_card(card))
    return cards_parsed

def evaluate_hand(hand): # can evaluate 5
    # hand will be a list of cards
    # the cards will be of the form "Ts" (rank suit)
    # Throw an error if the hand is not of the correct form
    if len(hand) < 5:
        raise ValueError(f"Need 5+ cards, got {len(hand)}")
    if len(hand) > 5:
        raise ValueError(f"Too many cards: {len(hand)}")
    hand_list = sorted(hand) # ensures resulting tuples are the same
    hand_tuple = tuple(hand_list)
    if hand_tuple in cached_hands:
        return cached_hands[hand_tuple]
    cards_parsed = parse_cards(hand)

    suits = [card[1] for card in cards_parsed]
    num_h = suits.count("h")
    num_d = suits.count("d")
    num_s = suits.count("s")
    num_c = suits.count("c")
    flush = False
    if num_h == 5 or num_d == 5 or num_s == 5 or num_c == 5:
        flush = True

    ranks = [card[0] for card in cards_parsed]
    ranks = sorted(ranks)
    rank_freq = Counter(ranks) # creates dict of element: frequency
    freq_list = sorted(rank_freq.values(), reverse=True)
    quad_rank = [rank for rank, freq in rank_freq.items() if freq == 4]
    trip_rank = [rank for rank, freq in rank_freq.items() if freq == 3]
    pairs_rank = sorted([rank for rank, freq in rank_freq.items() if freq == 2], reverse=True)
    singles_rank = sorted([rank for rank, freq in rank_freq.items() if freq == 1], reverse=True)

    handtype = None

    if flush: 
        handtype = (5, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
    if len(singles_rank) == 5:
        if singles_rank[0] - singles_rank[-1] == 4 or (singles_rank[0] == 14 and singles_rank[1] == 5 and singles_rank[-1] == 2):
            if flush: # straight flush
                # will override handtype from flush
                handtype = (8, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
                if singles_rank[4] == 2:
                    handtype = (8, singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4], singles_rank[0])
            else: # straight
                handtype = (4, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
                if singles_rank[4] == 2:
                    handtype = (4, singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4], singles_rank[0])
        else: 
            if handtype is None:  # make sure this doesn't override flush
            # high card
                handtype = (0, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
    elif len(quad_rank) > 0:
        # will override handtype from flush
        handtype = (7, quad_rank[0], singles_rank[0])
    elif len(trip_rank) > 0:
        if len(pairs_rank) > 0:
            # will override handtype from flush
            handtype = (6, trip_rank[0], pairs_rank[0])
        else:
            if handtype is None: # make sure this doesn't override straight, flush, or straight flush
                handtype = (3, trip_rank[0], singles_rank[0], singles_rank[1])
    elif len(pairs_rank) > 0:
        if handtype is None: # make sure this doesn't override anything else above (straight, flush, full house, straight flush, quad)
            if len(pairs_rank) > 1: 
                handtype = (2, pairs_rank[0], pairs_rank[1], singles_rank[0])
            else: 
                handtype = (1, pairs_rank[0], singles_rank[0], singles_rank[1], singles_rank[2])
    cached_hands[hand_tuple] = handtype
    return cached_hands[hand_tuple]

# Test cases
# print(evaluate_hand(['2h', '2d', 'As', 'Kc', 'Qh']))  # List
# print(evaluate_hand(['9h', '8d', '7c', '6s', '5h']))  # Straight
# print(evaluate_hand(['Ah', '5d', '4c', '3s', '2h']))  # Wheel


# evaluates best five card hand from seven cards
def evaluate_from_seven(seven_cards):
    # seven_cards is a list of seven cards
    five_card_combos = itertools.combinations(seven_cards, 5)
    best = None
    for combo in five_card_combos:
        result = evaluate_hand(combo)
        if best is None or result > best:
            best = result
    return best