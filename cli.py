import cli_mode1
import cli_mode2
from exceptions import QuitGame
from exceptions import get_input

def main():
    
    while True:
        try:
            mode = get_input("Mode 1 or 2: ")
            mode = mode.strip()
            if mode == "2":
                cli_mode2.main()
                break
            if mode == "1":
                cli_mode1.main()
                break
            else:
                print("Input 1 or 2")
        except QuitGame:
            print("Quitting game")
            return



if __name__ == "__main__": 
    main()