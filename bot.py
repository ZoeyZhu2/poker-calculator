import random

class bot():

    def __init__(self, volatility, aggressiveness, looseness, stack):
        # volatility is a float from 0 to 1 measure percentage it can swing from playing according to target ev based on big_blind
        # aggressiveness to be figured out
        # looseness is a percentage of default range (starting from best hands) it will play (can also go over default range)
        self.volatility = volatility
        self.aggressiveness = aggressiveness
        self.looseness = looseness
        self.stack = stack

    def get_equity(self, position):
        # calculate range equity (looseness plays into effect here)
        pass 

    def decision(self, equity, pot, cost_to_call, big_blind):
        if self.stack < 0:
            return "exit"
        if self.stack == 0:
            return "side pot"

        cost_to_call = min(cost_to_call, self.stack)  # cap first

        ev = equity * (pot + cost_to_call) - cost_to_call
        noise = random.uniform(-big_blind * self.volatility, big_blind * self.volatility)
        adjusted_ev = ev + noise
        if adjusted_ev <= 0:
            return "fold", 0
        # figure out raise behavior?
        else:
            self.stack -= cost_to_call
            return "call", cost_to_call