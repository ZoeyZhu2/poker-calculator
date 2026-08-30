import position_ranges
import equity_calculator
import random
import numpy as np
import pot


positions = ["BTN", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]


class PokerGame:
    def __init__(self, own_hand: list, own_pos: str, own_seat: int, occupied_seats: list, board_cards: list):
        # own_hand is a list of two cards ex: ["Ah", "Kd"]
        self.own_hand = own_hand
        # own_pos is a string representing position ex: "BTN"
        self.own_pos = own_pos
        # own_seat is an integer representing seat number
        self.own_seat = own_seat
        # occupied_seats is a list of integers
        self.occupied_seats = occupied_seats
        self.num_players = len(occupied_seats)
        # board cards is a list of any community cards already dealt out ex: ["2s", "7d", "5h"]
        self.board_cards = board_cards
        self.populate_positions(occupied_seats)
        # folded keeps track of folded cards. Not used right now.
        self.folded = set()
        # pot keeps track of the pot
        self.pot = pot.Pot()
        # seat -> bot for mode 1
        self.bots = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}
        # seat -> looseness for mode 2 (eventually volatility and aggressiveness will be added)
        self.traits = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0}
        
    def update_traits(self, seat: int, looseness):
        self.traits[seat] = looseness

    # getting range equities (so an estimation)
    def get_equity(self):
        heads_up = sum(self.seats_in.values()) == 2
        ranges = dict() # position -> all range hands
        for key, value in self.seats_in.items():
            if key == self.own_seat:
                continue
            if value is True:
                pos = self.rotation[key]
                ranges[pos] = position_ranges.get_range_hands(pos, heads_up=heads_up, looseness=self.traits[key])
        equities_sum = np.zeros(len(ranges) + 1)
        for i in range(10000):
            pocket_list = [self.own_hand]
            selected_cards = set()
            for card in self.own_hand:
                selected_cards.add(card)
            for card in self.board_cards:
                selected_cards.add(card)
            for key, value in ranges.items():
                random_cards = random.choice(value)
                card1, card2 = random_cards
                while card1 in selected_cards or card2 in selected_cards:
                    random_cards = random.choice(value)
                    card1, card2 = random_cards
                selected_cards.add(card1)
                selected_cards.add(card2)
                pocket_list.append(random_cards)
            # only testing one combination of community cards per combinations of hands:
            equity_list = equity_calculator.calculate_equity(pocket_list, self.board_cards, 1)
            equities_sum = equities_sum + np.array(equity_list)
        avg_equities = equities_sum / 10000    
        return avg_equities[0]
    
    def fold_player(self, seat):
        self.seats_in[seat] = False

    def player_bet(self, seat, amount):
        self.pot.add_contribution(seat, amount)

    def add_board_card(self, card):
        self.board_cards.append(card)

    def get_payout(self, player_cards):
        return self.pot.calculate_payout(player_cards, self.board_cards)

    def new_round(self, own_hand, seats_occupied, own_seat=None):
        if own_seat is not None:
            self.own_seat = own_seat
        self.own_hand = own_hand
        self.num_players = len(seats_occupied)
        self.populate_positions(seats_occupied, rotate=True)
        self.pot = pot.Pot()


    def populate_positions(self, seats_occupied, rotate=False):
        # position -> in game? for both modes
        self.seats_in = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}
        for num in seats_occupied:
            self.seats_in[num] = True
        num_players = len(seats_occupied)
        active_pos = set()
        if num_players > 1:
            active_pos.add("BTN")
            active_pos.add("BB")
            # this is so ranges are more accurate in heads-up
        if num_players > 2:
            active_pos.add("SB")
        if num_players > 3:
            active_pos.add("UTG")
        if num_players > 4:
            active_pos.add("CO")
        if num_players > 5:
            active_pos.add("HJ")
        if num_players > 6:
            active_pos.add("LJ")
        if num_players > 7:
            active_pos.add("UTG+1")
        if num_players > 8:
            active_pos.add("UTG+2")
        in_positions = [pos for pos in positions if pos in active_pos]
        if rotate == True:
            self.own_pos = in_positions[(in_positions.index(self.own_pos) + 1) % num_players]
        # seat -> position for both modes
        self.rotation = {self.own_seat: self.own_pos}
        own_pos_idx = in_positions.index(self.own_pos)
        next_pos_idx = (own_pos_idx + 1) % num_players
        own_seat_idx = seats_occupied.index(self.own_seat)
        next_seat_idx = (own_seat_idx + 1) % num_players
        while next_seat_idx != own_seat_idx:
            self.rotation[seats_occupied[next_seat_idx]] = in_positions[next_pos_idx]
            next_pos_idx = (next_pos_idx + 1) % num_players
            next_seat_idx = (next_seat_idx + 1) % num_players

    def get_action_order(self, betting_round):
        # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
        start_pos = "UTG" if betting_round == 0 else "SB"
        if self.num_players == 2:
            start_pos = "BTN" if betting_round == 0 else "BB"
        pos_to_seat = {pos: seat for seat, pos in self.rotation.items()} # pos -> seat 
        active_pos = [pos for pos in positions if pos in pos_to_seat and self.seats_in[pos_to_seat[pos]]]
        start_idx = active_pos.index(start_pos)
        action_order = active_pos[start_idx:] + active_pos[:start_idx]
        return [pos_to_seat[pos] for pos in action_order]

    def calculate_ev_call(self, equity, cost_to_call):
        return equity * (self.pot.get_amount() + cost_to_call) - cost_to_call

    def calculate_ev_raise(self, bet):
        # note: opponent reraise will be built later
        # we are calculating aggregate ev and new_equity will be calculated based on all the remaining opponents' ranges
        # p_fold and p_call will be averagse
        # p_call as it is is probability of continuining (so call and reraise included)
        heads_up = sum(self.seats_in.values()) == 2
        num_opp_in = 0
        p_fold = 0
        for s, value in self.seats_in.items():
            if s == self.own_seat:
                continue
            if value:
                num_opp_in += 1
                pos = self.rotation[s]
                p_fold += position_ranges.get_prob_fold(pos, self.traits[s], bet, self.pot.get_amount(), heads_up=heads_up)
        p_fold = p_fold / num_opp_in
        p_call = 0
        for s, value in self.seats_in.items():
            if s == self.own_seat:
                continue
            if value:
                pos = self.rotation[s]
                p_call += position_ranges.get_prob_cont(pos, self.traits[s], bet, self.pot.get_amount(), heads_up=heads_up)
        p_call = p_call / num_opp_in
        new_equity = self.get_bet_equity(tightness=0.1)

        ev = p_fold * self.pot.get_amount() + p_call * (new_equity * (self.pot.get_amount() + ( num_opp_in + 1) * bet) - bet)

        return ev

    def get_bet_equity(self, tightness=0):
        heads_up = sum(self.seats_in.values()) == 2
        ranges = dict() # position -> all range hands
        for key, value in self.seats_in.items():
            if key == self.own_seat:
                continue
            if value is True:
                pos = self.rotation[key]
                looseness = max(self.traits[key]-tightness, 0)
                ranges[pos] = position_ranges.get_range_hands(pos, heads_up=heads_up, looseness=looseness)
        equities_sum = np.zeros(len(ranges) + 1)
        for i in range(10000):
            pocket_list = [self.own_hand]
            selected_cards = set()
            for card in self.own_hand:
                selected_cards.add(card)
            for card in self.board_cards:
                selected_cards.add(card)
            for key, value in ranges.items():
                random_cards = random.choice(value)
                card1, card2 = random_cards
                while card1 in selected_cards or card2 in selected_cards:
                    random_cards = random.choice(value)
                    card1, card2 = random_cards
                selected_cards.add(card1)
                selected_cards.add(card2)
                pocket_list.append(random_cards)
            # only testing one combination of community cards per combinations of hands:
            equity_list = equity_calculator.calculate_equity(pocket_list, self.board_cards, 1)
            equities_sum = equities_sum + np.array(equity_list)
        avg_equities = equities_sum / 10000    
        return avg_equities[0]


    def get_own_seat(self):
        return self.own_seat

    def get_own_pos(self):
        return self.own_pos

    def get_occupied_seats(self):
        return self.occupied_seats
    
    def get_seats_in(self):
        return self.seats_in

    def get_player_contributions(self):
        return self.pot.get_player_contributions()

    def get_max_contribution(self):
        return max(self.get_player_contributions().values())

    def get_own_contribution(self):
        return self.get_player_contributions()[self.own_seat] 
