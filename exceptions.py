import deck

class QuitGame(Exception):
    def __init__(self):
        pass

def get_input(msg):
    try:
        ans = input(msg)
        if ans.strip().lower() == "q" or ans.strip().lower() == "quit":
            raise QuitGame()
        else:
            return ans
    except(KeyboardInterrupt, EOFError):
        raise QuitGame()

# The helpers below keep asking until the answer is valid (q still quits).

def get_int(msg, lo=None, hi=None):
    # whole number, optionally within [lo, hi]
    while True:
        try:
            n = int(get_input(msg).strip())
        except ValueError:
            print("Please enter a whole number.")
            continue
        if (lo is not None and n < lo) or (hi is not None and n > hi):
            bounds = f"between {lo} and {hi}" if lo is not None and hi is not None else f"at least {lo}" if lo is not None else f"at most {hi}"
            print(f"Please enter a number {bounds}.")
            continue
        return n

def get_yn(msg):
    # True for y, False for n
    while True:
        ans = get_input(msg).strip().lower()
        if ans in ("y", "n"):
            return ans == "y"
        print("Please enter Y or N.")

def get_cards(msg, count, taken=(), allow_empty=False):
    # exactly `count` distinct cards like "AhKd", none of which are in `taken`
    # returns a list like ["Ah", "Kd"] ([] if allow_empty and nothing was entered)
    while True:
        text = get_input(msg).strip()
        if allow_empty and text == "":
            return []
        cards = [text[i].upper() + text[i + 1].lower() for i in range(0, len(text) - 1, 2)]
        if len(text) != 2 * count or any(c not in deck.Deck.deck for c in cards):
            print(f"Please enter {count} card(s) like Ah, Td, 7c (rank then suit c/d/h/s).")
        elif len(set(cards)) < count or any(c in taken for c in cards):
            print("Those cards can't be used (duplicate or already dealt).")
        else:
            return cards
