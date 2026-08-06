import game

class pot():

    def __init__(self):
        self.player_contributions = {"UTG": 0, "UTG+1": 0, "UTG+2": 0, "LJ": 0, "HJ": 0, "CO": 0, "BTN": 0, "SB": 0, "BB": 0}
        # players -> contributions

    def add_contribution(self, player_pos, amount):
        self.player_contributions[player_pos] += amount

    # need to remove players who lose

    def calculate_side_pots(self):
        positions_in = game.get_positions_in()
        remaining_players = list()
        for position in positions_in:
            if positions_in[position] is True:
                remaining_players.append(position)
        contributions = dict() # contribution -> players
        for player in remaining_players:
            if contributions[self.player_contributions[player]] is None:
                contributions[self.player_contributions[player]] = [player]
            else:
                contributions[self.player_contributions[player]].append(player)
        num_side_pots = len(contributions)
        

