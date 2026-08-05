import random

class bot():

    def __init__(self, volatility, aggressiveness, stack):
        # volatility is a float from 0 to 1 measure percentage it can swing from playing according to target ev
        # aggressiveness is a float from 0 to 1 which is min equity needed to raise
        self.volatility = volatility
        self.aggressiveness = aggressiveness
        self.stack = stack

    def decision(self, equity, pot, cost_to_call):
        if self.stack < 0:
            return "exit"
        if self.stack == 0:
            return "side pot"

        cost_to_call = min(cost_to_call, self.stack)  # cap first

        ev = equity * (pot + cost_to_call) - cost_to_call
        adjusted_ev = random.uniform(ev - abs(ev) * self.volatility, ev + abs(ev) * self.volatility)
        if adjusted_ev <= 0:
            return "fold", 0
        elif equity > self.aggressiveness:
            raise_amount = pot * 0.66 # standard for now
            if raise_amount > self.stack:
                raise_amount = self.stack
            self.stack -= raise_amount
            return "raise", raise_amount
        else:
            self.stack -= cost_to_call
            return "call", cost_to_call