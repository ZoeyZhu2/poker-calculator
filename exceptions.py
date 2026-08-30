class QuitGame(Exception):
    def __init__(self):
        pass

def get_input(msg):
    ans = input(msg)
    if ans.strip().lower() == "q" or ans.strip().lower() == "quit":
        raise QuitGame()
    else:
        return ans