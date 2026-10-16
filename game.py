import position_ranges
import equity_calculator
import random
import numpy as np
import pot


positions = ["BTN", "SB", "BB", "UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]


class PokerGame:
    def __init__(self, own_hand: list, own_seat: int, occupied_seats: list, stacks: dict, board_cards: list, own_pos=None):
        # own_hand is a list of two cards ex: ["Ah", "Kd"]
        self.own_hand = own_hand
        # own_seat is an integer representing seat number
        self.own_seat = own_seat
        # own_seat is an integer representing own stack amount
        # stacks keeps track of seat -> stack
        self.stacks = stacks
        self.own_stack = self.stacks[self.own_seat]
        # occupied_seats is a list of integers
        self.occupied_seats = occupied_seats
        self.num_players = len(occupied_seats)
        self.num_in = len(occupied_seats)
        # board cards is a list of any community cards already dealt out ex: ["2s", "7d", "5h"]
        self.board_cards = board_cards
        # pot keeps track of the pot
        self.pot = pot.Pot()
        # seat -> bot for mode 1
        # self.bots = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}
        # seat -> looseness for mode 2 (eventually volatility and aggressiveness will be added)
        self.traits = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0}
        if own_pos is None:
            active_pos = self.get_active_positions(occupied_seats)
            # own_pos is a string representing position ex: "BTN"
            self.own_pos = random.choice(tuple(active_pos))
        else:
            self.own_pos = own_pos

        num_players = len(occupied_seats)
        in_positions = [p for p in positions if p in self.get_active_positions(occupied_seats)]
        self.button_seat = occupied_seats[(occupied_seats.index(own_seat) - in_positions.index(self.own_pos)) % num_players]
        self.populate_positions(occupied_seats, self.button_seat)

        
    def update_traits(self, seat: int, looseness):
        self.traits[seat] = looseness

    # getting range equities (so an estimation)
    def get_equity(self, seat=None, hand=None):
        if seat is None:
            seat = self.own_seat
        if hand is None:
            hand = self.own_hand
        heads_up = self.num_players == 2
        ranges = dict() # position -> all range hands
        for key, value in self.seats_in.items():
            if key == seat:
                continue
            if value is True:
                pos = self.rotation[key]
                ranges[pos] = position_ranges.get_range_hands(pos, heads_up=heads_up, looseness=self.traits[key])
        equities_sum = np.zeros(len(ranges) + 1)
        for i in range(10000):
            pocket_list = [hand]
            selected_cards = set()
            for card in hand:
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
        self.num_in -= 1

    def player_bet(self, seat, amount):
        if amount > self.stacks[seat]:
            raise ValueError(f"Seat {seat} cannot bet {amount} with a stack of {self.stacks[seat]}")
        self.pot.add_contribution(seat, amount)
        self.stacks[seat] -= amount

    def add_board_card(self, card):
        self.board_cards.append(card)

    def get_payout(self, player_cards):
        payouts = self.pot.calculate_payout(player_cards, self.board_cards)
        for seat, amount in payouts.items():
            self.stacks[seat] += amount
        return payouts

    def award_directly(self, seat):
        self.stacks[seat] += self.pot.get_amount()

    def new_round(self, own_hand, seats_occupied, own_seat, stacks):
        self.own_seat = own_seat
        self.own_hand = own_hand
        self.num_players = len(seats_occupied)
        self.num_in = len(seats_occupied)
        self.occupied_seats = seats_occupied
        self.button_seat = self.next_seat_after(self.button_seat, seats_occupied)
        self.populate_positions(seats_occupied, self.button_seat)        
        self.pot = pot.Pot()
        self.stacks = stacks
        self.board_cards = []

    def get_active_positions(self, seats_occupied):
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
        return active_pos
    
    def populate_positions(self, seats_occupied, button_seat):
        # position -> in game? for both modes
        self.seats_in = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}
        for s in seats_occupied:
            self.seats_in[s] = True
        num_players = len(seats_occupied)
        active_pos = self.get_active_positions(seats_occupied)
        in_positions = [pos for pos in positions if pos in active_pos]
        btn_idx = seats_occupied.index(button_seat)
        self.rotation = {}
        for i in range(num_players):
            self.rotation[seats_occupied[(btn_idx + i) % num_players]] = in_positions[i]
        self.own_pos = self.rotation[self.own_seat]

    def next_seat_after(self, seat, seats_occupied):
        for step in range(1, 10):
            s = (seat - 1 + step) % 9 + 1
            if s in seats_occupied:
                return s

    def get_action_order(self, betting_round, seats_all_in):
        # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
        pos_to_seat = {pos: seat for seat, pos in self.rotation.items()} # pos -> seat 
        pos_order = [pos for pos in positions if pos in pos_to_seat]
        start_pos = "UTG" if betting_round == 0 else "SB"
        if self.num_players == 3:
            start_pos = "BTN" if betting_round == 0 else "SB"
        if self.num_players == 2:
            start_pos = "BTN" if betting_round == 0 else "BB"
        anchor_idx = pos_order.index(start_pos)  
        pos_order = pos_order[anchor_idx:] + pos_order[:anchor_idx]
        action_order = []
        for pos in pos_order:
            if pos_to_seat[pos] in seats_all_in or not self.seats_in[pos_to_seat[pos]]:
                continue
            action_order.append(pos)
        return [pos_to_seat[pos] for pos in action_order]

    def calculate_ev_call(self, equity, cost_to_call):
        return equity * (self.pot.get_amount() + cost_to_call) - cost_to_call

    def calculate_ev_raise(self, bet, betting_round, seat=None, hand=None):
        # note: opponent reraise will be built later
        # we are calculating aggregate ev and new_equity will be calculated based on all the remaining opponents' ranges
        # p_fold and p_call will be averagse
        # p_call as it is is probability of continuining (so call and reraise included)
        if seat is None:
            seat = self.own_seat
        if hand is None:
            hand = self.own_hand
        heads_up = self.num_players == 2
        num_opp_in = 0
        p_fold = 0
        p_cont = 0
        for s, value in self.seats_in.items():
            if s == seat:
                continue
            if value:
                if self.stacks[s] == 0:
                    num_opp_in += 1
                    p_cont += 1
                else: 
                    num_opp_in += 1
                    pos = self.rotation[s]
                    board_texture = position_ranges.get_board_texture(self.board_cards)
                    prob_fold = position_ranges.get_prob_fold(pos, self.traits[s], bet, self.pot.get_amount(), self.stacks[s], betting_round, board_texture, heads_up=heads_up)
                    p_fold += prob_fold
                    p_cont += 1 - prob_fold
        p_fold = p_fold / num_opp_in
        p_cont = min(p_cont / num_opp_in, 1)
        bet_ratio = bet / self.pot.get_amount()
        scale_factor = 0.5
        tightness = bet_ratio * scale_factor
        new_equity = self.get_bet_equity(tightness=tightness, seat=seat, hand=hand)

        ev = p_fold * self.pot.get_amount() + p_cont * (new_equity * (self.pot.get_amount() + ( num_opp_in + 1) * bet) - bet)

        return ev

    def get_bet_equity(self, tightness=0, seat=None, hand=None):
        if seat is None:
            seat = self.own_seat
        if hand is None:
            hand = self.own_hand
        heads_up = self.num_players == 2
        ranges = dict() # position -> all range hands
        for key, value in self.seats_in.items():
            if key == seat:
                continue
            if value is True:
                pos = self.rotation[key]
                looseness = max(self.traits[key]-tightness, 0)
                ranges[pos] = position_ranges.get_range_hands(pos, heads_up=heads_up, looseness=looseness)
        equities_sum = np.zeros(len(ranges) + 1)
        for i in range(10000):
            pocket_list = [hand]
            selected_cards = set()
            for card in hand:
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

    def post_blinds(self, small_blind, big_blind):
        heads_up = len(self.occupied_seats) == 2
        for seat in self.occupied_seats:
            pos = self.rotation[seat]
            stack = self.stacks[seat]
            if (pos == "SB" and not heads_up) or (pos == "BTN" and heads_up):
                self.player_bet(seat, min(small_blind, stack))
            elif pos == "BB":
                self.player_bet(seat, min(big_blind, stack))

    def get_own_seat(self):
        return self.own_seat

    def get_own_pos(self):
        return self.own_pos

    def get_seat_pos(self, seat):
        return self.rotation[seat]

    def get_occupied_seats(self):
        return self.occupied_seats
    
    def get_seats_in(self):
        return self.seats_in

    def get_num_in(self):
        return self.num_in

    def get_player_contributions(self):
        return self.pot.get_player_contributions()

    def get_max_contribution(self):
        return max(self.get_player_contributions().values())

    def get_own_contribution(self):
        return self.get_player_contributions()[self.own_seat] 

    def get_seat_contribution(self, seat):
        return self.get_player_contributions()[seat] 

    def get_stack(self, seat):
        return self.stacks[seat]

    def set_stack(self, seat, amount):
        self.stacks[seat] = amount

    def set_all_stacks(self, amount):
        for seat in self.seats_in:
            self.stacks[seat] = amount

    def get_pot(self):
        return self.pot.get_amount()

    def get_stacks(self):
        return self.stacks
            