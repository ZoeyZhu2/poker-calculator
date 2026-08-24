# reject invalid input
# I will actually have this redirect to two more files, a cli for mode 1 and a cli for mode 2
import game

def main():
    mode = input("Mode 1 or 2: ")
    if mode == "2":
        # run cli_mode2.py
        pass
    if mode == "1":
        pass
    if mode == "q":
        return
    
if __name__ == "__main__":
    main()