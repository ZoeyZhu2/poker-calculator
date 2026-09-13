import position_ranges

boards = {
    "dry rainbow":        ["2c", "8d", "Ks"],
    "wet monotone straight": ["9h", "Th", "Jh"],
    "suit-only wet":      ["2h", "7h", "Kh"],
    "rank-only wet":      ["8c", "9d", "Th"],
    "paired, otherwise dry": ["7c", "7d", "2s"],
    "paired, otherwise wet": ["7h", "7s", "8h"],
    "trips":              ["7c", "7d", "7h"],
    "quads (turn)":       ["7c", "7d", "7h", "7s"],
}
for name, board in boards.items():
    print(f"{name}: {position_ranges.get_board_texture(board)}")