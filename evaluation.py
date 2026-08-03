from collections import Counter

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

def evaluate_hand(hand:str):
    # hand will be of the form "card1 card2 card3 card4 card5" where all cards are split by one space
    # the cards will be of the form "10s" (rank suit)
    # Throw an error if the hand is not of the correct form
    hand = hand.strip()
    if hand in cached_hands:
        return cached_hands[hand]
    cards_unparsed = hand.split()
    cards_parsed = []
    for card in cards_unparsed:
        cards_parsed.append(parse_card(card))

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
    if len(quad_rank) > 0:
        handtype = (7, quad_rank[0], singles_rank[0])
    elif len(trip_rank) > 0:
        if len(pairs_rank) > 0:
            handtype = (6, trip_rank[0], pairs_rank[0])
        else:
            handtype = (3, trip_rank[0], singles_rank[0], singles_rank[1])
    elif len(pairs_rank) > 0:
        if len(pairs_rank) > 1:
            handtype = (2, pairs_rank[0], pairs_rank[1], singles_rank[0])
        else:
            handtype = (1, pairs_rank[0], singles_rank[0], singles_rank[1], singles_rank[2])
    else:
        if singles_rank[0] - singles_rank[-1] == 4 or (singles_rank[0] == 14 and singles_rank[1] == 5 and singles_rank[4] == 2):
            if flush: # straight flush
                handtype = (8, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
                if singles_rank[4] == 2:
                    handtype = (8, singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4], singles_rank[0])
            else: # straght
                handtype = (4, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
                if singles_rank[4] == 2:
                    handtype = (4, singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4], singles_rank[0])
                            
        else:
            if flush: # flush
                handtype = (5, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
            else: # high card
                handtype = (0, singles_rank[0], singles_rank[1], singles_rank[2], singles_rank[3], singles_rank[4])
    cached_hands[hand] = handtype
    return cached_hands[hand]

# Test cases
print(evaluate_hand("2h 2d As Kc Qh"))  # Pair with 3 kickers
print(evaluate_hand("9h 8d 7c 6s 5h"))  # Straight
print(evaluate_hand("Ah 5d 4c 3s 2h"))  # Wheel (5-high straight)

def compare_hands(hand1: str, hand2: str):
    # generally, high to low order
    # 0: (0, rank1, rank2, rank3, rank4, rank5)           High card
    # 1: (1, pair_rank, kicker1, kicker2, kicker3)        Pair
    # 2: (2, highpair_rank, lowpair_rank, kicker)              Two pair
    # 3: (3, trips_rank, kicker1, kicker2)                Three of a kind
    # 4: (4, low_card, ...)                               Straight
    # 5: (5, rank1, rank2, rank3, rank4, rank5)           Flush
    # 6: (6, trips_rank, pair_rank)                       Full house
    # 7: (7, quads_rank, kicker)                          Four of a kind
    # 8: (8, high_card, ...)      

    # 0: High card
    # 1: Pair
    # 2: Two pair
    # 3: Three of a kind
    # 4: Straight
    # 5: Flush
    # 6: Full house     
    # 7: Four of a kind
    # 8: Straight flush
    pass
    # Question: how to throw errors