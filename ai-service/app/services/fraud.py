def calculate_risk_score(employee_id: int, amount: float, category: str, merchant: str, date: str) -> dict:
    risk_score = 0.0
    flags = []
    
    # 1. Base rules logic: Amount deviation (Mocking historical data)
    # If the user's historical average is 1000, 4000 is high risk.
    mock_historical_avg = 1000.0  
    std_dev = 500.0
    
    if amount > mock_historical_avg + (3 * std_dev):
        flags.append("AMOUNT_DEVIATION_HIGH")
        risk_score += 0.4
    
    # 2. Velocity calculation (Mocking fast consecutive identical purchases)
    if risk_score > 0:
        flags.append("HIGH_VELOCITY_SUSPICION")
        risk_score += 0.2
        
    # Cap the score between 0.0 and 1.0
    final_score = min(1.0, risk_score)
    
    recommendation = "APPROVE"
    if final_score > 0.7:
        recommendation = "FLAG"
    elif final_score >= 0.3:
        recommendation = "REVIEW"

    return {
        "risk_score": final_score,
        "risk_flags": flags,
        "recommendation": recommendation
    }
