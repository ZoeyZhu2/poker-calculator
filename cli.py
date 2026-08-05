# reject invalid input
import game

def main():
    own_hand = input("Your hand (format: Ah Kd): ").split()
    num_players = int(input("Number of players (including you): "))
    own_position = input("Your position (BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO): ")

    poker_game = game.PokerGame(own_hand, own_position, num_players, [])
    while True:
        if not handle_status(update_folds(poker_game), poker_game):
            break
        
        board_cards = input("Flop dealt (format: Ah Kd Qs): ").split()
        for card in board_cards:
            poker_game.add_board_card(card)
        
        if not handle_status(update_folds(poker_game), poker_game):
            break
        
        board_card = input("Turn dealt (format: Ah): ")
        poker_game.add_board_card(board_card)

        if not handle_status(update_folds(poker_game), poker_game):
            break

        board_card = input("River dealt: (format: Ah)")

        if not handle_status(update_folds(poker_game), poker_game):
            break

        own_position = poker_game.get_own_pos()
        

def update_folds(poker_game):
    print(f"Current equity: {poker_game.get_equity()}")
    folds = input("Who has folded before you (BTN SB BB...): ").split()
    for fold in folds:
        poker_game.fold_player(fold)
    print(f"Current equity: {poker_game.get_equity()}")
    fold = input("Did you fold (Y/N): ").strip()
    if fold == "Y":
        next_str = input("Next round (Y/N): ").strip()
        if next_str == "N":
            return "quit"
        else:
            return "fold"
    else:
        folds = input("Who has folded after you (BTN SB BB...): ").split()
        for fold in folds:
            poker_game.fold_player(fold)
        print(f"Current equity: {poker_game.get_equity()}")
    
def handle_status(status, poker_game):
    if status == "quit":
        print("Game over!")
        return False
    elif status == "fold":
        print("Starting next round!")
        own_hand = input("Your hand (format: Ah Kd): ").split()
        num_players = int(input("Number of players (including you): "))
        poker_game.new_round(own_hand, num_players)
        return False
    return True
