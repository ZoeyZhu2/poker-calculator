import game
from exceptions import QuitGame
from exceptions import get_input

def main():
    try:
        own_hand_str = get_input("Your hand (format: AhKd): ")
        own_hand = list()
        for i in range(0, len(own_hand_str), 2):
            own_hand.append(own_hand_str[i:i+2])
        own_pos = get_input("Your position (format: BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO): ")
        own_seat = int(get_input("Your seat (1, 2, 3, 4, 5, 6, 7, 8, 9): "))
        occupied_seats_str = get_input("All occupied seats incl. your own (format:1234): ")
        occupied_seats = list()
        stacks = dict()
        for i in range(0, len(occupied_seats_str)):
            curr_seat = int(occupied_seats_str[i:i+1])
            occupied_seats.append(curr_seat)
            curr_stack = int(get_input(f"What is the stack size of the player at seat {curr_seat} (format: 100)? "))
            stacks[curr_seat] = curr_stack                 
        poker_game = game.PokerGame(own_hand, own_seat, occupied_seats, stacks, [], own_pos)
        small_blind = int(get_input("Small blind: "))
        big_blind = int(get_input("Big blind: "))

        while True:
            poker_game.post_blinds(small_blind, big_blind)
            num_in, seats_all_in, seat = update_action(poker_game, 0)

            if num_in > 1:
                board_cards_str = get_input("Flop dealt (format: AhKdQs): ")
                for i in range(0, len(board_cards_str),2):
                    poker_game.add_board_card(board_cards_str[i:i+2])
                
                num_in, seats_all_in, seat = update_action(poker_game, 1, seats_all_in)

            if num_in > 1:
                board_card = get_input("Turn dealt (format: Ah): ")
                poker_game.add_board_card(board_card)

                num_in, seats_all_in, seat = update_action(poker_game, 2, seats_all_in)

            if num_in > 1:
                board_card = get_input("River dealt: (format: Ah)")
                poker_game.add_board_card(board_card)
                num_in, seats_all_in, seat = update_action(poker_game, 3, seats_all_in)

            if num_in != 1:
            # assuming everyone didn't fold
                seats_in = poker_game.get_seats_in()
                player_cards = {} # seat -> showdown hand
                for seat, value in seats_in.items():
                    if value:
                        cards_str = get_input(f"Input seat {seat}'s hand (format: AhKd). If mucked, just hit enter. : ")
                        cards_str = cards_str.strip()
                        cards = [cards_str[:2], cards_str[2:]]
                        player_cards[seat] = cards
                poker_game.get_payout(player_cards)
            else:
                poker_game.award_directly(seat)
            
            next_round = get_input("Next round (Y/N): ").strip()
            if next_round == "N":
                break
            change_seat = get_input("Did seats change? (Y/N): ")
            if change_seat == "Y":
                own_seat = int(get_input("Your seat (1, 2, 3, 4, 5, 6, 7, 8, 9): "))
                occupied_seats_str = get_input("All occupied seats incl. your own (format:1234): ")
                occupied_seats = list()
                stacks = dict()
                for i in range(0, len(occupied_seats_str)):
                    curr_seat = int(occupied_seats_str[i:i+1])
                    occupied_seats.append(curr_seat)
                    curr_stack = int(get_input(f"What is the stack size of the player at seat {curr_seat} (format: 100)? "))
                    stacks[curr_seat] = curr_stack       
            else: 
                own_pos = poker_game.get_own_pos()
                own_seat =  poker_game.get_own_seat()
                occupied_seats = poker_game.get_occupied_seats()
                change_stack = get_input("Did stacks change outside of gameplay? (Y/N): ")
                if change_stack == "Y":
                    stacks = dict()
                    for i in range(0, len(occupied_seats_str)):
                        curr_seat = int(occupied_seats_str[i:i+1])
                        curr_stack = int(get_input(f"What is the stack size of the player at seat {curr_seat} (format: 100)? "))
                        stacks[curr_seat] = curr_stack  

            own_hand_str = get_input("Your hand (format: AhKd): ")
            own_hand = list()
            for i in range(0, len(own_hand_str), 2):
                own_hand.append(own_hand_str[i:i+2])

            poker_game.new_round(own_hand, occupied_seats, own_seat, stacks)
    except QuitGame:
        print("Quitting game")
        return
        
def update_action(poker_game, betting_round, seats_all_in=None):
    # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
    # seats_all_in is no longer needed as input (all-in = in the hand with a stack of 0), kept so the callers don't change
    seats_in = poker_game.get_seats_in()
    current_equity = poker_game.get_equity()
    print(f"Current equity: {current_equity}")

    ring = poker_game.get_action_order(betting_round, set()) # everyone still in the hand, in action order

    def can_act(seat): # still in the hand and has chips left
        return seats_in[seat] and poker_game.get_stack(seat) > 0

    def all_in_seats():
        return {s for s in ring if seats_in[s] and poker_game.get_stack(s) == 0}

    to_act = [s for s in ring if can_act(s)] # queue of seats that still have to act
    while to_act:
        seat = to_act.pop(0)
        if not can_act(seat):
            continue
        cost_to_call = poker_game.get_max_contribution() - poker_game.get_seat_contribution(seat)
        if cost_to_call == 0 and sum(1 for s in ring if can_act(s)) == 1:
            break # everyone else is all-in or folded, so there is nobody to bet against
        prev_max_contribution = poker_game.get_max_contribution()
        stack = poker_game.get_stack(seat)

        if seat == poker_game.get_own_seat():
            print(f"Current EV to call: {poker_game.calculate_ev_call(current_equity, cost_to_call)}")
            while True:
                bet = get_input("Enter how much you want to raise to calculate new EV. Enter 0 to stop.")
                if bet.strip() == "0":
                    break
                bet = int(bet)
                if bet < cost_to_call:
                    print("You must input a higher number")
                    continue
                print(f"Current EV to raise: {poker_game.calculate_ev_raise(bet, betting_round)}")
        while True:
            amount = int(get_input(f"How much did the player in seat {seat} put in? (any negative for fold, 0 for check): "))
            if amount < 0 or amount == stack: # fold, or all-in
                break
            if amount > stack:
                print(f"That seat only has {stack}.")
            elif amount < cost_to_call:
                print(f"They must put in at least {cost_to_call}, or fold.")
            else:
                break

        if amount < 0:
            poker_game.fold_player(seat)
            current_equity = poker_game.get_equity()
            print(f"Current equity: {current_equity}")
            if poker_game.get_num_in() == 1:
                winner = next(s for s, value in seats_in.items() if value)
                return poker_game.get_num_in(), all_in_seats(), winner
        elif amount > 0:
            poker_game.player_bet(seat, amount)

        if poker_game.get_max_contribution() > prev_max_contribution: # a raise: everyone else has to act again
            i = ring.index(seat)
            to_act = [s for s in ring[i + 1:] + ring[:i] if can_act(s)]
    return poker_game.get_num_in(), all_in_seats(), None

if __name__ == "__main__": # name is only main if a user runs it, not if another file imports this one
    main()