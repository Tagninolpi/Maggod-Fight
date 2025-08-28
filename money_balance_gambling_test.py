def gain(v, b):
    if v > 0:
        return b * (89 - 8*v) / 90.0
    elif v == 0:
        return b
    else:  # v < 0
        return b * (-v + 1)

def scaled_gain(v, bet, wealth, fraction, reduction_neg=0.5, reduction_pos=0.2):
    base = gain(v, bet)
    if v > 0:
        scale = 1 - fraction * reduction_pos
    else:
        scale = 1 - fraction * reduction_neg
    return base * scale  # returns only net gain

# Example table
fractions = [0.1, 0.3, 0.5, 0.75, 1.0]
print("Value | " + " | ".join([f"{int(f*100)}%" for f in fractions]))
print("-"*50)

# Loop for negative and zero values (step 2)
for v in range(-10, 1, 2):
    line = f"{v:>5} | " + " | ".join([f"{scaled_gain(v, 100, 1000, f):>7.2f}" for f in fractions])
    print(line)

# Loop for positive values (step 2)
for v in range(2, 11, 2):
    line = f"{v:>5} | " + " | ".join([f"{scaled_gain(v, 100, 1000, f):>7.2f}" for f in fractions])
    print(line)

def true_gain(v, bet, wealth, reduction_neg=0.5, reduction_pos=0.2):
    fraction = bet / wealth
    if v > 0:
        base = bet * (89 - 8*v) / 90.0
        scale = 1 - fraction * reduction_pos
    elif v == 0:
        base = bet
        scale = 1 - fraction * reduction_pos
    else:  # v < 0
        base = bet * (-v + 1)
        scale = 1 - fraction * reduction_neg
    return base * scale  # only the gain

# Example of true gain
print(true_gain(10, 1000, 1000))
