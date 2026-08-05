import position_ranges
import equity_calculator
import random


positions = ["BTN", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]

class PokerGame:
    def __init__(self, own_hand, own_pos, num_players, board_cards):
        self.own_hand = own_hand
        self.own_pos = own_pos
        self.num_players = num_players
        self.board_cards = board_cards
        self.populate_positions(num_players)
        self.folded = set()

    def get_equity(self):
        ranges = dict()
        for key, value in self.positions_in.items():
            if value is True:
                ranges[key] = position_ranges.get_range_hands(key)
        pocket_list = [self.own_hand]
        selected_cards = set()
        for key, value in ranges.items():
            random_card = random.choice(value)
            random_card_tuple = tuple(random_card)
            if random_card_tuple not in selected_cards:
                selected_cards.add(random_card_tuple)
                pocket_list.append(random_card)

        print(f"pocket_list: {pocket_list}")  # Debug
        print(f"board: {self.board_cards}")  # Debug
        print(f"pocket_list[0] type: {type(pocket_list[0])}")  # ADD THIS
        print(f"pocket_list[1] type: {type(pocket_list[1])}")  # ADD THIS

        equity_list = equity_calculator.calculate_equity(pocket_list, self.board_cards, 10000)
        return equity_list[0]
    
    def fold_player(self, player_pos):
        self.positions_in[player_pos] = False

    def add_board_card(self, card):
        self.board_cards.append(card)

    def new_round(self, own_hand, num_players):
        # change everyone's positions by one
        self.own_hand = own_hand
        self.num_players = num_players
        self.populate_positions(num_players)


    def populate_positions(self, num_players):
        self.positions_in = {"UTG": False, "UTG+1": False, "UTG+2": False, "LJ": False, "HJ": False, "CO": False, "BTN": True, "SB": True, "BB": True}
        if num_players > 3:
            self.positions_in["UTG"] = True
        if num_players > 4: 
            self.positions_in["CO"] = True
        if num_players > 5: 
            self.positions_in["HJ"] = True
        if num_players > 6: 
            self.positions_in["LJ"] = True
        if num_players > 7: 
            self.positions_in["UTG+1"] = True
        if num_players > 8: 
            self.positions_in["UTG+2"] = True
        self.own_pos = positions[(positions.index(self.own_pos) + 1) % 9]
        while self.positions_in[self.own_pos] == False:
            self.own_pos = positions[(positions.index(self.own_pos) + 1) % 9]
        self.board_cards.clear()

    def get_own_pos(self):
        return self.own_pos


# Test the CLI game

# game = PokerGame(['Ah', 'Kh'], 'BTN', 3, [])
# print(f"3 players, BTN position, no board")
# print(f"Your hand: AKs")
# print(f"Equity: {game.get_equity():.2%}")

# game.add_board_card('5h')
# game.add_board_card('5c')
# game.add_board_card('5d')
# print(f"\nAdded flop: 5h 5c 5d")
# print(f"Equity: {game.get_equity():.2%}")

# game.fold_player('SB')
# print(f"\nSB folded (2 players left)")
# print(f"Equity: {game.get_equity():.2%}")

# game.add_board_card('2s')
# print(f"\nAdded turn: 2s")
# print(f"Equity: {game.get_equity():.2%}")

# game.add_board_card('3c')
# print(f"\nAdded river: 3c")
# print(f"Equity: {game.get_equity():.2%}")