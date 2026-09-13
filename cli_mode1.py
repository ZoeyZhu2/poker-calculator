from exceptions import QuitGame
from exceptions import get_input
import game
import bot
import random
import deck

def main():
    try:
        print("At any point, input q or quit to quit.")
        num_players = int(get_input("How many players are playing (including you)? Enter a digit 2-9: "))
        while num_players < 2 or num_players > 9:
            print("Please enter a different number.")
            num_players = int(get_input("How many players are playing (including you)? Enter a digit 2-9: "))
    
        # creating bots
        bots = list()
        for i in range(1, num_players):
            volatility = None
            aggressiveness = None
            looseness = None
            customize = get_input("Would you like to customize this bot (Y/N)? ")
            if customize.lower() == "y":
                volatile = get_input("How volatile do you want this bot to be (enter integer 0-5): ")
                volatility = 0.2 * int(volatile.strip())
                aggressive = get_input("How aggressive do you want this bot to be (enter integer 0-5): ")
                aggressiveness = 0.2 * int(aggressive.strip())
                loose = get_input("How aggressive do you want this bot to be (enter integer 1-5; 3 is normal, 1 is super tight, 5 is super loose): ")
                looseness = 0.5 + int(loose.strip()) * 0.25
            new_bot = bot.bot(volatility, aggressiveness, looseness)
            bots.append(new_bot)

        # getting active positions
        active_pos = list()
        if num_players > 1:
            active_pos.append("BTN")
            active_pos.append("BB")
            # this is so ranges are more accurate in heads-up
        if num_players > 2:
            active_pos.append("SB")
        if num_players > 3:
            active_pos.append("UTG")
        if num_players > 4:
            active_pos.append("CO")
        if num_players > 5:
            active_pos.append("HJ")
        if num_players > 6:
            active_pos.append("LJ")
        if num_players > 7:
            active_pos.append("UTG+1")
        if num_players > 8:
            active_pos.append("UTG+2")

        # setting stack sizes and big_blinds
        stack_size = int(get_input("What do you want initial stack size to be?"))
        big_blind = int(get_input("What do you want big blind to be?"))
        while big_blind > stack_size or big_blind <= 0:
            big_blind = int(get_input("What do you want big blind to be?"))
        small_blind = int(get_input("What do you want small blind to be?"))
        while small_blind <= 0 or small_blind > big_blind:
            small_blind = int(get_input("What do you want big blind to be?"))
        stacks = dict() # seat -> stack_size
        for i in range (1, num_players + 1):
            stacks[i] = stack_size

        # assigning seat
        player_seats = dict() # seat -> player
        player_seat = random.randint(1, num_players)
        player_seats[player_seat] = "player"
        current_seat = 1
        for b in bots:
            if current_seat == player_seat:
                current_seat += 1
            player_seats[current_seat] = b
            current_seat += 1
            

        # assigning community cards
        board_cards = []

        # assigning position
        player_pos = random.choice(active_pos)

        # making list of seats
        occupied_seats = [i for i in range(1, num_players + 1)]

        # assigning hand
        game_deck = deck.Deck()
        own_hand = []
        own_hand.append(game_deck.deal_card())
        own_hand.append(game_deck.deal_card())

        player_hands = dict() # seat -> hands
    
        poker_game = game.PokerGame(own_hand, player_pos, player_seat, occupied_seats, stacks, board_cards)
        while True:
            player_hands[player_seat] = own_hand
            print(f"This is your hand: {own_hand}")
            print(f"This is your seat and position: Seat {player_seat} {player_pos}")
            current_seat = 1
            for b in bots:
                if current_seat == player_seat:
                    current_seat += 1
                player_hands[current_seat] = [game_deck.deal_card(), game_deck.deal_card()]
                current_seat += 1

            num_in, seats_all_in, seat = update_action(poker_game, 0, player_seats, player_hands, small_blind, big_blind)

            if num_in > 1:
                cards_dealt = ""
                for i in range(3):
                    next_card = game_deck.deal_card()
                    cards_dealt += next_card + " "
                    poker_game.add_board_card(next_card)
                print(f"Flop dealt: {cards_dealt}")
                
                num_in, seats_all_in, seat = update_action(poker_game, 1, player_seats, player_hands, small_blind, big_blind, seats_all_in)

            if num_in > 1:
                next_card = game_deck.deal_card()
                poker_game.add_board_card(next_card)
                print(f"Turn dealt: {next_card}")

                num_in, seats_all_in, seat = update_action(poker_game, 2, player_seats, player_hands, small_blind, big_blind, seats_all_in)

            if num_in > 1:
                next_card = game_deck.deal_card()
                poker_game.add_board_card(next_card)
                print(f"River dealt: {next_card}")
                num_in, seats_all_in, seat = update_action(poker_game, 3, player_seats, player_hands, small_blind, big_blind, seats_all_in)

            if num_in != 1:
            # assuming everyone didn't fold
                seats_in = poker_game.get_seats_in()
                player_cards = dict() # seat -> hand but only for palyers still in
                for seat, value in seats_in.items():
                    if value:
                        print(f"Player in seat {seat} has {player_hands[seat]}")
                        player_cards[seat] = player_hands[seat]
                payouts = poker_game.get_payout(player_cards)
                for seat, payout in payouts.items():
                    print(f"The player in seat {seat} wins: {payout}")
            else:
                poker_game.award_directly(seat)
                print(f"The player in seat {seat} wins: {poker_game.get_pot()}")
            
            next_round = get_input("Next round (Y/N): ").strip()
            if next_round == "N":
                break

            own_hand = []
            own_hand.append(game_deck.deal_card())
            own_hand.append(game_deck.deal_card())

            stacks = poker_game.get_stacks()
            poker_game.new_round(own_hand, occupied_seats, player_seat, stacks)
    except QuitGame:
        print("Quitting game")
        return
    
def update_action(poker_game, betting_round, player_seats, player_hands, small_blind, big_blind, seats_all_in=None):
    # betting_round: 0,1,2,3 for preflop, post flop, post turn, post river
    if seats_all_in is None:
        seats_all_in = set()
    current_equity = poker_game.get_equity()
    print(f"Current equity: {current_equity}")
    if betting_round == 0:
        for seat in player_seats:
            if len(player_seats) == 2:
                if poker_game.get_seat_pos(seat) == "BTN":
                    poker_game.player_bet(seat, small_blind)
                if poker_game.get_seat_pos(seat) == "BB":
                    poker_game.player_bet(seat, big_blind)
            else:
                if poker_game.get_seat_pos(seat) == "SB":
                    poker_game.player_bet(seat, small_blind)
                if poker_game.get_seat_pos(seat) == "BB":
                    poker_game.player_bet(seat, big_blind)
    left_to_act = poker_game.get_num_in() - len(seats_all_in)
    while left_to_act > 0: # until all bets are equal or all ins or whatever (need to write break thing)
        action_order = poker_game.get_action_order(betting_round, seats_all_in)
        for seat in action_order:
            all_in = False
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
                    print(f"Current EV to raise: {poker_game.calculate_ev_raise(bet, betting_round)}")
                amount = int(get_input("How much do you bet? (any negative for fold): "))
            else: # bot bets
                equity = poker_game.get_equity(seat=seat, hand=player_hands[seat])
                cost_to_call = poker_game.get_max_contribution() - poker_game.get_seat_contribution(seat)
                ev_call = poker_game.calculate_ev_call(equity, cost_to_call)
                pot = poker_game.get_pot()
                stack = poker_game.get_stack(seat)
                if stack == 0:
                    seats_all_in.add(seat)
                last_bet = poker_game.get_last_bet()
                action, amount = player_seats[seat].decision(poker_game, seat, player_hands[seat], stack, ev_call, betting_round, pot, cost_to_call, last_bet, big_blind)
                if action != "fold":
                    print(f"The player in seat {seat} {action}s {amount} ")
            if amount < 0:
                poker_game.fold_player(seat)
                print(f"Player in seat {seat} folds")
                if seat != poker_game.get_own_seat():
                    current_equity = poker_game.get_equity()
                    print(f"Current equity: {current_equity}")
                if poker_game.get_num_in() == 1:
                    seat = next(s for s, value in poker_game.get_seats_in().items() if value)
                    return poker_game.get_num_in(), seats_all_in, seat
            elif amount == 0:
                pass # do nothing!
            else:
                if amount == poker_game.get_stack(seat):
                    all_in = True
                    seats_all_in.add(seat)
                poker_game.player_bet(seat, amount)
            # figure out rest of all_in stuff
            if all_in:
                left_to_act = poker_game.get_num_in() - len(seats_all_in)
            elif poker_game.get_max_contribution() != curr_max_contribution:
                left_to_act = poker_game.get_num_in()
            left_to_act -= 1
    return poker_game.get_num_in(), seats_all_in, None


if __name__ == "__main__":
    main()