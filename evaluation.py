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
    ranks = [card[0] for card in cards_parsed]
    ranks = sorted(ranks)
    suits = [card[1] for card in cards_parsed]
    num_h = suits.count("h")
    num_d = suits.count("d")
    num_s = suits.count("s")
    num_c = suits.count("c")
    flush = False
    if num_h == 5 or num_d == 5 or num_s == 5 or num_c == 5:
        flush = True
    ranks = tuple(ranks)
    suits = tuple(suits)
    # count frequency of cards. Note that ranks are sorted in ascending order
    n1 = ranks.count(ranks[0])
    n2 = ranks.count(ranks[1])
    n3 =ranks.count(ranks[2])
    n4 =ranks.count(ranks[3])
    n5 = ranks.count(ranks[4])
    # if every card has a frequency of 1: straight flush, flush, straight, or high card
    if n1 == n2 == n3 == n4 == n5: 
        if ranks[4] - ranks[0] == 4 or (ranks[3] - ranks[0] == 3 and ranks[4] == 14): # must be a straight because no repeated ranks
            if flush: #straight flush
                handtype = (8, ranks[-1], ranks[-2], ranks[2], ranks[1], ranks[0])
            else: # straight
                handtype = (4, ranks[-1], ranks[-2], ranks[2], ranks[1], ranks[0])
        elif flush: #flush
            handtype = (4, ranks[-1], ranks[-2], ranks[2], ranks[1], ranks[0])
        else: # high card
            handtype = (0, ranks[-1], ranks[-2], ranks[2], ranks[1], ranks[0])
        # just be careful when I later compare hands to check the first and last cards in the straight for wheels

    # if quad
    if n1 == 4: 
        handtype = (7, ranks[0], ranks[4])
    if n5 == 4:
        handtype = (7, ranks[4], ranks[0])

    # if there"s a triple: either full house or set
    if n1 == 3:
        if n5 == 2:
            handtype = (6, ranks[0], ranks[4])
        else:
            handtype = (3, ranks[0], ranks[4], ranks[3])
    if n5 == 3:
        if n1 == 2:
            handtype = (6, ranks[4], ranks[0])
        else:
            handtype = (3, ranks[4], ranks[1], ranks[0])
    if n2 == 3: # must be a set
        handtype = (3, ranks[1], ranks[4], ranks[0])
   
    # if there"s a pair: full house, two pair, or one pair
    # already checked for full house, so eliminate that now...
    if n1 == 2 and n3 != 3: # if a pair and not another set
        if n3 == 2: # two pair
            handtype = (2, ranks[2], ranks[0], ranks[4])
        elif n4 == 2: # two pair
            handtype = (2, n4, ranks[0], ranks[2])
        else: # one pair
            handtype = (1, ranks[0], ranks[4], ranks[3], ranks[2])
    if n5 == 2 and n1 != 3: # if a pair and not another set
        if n3 == 2: # two pair
            handtype = (2, ranks[4], ranks[2], ranks[0])
        elif n1 == 2: # two pair
            handtype = (2, ranks[4], ranks[0], ranks[2])
        else: # one pair
            handtype = (1, ranks[4], ranks[2], ranks[1], ranks[0])
    if n3 == 2: # full house not possible here
        if n5 == 2: # two pair
            handtype = (2, ranks[4], ranks[2], ranks[0])
        elif n1 == 2: # two pair
            handtype = (2, ranks[2], ranks[0], ranks[4])
        elif n4 == 2: # n3 and n4 part of same pair
            handtype = (1, ranks[2], ranks[4], ranks[1], ranks[0]) 
        else: # n2 and n3 part of same pair
            handtype = (1, ranks[2], ranks[4], ranks[3], ranks[0])

    cached_hands[hand] = handtype, ranks, suits
    return cached_hands[hand]

def compare_hands(hand1: str, hand2: str):
    # use evaluate hand?
    # 0: (0, rank1, rank2, rank3, rank4, rank5)           High card
    # 1: (1, pair_rank, kicker1, kicker2, kicker3)        Pair
    # 2: (2, pair1_rank, pair2_rank, kicker)              Two pair
    # 3: (3, trips_rank, kicker1, kicker2)                Three of a kind
    # 4: (4, low_card, ...)                               Straight
    # 5: (5, rank1, rank2, rank3, rank4, rank5)           Flush
    # 6: (6, trips_rank, pair_rank)                       Full house
    # 7: (7, quads_rank, kicker)                          Four of a kind
    # 8: (8, low_card, ...)


# Question: how to throw errors?