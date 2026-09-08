def calculate(principal, rate, time, additional=0, frequency=12):
    result = principal
    rate_per_period = rate / 100 / frequency
    total_periods = time * frequency

    for period in range(1, total_periods + 1):
        interest = result * rate_per_period
        result += interest
        if period % frequency == 0 and period < total_periods:
            result += additional

    return {
        "final_amount": round(result, 2),
        "interest_earned": round(result - principal - (additional * (time - 1)), 2),
        "total_contributions": principal + (additional * (time - 1))
    }