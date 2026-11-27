import game
from exceptions import QuitGame
from exceptions import get_input, get_int, get_yn, get_cards
import game_decision

def ask_position():
    while True:
        pos = get_input("Your position (format: BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO): ").strip().upper()
        if pos in game.positions:
            return pos
        print(f"Please enter one of: {', '.join(game.positions)}")

def ask_stacks(seats):
    return {seat: get_int(f"What is the stack size of the player at seat {seat} (format: 100)? ", 1) for seat in seats}

def ask_seats():
    # returns own_seat, occupied_seats (sorted, includes own seat), stacks
    own_seat = get_int("Your seat (1, 2, 3, 4, 5, 6, 7, 8, 9): ", 1, 9)
    while True:
        text = get_input("All occupied seats incl. your own (format:1234): ").strip()
        seats = sorted({int(ch) for ch in text if ch in "123456789"})
        if len(seats) != len(text) or len(seats) < 2:
            print("Please enter 2 or more different seat digits 1-9, like 1234.")
        elif own_seat not in seats:
            print(f"Your own seat ({own_seat}) must be in the list.")
        else:
            return own_seat, seats, ask_stacks(seats)

def main():
    try:
        own_hand = get_cards("Your hand (format: AhKd): ", 2)
        own_pos = ask_position()
        own_seat, occupied_seats, stacks = ask_seats()
        while True:
            try:
                poker_game = game.PokerGame(own_hand, own_seat, occupied_seats, stacks, [], own_pos)
                break
            except ValueError: # the position doesn't exist at a table this size
                print(f"There is no {own_pos} with {len(occupied_seats)} players.")
                own_pos = ask_position()
        small_blind = get_int("Small blind: ", 1)
        big_blind = get_int("Big blind: ", small_blind)

        def dealt(): # cards already known, which can't come again
            return poker_game.board_cards + poker_game.own_hand

        while True:
            poker_game.post_blinds(small_blind, big_blind)
            num_in, seats_all_in, seat = update_action(poker_game, 0)

            if num_in > 1:
                for card in get_cards("Flop dealt (format: AhKdQs): ", 3, dealt()):
                    poker_game.add_board_card(card)
                num_in, seats_all_in, seat = update_action(poker_game, 1, seats_all_in)

            if num_in > 1:
                poker_game.add_board_card(get_cards("Turn dealt (format: Ah): ", 1, dealt())[0])
                num_in, seats_all_in, seat = update_action(poker_game, 2, seats_all_in)

            if num_in > 1:
                poker_game.add_board_card(get_cards("River dealt: (format: Ah)", 1, dealt())[0])
                num_in, seats_all_in, seat = update_action(poker_game, 3, seats_all_in)

            if num_in != 1:
            # assuming everyone didn't fold
                seats_in = poker_game.get_seats_in()
                player_cards = {} # seat -> showdown hand
                for seat, value in seats_in.items():
                    if value:
                        known = poker_game.board_cards + [c for cards in player_cards.values() for c in cards]
                        if seat != poker_game.get_own_seat(): # your own hand is allowed to be re-entered
                            known += poker_game.own_hand
                        cards = get_cards(f"Input seat {seat}'s hand (format: AhKd). If mucked, just hit enter. : ", 2, known, allow_empty=True)
                        player_cards[seat] = cards or ["", ""]
                poker_game.get_payout(player_cards)
            else:
                poker_game.award_directly(seat)
            
            if not get_yn("Next round (Y/N): "):
                break
            if get_yn("Did seats change? (Y/N): "):
                own_seat, occupied_seats, stacks = ask_seats()
            else:
                own_seat = poker_game.get_own_seat()
                occupied_seats = poker_game.get_occupied_seats()
                stacks = poker_game.get_stacks()
                if get_yn("Did stacks change outside of gameplay? (Y/N): "):
                    stacks = ask_stacks(occupied_seats)

            own_hand = get_cards("Your hand (format: AhKd): ", 2)
            poker_game.new_round(own_hand, occupied_seats, own_seat, stacks)
    except QuitGame:
        print("Quitting game")
        return
        
def update_action(poker_game, betting_round, seats_all_in=None):
    # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
    # seats_all_in is no longer needed as input (all-in = in the hand with a stack of 0), kept so the callers don't change
    seats_in = poker_game.get_seats_in()
    current_equity = game_decision.get_equity(poker_game.to_snapshot())
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
            print(f"Current EV to call: {game_decision.calculate_ev_call(poker_game.to_snapshot(), current_equity, cost_to_call)}")
            while True:
                bet = get_int("Enter how much you want to raise to calculate new EV. Enter 0 to stop.", 0)
                if bet == 0:
                    break
                if bet < cost_to_call:
                    print("You must input a higher number")
                    continue
                print(f"Current EV to raise: {game_decision.calculate_ev_raise(poker_game.to_snapshot(), bet, betting_round)}")
        while True:
            amount = get_int(f"How much did the player in seat {seat} put in? (any negative for fold, 0 for check): ")
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
            current_equity = game_decision.get_equity(poker_game.to_snapshot())
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