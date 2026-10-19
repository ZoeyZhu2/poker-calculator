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
                loose = get_input("How loose do you want this bot to be (enter integer 1-5; 3 is normal, 1 is super tight, 5 is super loose): ")
                looseness = 0.5 + int(loose.strip()) * 0.25
            new_bot = bot.bot(volatility, aggressiveness, looseness)
            bots.append(new_bot)

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

        # making list of seats
        occupied_seats = [i for i in range(1, num_players + 1)]

        # assigning hand
        game_deck = deck.Deck()
        own_hand = []
        own_hand.append(game_deck.deal_card())
        own_hand.append(game_deck.deal_card())

        player_hands = dict() # seat -> hands
    
        poker_game = game.PokerGame(own_hand, player_seat, occupied_seats, stacks, board_cards)
        while True:
            player_hands[player_seat] = own_hand
            print(f"This is your hand: {own_hand}")
            print(f"This is your seat and position: Seat {player_seat} {poker_game.get_own_pos()}")
            for seat in occupied_seats:
                if seat != player_seat:
                   player_hands[seat] = [game_deck.deal_card(), game_deck.deal_card()]
            
            poker_game.post_blinds(small_blind, big_blind)
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

            game_deck = deck.Deck()
            own_hand = []
            own_hand.append(game_deck.deal_card())
            own_hand.append(game_deck.deal_card())

            stacks = poker_game.get_stacks()
            occupied_seats = [s for s in occupied_seats if stacks[s] > 0]
            if player_seat not in occupied_seats:
                print("You're out of chips. Game over.")
                break
            if len(occupied_seats) == 1:
                print("You win!")
                break
            poker_game.new_round(own_hand, occupied_seats, player_seat, stacks)
    
    except QuitGame:
        print("Quitting game")
        return

def update_action(poker_game, betting_round, player_seats, player_hands, small_blind, big_blind, seats_all_in=None):
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
                amount = int(get_input("How much do you bet? (any negative for fold): "))
                if amount < 0 or amount == stack: # fold, or all-in (always legal)
                    break
                if amount > stack:
                    print(f"You only have {stack}.")
                elif amount < cost_to_call:
                    print(f"You must put in at least {cost_to_call}, or fold.")
                elif cost_to_call < amount < cost_to_call + big_blind:
                    print(f"The minimum raise is {cost_to_call + big_blind}.")
                else:
                    break
        else: # bot bets
            equity = poker_game.get_equity(seat=seat, hand=player_hands[seat], n_sims=1000)
            ev_call = poker_game.calculate_ev_call(equity, cost_to_call)
            pot = poker_game.get_pot()
            action, amount = player_seats[seat].decision(poker_game, seat, player_hands[seat], stack, ev_call, betting_round, pot, cost_to_call, big_blind)
            if action != "fold":
                print(f"The player in seat {seat} {action}s {amount} ")

        if amount < 0:
            poker_game.fold_player(seat)
            print(f"Player in seat {seat} folds")
            if seat != poker_game.get_own_seat():
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


if __name__ == "__main__":
    main()