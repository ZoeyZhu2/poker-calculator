import bot

def print_result(label, result):
    print(f"{label}: {result}")

# Test 1: High equity, should raise (equity > aggressiveness)
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=1000)
result = b.decision(equity=0.8, pot=100, cost_to_call=10)
print_result("High equity (0.8), no noise -> expect raise", result)

# Test 2: Low equity, bad pot odds, should fold
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=1000)
result = b.decision(equity=0.05, pot=100, cost_to_call=50)
print_result("Low equity (0.05), bad odds -> expect fold", result)

# Test 3: Low equity, but good pot odds, should call
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=1000)
result = b.decision(equity=0.15, pot=100, cost_to_call=5)
print_result("Low equity (0.15), good pot odds -> expect call", result)

# Test 4: Equity right at aggressiveness threshold
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=1000)
result = b.decision(equity=0.5, pot=100, cost_to_call=10)
print_result("Equity == aggressiveness (0.5) -> expect call (not >)", result)

# Test 5: Raise amount capped by stack
b = bot.bot(volatility=0.0, aggressiveness=0.3, stack=20)
result = b.decision(equity=0.9, pot=100, cost_to_call=10)
print_result("Small stack (20), high equity -> expect raise capped at stack", result)
print(f"  Remaining stack: {b.stack} (should be 0)")

# Test 6: Call amount capped by stack
b = bot.bot(volatility=0.0, aggressiveness=0.9, stack=5)
result = b.decision(equity=0.3, pot=100, cost_to_call=50)
print_result("Small stack (5), call cost exceeds stack -> expect call capped at stack", result)
print(f"  Remaining stack: {b.stack} (should be 0)")

# Test 7: Stack already at 0
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=0)
result = b.decision(equity=0.9, pot=100, cost_to_call=10)
print_result("Stack == 0 -> expect side pot", result)

# Test 8: Stack negative (shouldn't normally happen, but test the guard)
b = bot.bot(volatility=0.0, aggressiveness=0.5, stack=-5)
result = b.decision(equity=0.9, pot=100, cost_to_call=10)
print_result("Stack < 0 -> expect exit", result)

# Test 9: High volatility - run multiple times, expect variation
print("\nHigh volatility test (run 5 times, same inputs, expect different results sometimes):")
for i in range(5):
    b = bot.bot(volatility=1.0, aggressiveness=0.5, stack=1000)
    result = b.decision(equity=0.11, pot=100, cost_to_call=14)  # borderline EV
    print_result(f"  Trial {i+1}", result)