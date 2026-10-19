import random

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

        cost_to_call = min(cost_to_call, stack)  # cap first
        options = [] # (action, amount, ev)
        if cost_to_call > 0: # fold is only legal when there is something to call
            options.append(("fold", -1, 0))
        adjusted_ev_call = ev_call + random.uniform(-self.volatility * big_blind, self.volatility * big_blind)
        adjusted_ev_call = adjusted_ev_call + (-1.0 + self.looseness) * big_blind
        call_name = "check" if cost_to_call == 0 else "call"
        options.append((call_name, cost_to_call, adjusted_ev_call))

        if stack > cost_to_call: # otherwise calling is already all-in, so no raise exists
            min_raise = cost_to_call + big_blind
            bet_proportions = [0.1, 0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 1]
            bet_sizes = {stack} # a set, so duplicates disappear; all-in is always an option
            for prop in bet_proportions:
                size = max(int(prop * pot), min_raise) # whole chips, never below the legal minimum
                if size < stack:
                    bet_sizes.add(size)

            raise_options = []
            for bet in sorted(bet_sizes):
                ev_raise = game.calculate_ev_raise(bet, betting_round, seat, hand)
                adjusted_ev_raise = ev_raise + random.uniform(-self.volatility * big_blind, self.volatility * big_blind)
                raise_options.append(("raise", bet, adjusted_ev_raise))
            best_raise = max(raise_options, key=lambda option: option[2])
            # applying aggressiveness to raising:
            bonus = self.aggressiveness * big_blind if best_raise[2] > 0 else 0 # aggression never makes a losing raise beat folding
            options.append((best_raise[0], best_raise[1], best_raise[2] + bonus))

        best_option = max(options, key=lambda option: option[2])
        return best_option[0], best_option[1]
    
    def set_volatility(self, volatility):
        self.volatility = volatility

    def set_aggressiveness(self, aggressiveness):
        self.aggressiveness = aggressiveness

    def set_looseness(self, looseness):
        self.looseness = looseness