import random
import game

class bot():

    def __init__(self, volatility=None, aggressiveness=None, looseness=None):
        # volatility is a float from 0 to 1 measure percentage it can swing from playing according to its ev thresholds for calling and raising on big_blind
        # aggressiveness is a float from 0 to 1 measuring how much worse ev_raise needs to be than ev_call to raise (1 is max aggression)
        # looseness is a percentage of default range (starting from best hands) it will play (can also go over default range). Measures how much worse ev_call can be to call. Higher looseness means more loose
        if volatility is not None:
            self.volatility = volatility
        else:
            self.volatility = random.uniform(0,1)
        if aggressiveness is not None:
            self.aggressiveness = aggressiveness
        else:
            self.aggressiveness = random.uniform(0,1)
        if looseness is not None:
            self.looseness = looseness
        else:
            self.looseness = random.uniform(0.5, 1.5)
    
    def decision(self, game, seat, hand, stack, ev_call, betting_round, pot, cost_to_call, big_blind):
        # game is a PokerGame instance that is the current game being played
        # ev_call is a float
        # stack, betting_round, pot, cost_to_call, big_blind is an int
        # pot is the amount in the pot

        if stack < 0:
            return "exit", 0
        if stack == 0:
            return "side pot", 0

        options = [] # (action, bet size, ev)
        options.append(("fold", 0, 0))
        cost_to_call = min(cost_to_call, stack)  # cap first
        adjusted_ev_call = ev_call + random.uniform(-self.volatility * big_blind, self.volatility * big_blind)
        adjusted_ev_call = adjusted_ev_call + (-1.0 + self.looseness) * big_blind
        options.append(("call", cost_to_call, adjusted_ev_call))

        bet_proportions = [0.1, 0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 1]
        bet_sizes = []
        for prop in bet_proportions:
            if prop * pot > stack:
                break
            bet_sizes.append(max(big_blind, prop * pot))
        bet_sizes.append(stack)

        raise_options = []
        for bet in bet_sizes:
            ev_raise = game.calculate_ev_raise(bet, betting_round, seat, hand)
            adjusted_ev_raise = ev_raise + random.uniform(-self.volatility * big_blind, self.volatility * big_blind)
            raise_options.append(("raise", bet, adjusted_ev_raise))
        best_raise_options = sorted(raise_options, key=lambda ev: ev[2], reverse=True)
        best_raise_option = best_raise_options[0]
        options.append(best_raise_option) # only adding best raise option to options
        # applying aggressiveness to raising: 
        options[-1] = (options[-1][0], options[-1][1], options[-1][2] + self.aggressiveness * big_blind)
        # picking best option out of all actions
        options = sorted(options, key=lambda ev: ev[2], reverse=True)
        best_option = options[0]
        return best_option[0], best_option[1]

    def set_volatility(self, volatility):
        self.volatility = volatility

    def set_aggressiveness(self, aggressiveness):
        self.aggressiveness = aggressiveness

    def set_looseness(self, looseness):
        self.looseness = looseness