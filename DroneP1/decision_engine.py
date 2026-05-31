def evaluate_signal(signal):
    if signal > -75:
        return "GOOD"
    
    elif signal > -90:
        return "WEAK"
    else:
        return "NOT FEASIBLE"