import evaluation
from collections import defaultdict


class pot():

    def __init__(self):
        self.player_contributions = {"UTG": 0, "UTG+1": 0, "UTG+2": 0, "LJ": 0, "HJ": 0, "CO": 0, "BTN": 0, "SB": 0, "BB": 0}
        # players -> contributions
        self.amount = 0

    def add_contribution(self, player_pos, amount):
        self.player_contributions[player_pos] += amount
        self.amount += amount

    def calculate_payout(self, player_cards, board_cards):
        # evaluate final equities of player_cards
        # if the winner(s) have the most contribution, they get all of the pot
        # otherwise, figure out how to split the side pot

        # player_cards is a dict: player position -> actual hand as a list ["Ah", "7s"]
        hands = {} # position -> evaluated hand
        for position, cards in player_cards.items():
            seven_cards = board_cards + cards
            hands[position] = evaluation.evaluate_from_seven(seven_cards)

        layers = dict() # contribution amount -> players involved
        for player, contribution in self.player_contributions.items():
            if contribution not in layers:
                layers[contribution] = [player]
            else:
                layers[contribution].append(player)

        contributions = sorted(layers.keys(), reverse=True) # contribution amounts in greatest to least
        for i in range(1, len(contributions)):
            layers[contributions[i]] += layers[contributions[i-1]]
        # now layers is contribution threshold -> players involved
        layer_amounts = dict()
        for i in range(0, len(contributions) - 1):
            layer_amounts[contributions[i]] = contributions[i] * len(layers[contributions[i]]) - contributions[i+1] * len(layers[contributions[i]])
            # need len(layer_amounts[contributions[i]]) for both terms because only the higher threshold players also overlap with the lower threshold
        layer_amounts[contributions[-1]] = contributions[-1] * len(layers[contributions[-1]])
        payouts = defaultdict(int) # player position -> payout amount

        for layer, players in layers.items():
            winners = list()
            best_hand = (0,0,0,0,0,0)
            for player in players:
                if player not in hands:
                    continue
                if hands[player] > best_hand:
                    best_hand = hands[player]
                    winners = [player]
                elif hands[player] == best_hand:
                    winners.append(player)
            for player in winners:
                payouts[player] += layer_amounts[layer] / len(winners)
    
        return payouts
        

