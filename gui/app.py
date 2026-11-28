"""Temporary web GUI for cli_mode1 / cli_mode2.

Run from the project root:  python3 gui/app.py   then open http://127.0.0.1:5000

Nothing in the existing code is edited. We run the CLI's main() in a background
thread and swap out, inside that module only:
  - get_input  -> (also patched in exceptions.py, where the validators live) blocks until the browser answers
  - print      -> goes to a log (and is parsed for equity/EV)
  - update_action -> wrapped so we can grab the PokerGame object for the table view
"""
import os
import queue
import re
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, jsonify, request, send_file  # noqa: E402

import cli_mode1  # noqa: E402
import cli_mode2  # noqa: E402
import exceptions  # noqa: E402
from exceptions import QuitGame  # noqa: E402

app = Flask(__name__)
MODES = {"1": cli_mode1, "2": cli_mode2}
NEW_HAND = re.compile(r"^(Flop|Turn|River) dealt|^This is your hand|^Your hand")


class Session:
    def __init__(self, mode):
        self.mode = mode
        self.module = MODES[mode]
        self.game = None        # PokerGame, grabbed from update_action
        self.hands = {}         # seat -> hand for bots (mode 1 only; hidden until showdown)
        self.revealed = {}      # seat -> hand shown at showdown
        self.actions = {}       # seat -> last action text this street
        self.log = []
        self.hud = {}           # equity / ev_call / ev_raise
        self.prompt = None
        self.bb = 0
        self.status = "running"  # running | finished | error
        self.answers = queue.Queue()

    # --- things the CLI code calls (installed into the cli module) ---
    def get_input(self, msg):
        self.new_street(msg)
        self.prompt = msg
        ans = self.answers.get()  # blocks until the browser answers
        self.prompt = None
        if ans is None or ans.strip().lower() in ("q", "quit"):
            raise QuitGame()
        self.log.append("› " + ans)
        self.note_answer(msg, ans)
        return ans

    def print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args).strip()
        self.new_street(text)
        self.log.append(text)
        if m := re.match(r"Current equity: (.*)", text):
            self.hud["equity"] = m.group(1)
        elif m := re.match(r"Current EV to call: (.*)", text):
            self.hud["ev_call"] = m.group(1)
            self.hud.pop("ev_raise", None)
        elif m := re.match(r"Current EV to raise: (.*)", text):
            self.hud["ev_raise"] = m.group(1)
        elif m := re.match(r"The player in seat (\d) (\w+?)s? (\d+)", text):
            self.actions[int(m.group(1))] = f"{m.group(2)} {m.group(3)}"
            time.sleep(0.6)  # pace the bots so the hand is followable
        elif m := re.match(r"Player in seat (\d) folds", text):
            self.actions[int(m.group(1))] = "fold"
        elif m := re.match(r"Player in seat (\d) has \[(.*)\]", text):
            self.revealed[int(m.group(1))] = re.findall(r"\w\w", m.group(2))

    def update_action(self, poker_game, *args, **kwargs):
        self.game = poker_game
        if self.mode == "1":
            self.hands = args[2]  # args = (betting_round, player_seats, player_hands, ...)
        return self.orig_update_action(poker_game, *args, **kwargs)

    # --- helpers ---
    def new_street(self, text):
        if NEW_HAND.match(text):
            self.actions = {}
            if text.startswith(("This is your hand", "Your hand")):
                self.revealed = {}

    def note_answer(self, msg, ans):
        low = msg.lower()
        if "big blind" in low:
            self.bb = int(ans)
        if m := re.search(r"How much did the player in seat (\d) put in", msg):
            n = int(ans)
            self.actions[int(m.group(1))] = "fold" if n < 0 else "check" if n == 0 else f"bet {n}"
        elif "How much do you bet" in msg:
            n = int(ans)
            self.actions[self.game.get_own_seat()] = "fold" if n < 0 else "check" if n == 0 else f"bet {n}"
        elif m := re.search(r"Input seat (\d)'s hand", msg):
            if ans.strip():
                self.revealed[int(m.group(1))] = re.findall(r"\w\w", ans.strip())

    def describe_prompt(self):
        msg = self.prompt
        if msg is None:
            return None
        p = {"text": msg, "kind": "text"}
        g = self.game
        seat = None
        if m := re.search(r"How much did the player in seat (\d) put in", msg):
            seat = int(m.group(1))
        elif "How much do you bet" in msg:
            seat = g.get_own_seat()
        if seat is not None and g:
            to_call = g.get_max_contribution() - g.get_seat_contribution(seat)
            p.update(kind="action", seat=seat, to_call=to_call, stack=g.get_stack(seat),
                     min_raise=to_call + self.bb, pot=g.get_pot())
        elif "raise to calculate new EV" in msg:
            p["kind"] = "ev"
        elif "(Y/N)" in msg:
            p["kind"] = "yn"
        elif "Flop dealt" in msg:
            p.update(kind="cards", count=3)
        elif re.search(r"Turn dealt|River dealt", msg):
            p.update(kind="cards", count=1)
        elif re.search(r"Your hand|Input seat \d's hand", msg):
            p.update(kind="cards", count=2, optional="Input seat" in msg)
        return p

    def table(self):
        g = self.game
        if g is None:
            return None
        contrib = g.get_player_contributions()
        seats = []
        for s in list(g.get_occupied_seats()):
            if s == g.get_own_seat():
                hand = list(g.own_hand)
            else:
                hand = self.revealed.get(s)
            seats.append({
                "seat": s, "pos": g.rotation.get(s), "stack": g.get_stack(s),
                "in_pot": contrib[s], "folded": not g.get_seats_in()[s],
                "action": self.actions.get(s), "hand": hand,
                "bot_hand": self.hands.get(s) if s != g.get_own_seat() else None,
            })
        return {"seats": seats, "own_seat": g.get_own_seat(), "board": list(g.board_cards),
                "pot": g.get_pot()}

    def state(self):
        return {"mode": self.mode, "status": self.status, "log": self.log[-60:],
                "hud": self.hud, "prompt": self.describe_prompt(), "table": self.table()}


session = None


def start(mode):
    global session
    if session and session.status == "running":
        session.answers.put(None)  # unblock the old game so its thread exits
        time.sleep(0.1)
    s = session = Session(mode)
    mod = s.module
    for m in (mod, exceptions):  # exceptions holds the get_int/get_yn/get_cards helpers
        m.get_input, m.print = s.get_input, s.print
    s.orig_update_action = mod.update_action
    mod.update_action = s.update_action

    def run():
        try:
            mod.main()
            s.status = "finished"
        except Exception as e:  # the CLI code has no input validation
            s.log.append(f"ERROR: {e!r}")
            s.status = "error"
        finally:
            mod.update_action = s.orig_update_action

    threading.Thread(target=run, daemon=True).start()


@app.get("/")
def index():
    return send_file(os.path.join(os.path.dirname(__file__), "index.html"))


@app.post("/start")
def start_route():
    start(request.json["mode"])
    return jsonify(ok=True)


@app.post("/answer")
def answer_route():
    if session and session.prompt is not None:
        session.answers.put(str(request.json["value"]))
    return jsonify(ok=True)


@app.get("/state")
def state_route():
    return jsonify(session.state() if session else {"status": "idle"})


if __name__ == "__main__":
    app.run(port=5000, threaded=True)
