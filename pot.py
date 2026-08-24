import evaluation
from collections import defaultdict


class Pot():

    def __init__(self):
        self.player_contributions = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0} # seat -> contribution
        # players -> contributions
        self.amount = 0

    def add_contribution(self, seat, amount):
        self.player_contributions[seat] += amount
        self.amount += amount

    def calculate_payout(self, player_cards, board_cards):
        # evaluate final equities of player_cards
        # if the winner(s) have the most contribution, they get all of the pot
        # otherwise, figure out how to split the side pot

        # player_cards is a dict: player seat -> actual hand as a list ["Ah", "7s"]
        hands = {} # seat -> evaluated hand
        for seat, cards in player_cards.items():
            seven_cards = board_cards + cards
            hands[seat] = evaluation.evaluate_from_seven(seven_cards)

        layers = dict() # contribution amount -> players involved
        for seat, contribution in self.player_contributions.items():
            if contribution not in layers:
                layers[contribution] = [seat]
            else:
                layers[contribution].append(seat)

        contributions = sorted(layers.keys(), reverse=True) # contribution amounts in greatest to least
        for i in range(1, len(contributions)):
            layers[contributions[i]] += layers[contributions[i-1]]
        # now layers is contribution threshold -> players involved
        layer_amounts = dict()
        for i in range(0, len(contributions) - 1):
            layer_amounts[contributions[i]] = contributions[i] * len(layers[contributions[i]]) - contributions[i+1] * len(layers[contributions[i]])
            # need len(layer_amounts[contributions[i]]) for both terms because only the higher threshold players also overlap with the lower threshold
        layer_amounts[contributions[-1]] = contributions[-1] * len(layers[contributions[-1]])
        payouts = defaultdict(int) # player seat -> payout amount

        for layer, seats in layers.items():
            winners = list()
            best_hand = (0,0,0,0,0,0)
            for seat in seats:
                if seat not in hands:
                    continue
                if hands[seat] > best_hand:
                    best_hand = hands[seat]
                    winners = [seat]
                elif hands[seat] == best_hand:
                    winners.append(seat)
            for seat in winners:
                payouts[seat] += layer_amounts[layer] / len(winners)
    
        return payouts

    def get_amount(self):
        return self.amount

    def get_player_contributions(self):
        return self.player_contributions

