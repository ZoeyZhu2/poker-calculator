import evaluation
from collections import defaultdict


class Pot():

    def __init__(self):
        self.player_contributions = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0} # seat -> contribution
        # players -> contributions
        self.amount = 0
        self.last_contribution = 0

    def add_contribution(self, seat, amount):
        self.player_contributions[seat] += amount
        self.amount += amount
        self.last_contribution = amount

    def calculate_payout(self, player_cards, board_cards):
        # evaluate final equities of player_cards
        # if the winner(s) have the most contribution, they get all of the pot
        # otherwise, figure out how to split the side pot

        # player_cards is a dict: player seat -> actual hand as a list ["Ah", "7s"]
        hands = {} # seat -> evaluated hand
        for seat, cards in player_cards.items():
            if cards == ["", ""]: # player mucked
                continue
            seven_cards = board_cards + cards
            hands[seat] = evaluation.evaluate_from_seven(seven_cards)

        payouts = defaultdict(int) # player seat -> payout amount

        contributions = {seat: c for seat, c in self.player_contributions.items() if c > 0}
        prev_level = 0
        for level in sorted(set(contributions.values())):
            payers = [seat for seat, c in contributions.items() if c >= level]
            amount = (level - prev_level) * len(payers)
            prev_level = level

            if len(payers) == 1: # nobody called at this level
                payouts[payers[0]] += amount
                continue

            contenders = [seat for seat in payers if seat in hands]
            best = max(hands[seat] for seat in contenders)
            winners = [seat for seat in contenders if hands[seat] == best]
            share, remainder = divmod(amount, len(winners))
            for seat in winners:
                payouts[seat] += share
            payouts[winners[0]] += remainder # odd chip goes to the first winner
        
        return payouts

    def get_amount(self):
        return self.amount

    def get_player_contributions(self):
        return self.player_contributions


