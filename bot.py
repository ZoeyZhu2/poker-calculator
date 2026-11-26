import random

class bot():

    def __init__(self, volatility=None, aggressiveness=None, looseness=None, bet_sizing=None):
        
        # (Variance) volatility is a float from 0 to 1:
        # measures percentage bot can swing from playing according to its ev thresholds for calling and raising as a percentage of big_blind
        # (PFR-ish) aggressiveness is a float from 0 to 1:
        # measures betting frequency: how much low ev_raise needs to be compared to ev_call to raise (1 is max aggression)
        # (VPIP) looseness is a float from 0.5 to 1.5:
        # it measures how far or below standard ev cutoffs the bot will play at
        # Measures how much worse ev_call can be to call. Higher looseness means more loose
        # bet_sizing: float between 0 and 1
        # measures how large bot's bet sizing will be relative to ideal ev (baseline is 0.5)
        
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
        if bet_sizing is not None:
            self.bet_sizing = bet_sizing
        else:
            self.bet_sizing = random.uniform(0,1)
        
    def decision(self, game, seat, hand, stack: int, ev_call: float, betting_round: int, pot: int, cost_to_call: int, big_blind: int):
        # game is a PokerGame instance that is the current game being played

        if stack < 0:
            return "exit", 0
        if stack == 0:
            return "side pot", 0

        cost_to_call = min(cost_to_call, stack)  # cap first
        options = [] # list of [action, amount, ev, with nudge]
        
        if cost_to_call > 0: # fold is only legal when there is something to call
            options.append(["fold", -1, 0]) # -1 is a placeholder for amount
        
        # adjust ev_call based on volatility (variance)
        adjusted_ev_call = ev_call + random.uniform(-self.volatility * big_blind, self.volatility * big_blind) # scaling by big_blind
        # increase or decrease ev_call based on how loose a player is
        adjusted_ev_call = adjusted_ev_call + (self.looseness - 1.0) * big_blind
        call_name = "check" if cost_to_call == 0 else "call"
        options.append([call_name, cost_to_call, adjusted_ev_call])

        if stack > cost_to_call: # otherwise calling is already all-in, so no raise exists
            min_raise = cost_to_call + big_blind
            bet_proportions = [0.1, 0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 1]
            # add all potential bet_sizes
            bet_sizes = {stack} # a set, so duplicates disappear; all-in is always an option
            for prop in bet_proportions:
                size = max(int(prop * pot), min_raise) # whole chips, never below the legal minimum
                if size < stack:
                    bet_sizes.add(size)

            raise_options = []
            volatility_amount = random.uniform(-self.volatility * big_blind, self.volatility * big_blind)
            for bet in sorted(bet_sizes):
                ev_raise = game.calculate_ev_raise(bet, betting_round, seat, hand)
                # scale ev_raise by volatiility
                adjusted_ev_raise = ev_raise + volatility_amount
                # increase or decrease ev_raise based on how loose a player is
                adjusted_ev_raise = adjusted_ev_raise + (self.looseness - 1.0) * big_blind     
                raise_options.append(["raise", bet, adjusted_ev_raise, adjusted_ev_raise])

            best_raise = max(raise_options, key=lambda option: option[2])

            # calculate bet_sizing nudge:
            nudge_factor = 0.25 * big_blind # needs calibration
            nudge_size = (self.bet_sizing - 0.5) * nudge_factor
            for option in raise_options:
                if option[1] > best_raise[1]: 
                    option[3] = option[2] + nudge_size
                elif option[1] < best_raise[1]: 
                    option[3] = option[2] - nudge_size
                else:
                    option[3] = option[2]
            
            # recalculate best raise option after bet_sizing nudge
            best_raise = max(raise_options, key=lambda option: option[3])

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

    def set_bet_sizing(self, bet_sizing):
        self.bet_sizing = bet_sizing