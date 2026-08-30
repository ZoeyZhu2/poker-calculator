import game
from exceptions import QuitGame
from exceptions import get_input

def main():
    try:
        own_hand_str = get_input("Your hand (format: AhKd): ")
        own_hand = list()
        for i in range(0, len(own_hand_str)-2, 2):
            own_hand.append(own_hand_str[i:i+2])
        own_pos = get_input("Your position (format: BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO): ")
        own_seat = int(get_input("Your seat (1, 2, 3, 4, 5, 6, 7, 8, 9): "))
        occupied_seats_str = get_input("All occupied seats incl. your own (format:1234): ")
        occupied_seats = list()
        for i in range(0, len(occupied_seats_str)):
            occupied_seats.append(int(occupied_seats_str[i:i+1]))
        poker_game = game.PokerGame(own_hand, own_pos, own_seat, occupied_seats, [])

        while True:
            num_in = update_action(poker_game, 0)

            if num_in > 1:
                board_cards_str = get_input("Flop dealt (format: AhKdQs): ")
                for i in range(0, len(board_cards_str)-2,2):
                    poker_game.add_board_card(board_cards_str[i:i+2])
                
                num_in = update_action(poker_game, 1)

            if num_in > 1:
                board_card = get_input("Turn dealt (format: Ah): ")
                poker_game.add_board_card(board_card)

                num_in = update_action(poker_game, 2)

            if num_in > 1:
                board_card = get_input("River dealt: (format: Ah)")
                poker_game.add_board_card(board_card)
                num_in = update_action(poker_game, 3)
            
            next_round = get_input("Next round (Y/N): ").strip()
            if next_round == "N":
                break
            change_seat = get_input("Did seats change? (Y/N): ")
            if change_seat == "Y":
                own_seat = int(get_input("Your seat (1, 2, 3, 4, 5, 6, 7, 8, 9): "))
                occupied_seats_str = get_input("All occupied seats incl. your own (format:1234): ")
                occupied_seats = list()
                for i in range(0, len(occupied_seats_str)):
                    occupied_seats.append(int(occupied_seats_str[i:i+1]))
                
            else: 
                own_pos = poker_game.get_own_pos()
                own_seat =  poker_game.get_own_seat()
                occupied_seats = poker_game.get_occupied_seats()   

            own_hand_str = get_input("Your hand (format: AhKd): ")
            own_hand = list()
            for i in range(0, len(own_hand_str)-2, 2):
                own_hand.append(own_hand_str[i:i+2])

            poker_game.new_round(own_hand, occupied_seats, own_seat)
    except QuitGame:
        print("Quitting game")
        return
        
def update_action(poker_game, betting_round):
    # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
    current_equity = poker_game.get_equity()
    print(f"Current equity: {current_equity}")
    left_to_act = poker_game.get_num_in()
    while left_to_act > 0: # until all bets are equal or all ins or whatever (need to write break thing)
        action_order = poker_game.get_action_order(betting_round)
        for seat in action_order:
            curr_max_contribution = poker_game.get_max_contribution()
            if seat == poker_game.get_own_seat():
                cost_to_call = poker_game.get_max_contribution() - poker_game.get_own_contribution()
                print(f"Current EV to call: {poker_game.calculate_ev_call(current_equity, cost_to_call)}")
                while True:
                    bet = get_input("Enter how much you want to raise to calculate new EV. Enter 0 to stop.")
                    if bet.strip() == "0":
                        break
                    bet = int(bet)
                    if bet < cost_to_call:
                        print("You must input a higher number")
                        continue
                    print(f"Current EV to raise: {poker_game.calculate_ev_raise(bet)}")
            amount = int(get_input(f"How much did the player in seat {seat} bet? (any negative for fold): "))
            if amount < 0:
                poker_game.fold_player(seat)
                current_equity = poker_game.get_equity()
                print(f"Current equity: {current_equity}")
                if poker_game.get_num_in() == 1:
                    return poker_game.get_num_in()
            elif amount == 0:
                pass # do nothing!
            else:
                poker_game.player_bet(seat, amount)
            if poker_game.get_max_contribution() != curr_max_contribution:
                left_to_act = poker_game.get_num_in()
            left_to_act -= 1
    return poker_game.get_num_in()

if __name__ == "__main__": # name is only main if a user runs it, not if another file imports this one
    main()