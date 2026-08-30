import cli_mode2
from exceptions import QuitGame
from exceptions import get_input

def main():
    
    while True:
        try:
            mode = get_input("Mode 1 or 2: ")
            if mode == "2":
                cli_mode2.main()
                break
            if mode == "1":
                pass
                break
        except QuitGame:
            print("Quitting game")
            return



if __name__ == "__main__": 
    main()