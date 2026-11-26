# contains decision logic for game.py

import position_ranges
import numpy as np
import random
import equity_calculator

# getting range equities (so an estimation)
# wrapper function
def get_equity(snapshot: dict, seat=None, hand=None, n_sims=5000):
    return get_bet_equity(snapshot, seat=seat, hand=hand, n_sims=n_sims)

def calculate_ev_call(snapshot: dict, equity, cost_to_call):
    pot_size = snapshot["pot_size"]
    return equity * (pot_size + cost_to_call) - cost_to_call

def calculate_ev_raise(snapshot: dict, bet, betting_round, seat=None, hand=None, n_sims=1000):
    # note: opponent reraise will be built later
    # we are calculating aggregate ev and new_equity will be calculated based on all the remaining opponents' ranges
    # p_call as it is is probability of continuining (so call and reraise included)
    if seat is None:
        seat = snapshot["own_seat"]
    if hand is None:
        hand = snapshot["own_hand"]
    heads_up = snapshot["num_players"] == 2
    board_cards = snapshot["board_cards"]
    pot_size = snapshot["pot_size"]
    contributions = snapshot["contributions"]
    seats_in = snapshot["seats_in"]
    stacks = snapshot["stacks"]
    bet = min(bet, stacks[seat])
    rotation = snapshot["rotation"]
    traits = snapshot["traits"]
    board_texture = position_ranges.get_board_texture(board_cards)
    fold_probs = [] # one entry per opponent who still has chips behind
    fold_by_seat = dict() # seat -> fold probability
    call_cost_by_seat = dict() # seat -> chips opponent adds if they call
    all_in_seats = []
    num_all_in = 0 # all-in opponents always continue
    for s, value in seats_in.items():
        if s == seat or not value:
            continue
        if stacks[s] == 0:
            num_all_in += 1
            all_in_seats.append(s)
        else:
            pos = rotation[s]
            # what it costs this opponent to call
            call_cost = min(max(contributions[seat] + bet - contributions[s], 0), stacks[s])
            pf = position_ranges.get_prob_fold(pos, traits[s], call_cost, pot_size + bet, stacks[s], betting_round, board_texture, heads_up=heads_up)
            fold_probs.append(pf)
            fold_by_seat[s] = pf
            call_cost_by_seat[s] = call_cost

    # only win the pot uncontested if EVERY opponent folds
    p_all_fold = 0 if num_all_in > 0 else 1
    for pf in fold_probs:
        p_all_fold *= pf
    if p_all_fold == 1:
        return pot_size
    p_cont = 1 - p_all_fold # prob of round continuing
    # expected callers overall, then divided by p_cont to get callers given that someone called
    expected_callers = num_all_in + sum(1 - pf for pf in fold_probs)
    callers_if_cont = expected_callers / p_cont # expected value removing the p_fold from the calculation

    bet_ratio = bet / pot_size
    scale_factor = 0.3 # arbitrary. how much tighter opponents will get with bet-sizing
    tightness = bet_ratio * scale_factor

    num_callers = max(1, round(callers_if_cont)) - num_all_in # excluding all-ins!
    likely = sorted(fold_by_seat, key=fold_by_seat.get)[:max(num_callers, 0)] # the seats of the callers
    continuing = set(all_in_seats) | set(likely) # this is now all the callers
    new_equity = get_bet_equity(snapshot, tightness=tightness, seat=seat, hand=hand, n_sims=n_sims, only_seats=continuing) # only calculate equity against continuing players

    # expected chips callers add, given the round continues. all-in opponents add nothing (their chips are already in the pot)
    # and short stacks add only what they can actually call
    expected_call_chips = sum((1 - fold_by_seat[s]) * call_cost_by_seat[s] for s in fold_by_seat) / p_cont

    # any part of the bet that no continuing opponent can match is returned to us, so we only risk what can be matched
    matchable = []
    for s in continuing:
        if s in call_cost_by_seat:
            matchable.append(contributions[s] + call_cost_by_seat[s] - contributions[seat])
        else: # all-in opponent: their total commitment is already fixed
            matchable.append(contributions[s] - contributions[seat])
    effective_bet = min(bet, max(max(matchable), 0))

    ev = p_all_fold * pot_size + p_cont * (new_equity * (pot_size + effective_bet + expected_call_chips) - effective_bet)
    return ev


def get_bet_equity(snapshot: dict, tightness=0, seat=None, hand=None, n_sims=1000, only_seats=None):
    if seat is None:
        seat = snapshot["own_seat"]
    if hand is None:
        hand = snapshot["own_hand"]
    heads_up = snapshot["num_players"] == 2
    board_cards = snapshot["board_cards"]
    seats_in = snapshot["seats_in"]
    stacks = snapshot["stacks"]
    rotation = snapshot["rotation"]
    traits = snapshot["traits"]
    dead = set(hand) | set(board_cards)
    ranges = dict() # position -> all unblocked range hands
    for key, value in seats_in.items():
        if key == seat or (only_seats is not None and key not in only_seats):
            continue
        if value:
            pos = rotation[key]
            if stacks[key] == 0:
                looseness = traits[key]
            else:
                looseness = max(traits[key]-tightness, 0)
            while True:
                range_hands = position_ranges.get_range_hands(pos, heads_up=heads_up, looseness=looseness)
                live = [c for c in range_hands if c[0] not in dead and c[1] not in dead]
                if len(live) >= 6: # arbitrary live cutoff
                    break
                looseness += 0.05 # widening looseness until a possible card is chosen
            ranges[key] = live
    equities_sum = np.zeros(len(ranges) + 1)
    completed = 0
    for i in range(n_sims):
        pocket_list = [hand]
        selected_cards = set(dead)
        all_dealt = True
        for key, value in ranges.items():
            dealt = False
            for _ in range(50):
                random_cards = random.choice(value)
                card1, card2 = random_cards
                if card1 not in selected_cards and card2 not in selected_cards:
                    dealt = True
                    break
            if not dealt:
                all_dealt = False
                break
            selected_cards.add(card1)
            selected_cards.add(card2)
            pocket_list.append(random_cards)
        if all_dealt:
            equity_list = equity_calculator.calculate_equity(pocket_list, board_cards, 1)
            equities_sum = equities_sum + np.array(equity_list)
            completed += 1
    if completed == 0:
        range_sizes = {seat_key: len(hands) for seat_key, hands in ranges.items()}
        raise RuntimeError(f"No simulations completed: could not deal non-overlapping hands to all opponents (live range sizes by seat: {range_sizes})")
    avg_equities = equities_sum / completed
    return avg_equities[0]
