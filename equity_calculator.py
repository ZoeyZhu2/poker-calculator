import evaluation
import itertools
import random
import numpy as np

# should I use list or set for deck (probably set for quick remove, right?)
deck = {"2c", "3c", "4c", "5c", "6c", "7c", "8c", "9c", "Tc", "Jc", "Qc", "Kc", "Ac", 
        "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d", "Td", "Jd", "Qd", "Kd", "Ad",
        "2h", "3h", "4h", "5h", "6h", "7h", "8h", "9h", "Th", "Jh", "Qh", "Kh", "Ah", 
        "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s", "Ts", "Js", "Qs", "Ks", "As"}

# Calculate equity for two players 
# def calculate_equity(pocket1, pocket2, community_cards, num_simulations=-1):
#     # pocket1, pocket2: list of 2 cards each (e.g., ['Ah', 'Kd'])
#     # community_cards: list of 0-4 cards (e.g., ['5h', '5c', '5d'])
#     # returns: float between 0 and 1 (win probability of pocket 1)
    
#     if len(community_cards) == 5:
#         hand1 = evaluation.evaluate_hand(pocket1 + community_cards)
#         hand2 = evaluation.evaluate_hand(pocket2 + community_cards)
#         if hand1 > hand2:
#             return 1.0
#         elif hand1 == hand2:
#             return 0.5
#         else:
#             return 0.0

#     known_cards = pocket1 + pocket2 + community_cards
#     remaining_deck = deck - set(known_cards)
#     num_cards_needed = 5 - len(community_cards)

#     wins = 0
#     total = 0

#     # the exact way
#     if num_simulations == -1:
#         futures = itertools.combinations(remaining_deck, num_cards_needed) # returns list of tuples
#         for future in futures:
#             total += 1
#             board = community_cards + list(future)
#             hand1 = evaluation.evaluate_from_seven(pocket1 + board)
#             hand2 = evaluation.evaluate_from_seven(pocket2 + board)
#             if hand1 > hand2:
#                 wins += 1
#             if hand1 == hand2:
#                 wins += 0.5
#     # faster approximation
#     else:
#         for _ in range(num_simulations):
#             future = random.sample(list(remaining_deck), num_cards_needed)
#             total += 1
#             board = community_cards + future
#             hand1 = evaluation.evaluate_from_seven(pocket1 + board)
#             hand2 = evaluation.evaluate_from_seven(pocket2 + board)
#             if hand1 > hand2:
#                 wins += 1
#             if hand1 == hand2:
#                 wins += 0.5
#     return wins/total

# N number of players
def calculate_equity(pockets_list, community_cards, num_simulations=-1):
    # pockets_list: list of each player's pocket, which is a list of 2 cards (e.g., ['Ah', 'Kd'])
    # community_cards: list of 0-4 cards (e.g., ['5h', '5c', '5d'])
    # returns: float between 0 and 1 (win probability of pocket 1)
    equities_list = [0] * len(pockets_list)

    # if all cards are dealt out
    if len(community_cards) == 5:
        evaluated_hands = list()
        best_indices = list() # implement a queue
        best_hand = None
        for index, pocket in enumerate(pockets_list):
            evaluated_hand = evaluation.evaluate_from_seven(pocket + community_cards)
            evaluated_hands.append(evaluated_hand)
            if best_hand is None or evaluated_hand >= best_hand:
                if best_hand is not None and evaluated_hand > best_hand:
                    best_indices.clear()
                best_indices.append(index)
                best_hand = evaluated_hand
        equity = 1.0 / len(best_indices)
        for index in best_indices:
            equities_list[index] = equity
        return equities_list        

    known_cards = list()
    for pocket in pockets_list:
        known_cards.extend(pocket)
    known_cards.extend(community_cards)
    remaining_deck = deck - set(known_cards) # this is a set
    num_cards_needed = 5 - len(community_cards)
   
    wins = np.zeros(len(pockets_list))
    total = 0

    # the exact way
    if num_simulations == -1:
        futures = itertools.combinations(list(remaining_deck), num_cards_needed) # returns list of tuples
        for future in futures:
            total += 1
            board = community_cards + list(future)
            all_hand_ranks = list()
            current_wins = np.zeros(len(pockets_list))
            for index, pocket in enumerate(pockets_list):
                hand_rank = evaluation.evaluate_from_seven(pocket + board)
                all_hand_ranks.append(hand_rank)
                # if best_rank is None or hand_rank >= best_rank:
                #     num_best += 1
                #     if hand_rank > best_rank:
                #         num_best = 1
                #         current_wins[:] = 0
                #         current_wins[index] += 1
                #     if hand_rank == best_rank:
                #         current_wins[index] += 1
                #         current_wins[:] = current_wins[:]/num_best # divide current values by num_best
                #     best_rank = hand_rank
            best_rank = max(all_hand_ranks)
            best_rank_indices = list()
            for index, rank in enumerate(all_hand_ranks):
                if rank == best_rank:
                    best_rank_indices.append(index)
            equity = 1.0 / len(best_rank_indices)
            for index in best_rank_indices:
                current_wins[index] = equity
            wins = wins + current_wins
    # faster approximation
    else:
        for _ in range(num_simulations):
            future = random.sample(list(remaining_deck), num_cards_needed)
            total += 1
            board = community_cards + list(future)
            all_hand_ranks = list()
            current_wins = np.zeros(len(pockets_list))
            for index, pocket in enumerate(pockets_list):
                hand_rank = evaluation.evaluate_from_seven(pocket + board)
                all_hand_ranks.append(hand_rank)
                # if best_rank is None or hand_rank >= best_rank:
                #     num_best += 1
                #     if hand_rank > best_rank:
                #         num_best = 1
                #         current_wins[:] = 0
                #         current_wins[index] += 1
                #     if hand_rank == best_rank:
                #         current_wins[index] += 1
                #         current_wins[:] = current_wins[:]/num_best # divide current values by num_best
                #     best_rank = hand_rank
            best_rank = max(all_hand_ranks)
            best_rank_indices = list()
            for index, rank in enumerate(all_hand_ranks):
                if rank == best_rank:
                    best_rank_indices.append(index)
            equity = 1.0 / len(best_rank_indices)
            for index in best_rank_indices:
                current_wins[index] = equity
            wins = wins + current_wins
    return wins/total

# # Test
# # 3 players, flat board
# equity = calculate_equity(
#     [['Ah', 'Kh'], ['Ad', 'Kd'], ['2c', '3c']],
#     ['5h', '5c', '5d']
# )
# print(f"Calculated equity: {equity}; expected equity: [0.35, 0.35, 0.30]")

# # Same pocket (tie)
# equity = calculate_equity(
#     [['Ah', 'Kh'], ['Ah', 'Kh']],
#     ['5h', '5c', '5d']
# )
# print(f"Calculated equity: {equity}; expected equity: [0.5, 0.5]")
