# reject invalid input
import game

def main():
    new_round = True
    own_hand = input("Your hand (format: Ah Kd): ").split()
    num_players = int(input("Number of players (including you): "))
    own_position = input("Your position (BTN, SB, BB, UTG, UTG+1, UTG+2, LJ, HJ, CO): ")

    poker_game = game.PokerGame(own_hand, own_position, num_players, [])
    while new_round:
        print(f"Current equity: {poker_game.get_equity()}")
        folds = input("Who has folded before you (BTN SB BB...): ").split()
        for fold in folds:
            poker_game.fold_player(fold)
        print(f"Current equity: {poker_game.get_equity()}")
        fold = input("Did you fold (Y/N): ").strip()
        if fold == "Y":
            next_str = input("Next round (Y/N): ").strip()
            if next_str == "N":
                print("Game ending!")
                new_round = False
                return
            else:
                print("Starting next round!")
                own_hand = input("Your hand (format: Ah Kd): ").split()
                num_players = int(input("Number of players (including you): "))
                poker_game.new_round(own_hand, num_players)
                continue
        else:
            folds = input("Who has folded after you (BTN SB BB...): ").split()
            for fold in folds:
                poker_game.fold_player(fold)
            print(f"Current equity: {poker_game.get_equity()}")
        
        board_cards = input("Flop dealt (format: Ah Kd Qs): ").split()
        for card in board_cards:
            poker_game.add_board_card(card)
        
        print(f"Current equity: {poker_game.get_equity()}")
        folds = input("Who has folded (BTN SB BB...): ").split()
        for fold in folds:
            poker_game.fold_player(fold)
        print(f"Current equity: {poker_game.get_equity()}")
        fold = input("Did you fold (Y/N): ").strip()
        if fold == "Y":
            next_str = input("Next round (Y/N): ").strip()
            if next_str == "N":
                print("Game ending!")
                new_round = False
                return
            else:
                print("Starting next round!")
                own_hand = input("Your hand (format: Ah Kd): ").split()
                num_players = int(input("Number of players (including you): "))
                poker_game.new_round(own_hand, num_players)
                continue
        else:
            folds = input("Who has folded after you (BTN SB BB...): ").split()
            for fold in folds:
                poker_game.fold_player(fold)
            print(f"Current equity: {poker_game.get_equity()}")
        
        board_card = input("Turn dealt (format: Ah): ")
        poker_game.add_board_card(board_card)

        print(f"Current equity: {poker_game.get_equity()}")
        folds = input("Who has folded before you (BTN SB BB...): ").split()
        for fold in folds:
            poker_game.fold_player(fold)
        print(f"Current equity: {poker_game.get_equity()}")
        fold = input("Did you fold (Y/N): ").strip()
        if fold == "Y":
            next_str = input("Next round (Y/N): ").strip()
            if next_str == "N":
                print("Game ending!")
                new_round = False
                return
            else:
                print("Starting next round!")
                own_hand = input("Your hand (format: Ah Kd): ").split()
                num_players = int(input("Number of players (including you): "))
                poker_game.new_round(own_hand, num_players)
                continue
        else:
            folds = input("Who has folded after you (BTN SB BB...): ").split()
            for fold in folds:
                poker_game.fold_player(fold)
            print(f"Current equity: {poker_game.get_equity()}")

        board_card = input("River dealt: (format: Ah)")
        print(f"Current equity: {poker_game.get_equity()}")
        folds = input("Who has folded before you (BTN SB BB...): ").split()
        for fold in folds:
            poker_game.fold_player(fold)
        print(f"Current equity: {poker_game.get_equity()}")
        fold = input("Did you fold (Y/N): ").strip()
        if fold == "Y":
            next_str = input("Next round (Y/N): ").strip()
            if next_str == "N":
                print("Game ending!")
                new_round = False
                return
            else:
                print("Starting next round!")
                own_hand = input("Your hand (format: Ah Kd): ").split()
                num_players = int(input("Number of players (including you): "))
                poker_game.new_round(own_hand, num_players)
                continue
        else:
            folds = input("Who has folded after you (BTN SB BB...): ").split()
            for fold in folds:
                poker_game.fold_player(fold)
            print(f"Current equity: {poker_game.get_equity()}")

        

