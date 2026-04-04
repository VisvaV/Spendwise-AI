from datetime import datetime

def calculate_risk_score(employee_id: int, amount: float, category: str, merchant: str, date: str, department_id: int = None, role: str = None, recent_same_category_count: int = 0, recent_same_amount_count: int = 0) -> dict:
    risk_score = 0.0
    flags = []
    
    # 1. Role-based multipliers
    role_multipliers = {
        "Employee": 1.0,
        "Manager": 2.5,
        "Finance": 3.0,
        "Senior Approver": 4.0,
        "Admin": 5.0
    }
    multiplier = role_multipliers.get(role, 1.0)
    
    category_baselines = {
        "Travel": 4000.0,
        "Meals": 500.0,
        "Equipment": 10000.0,
        "Software": 2000.0,
        "Accommodation": 8000.0,
        "Training": 5000.0,
        "Marketing": 10000.0,
        "Miscellaneous": 500.0
    }
    
    base_avg = category_baselines.get(category, 1000.0)
    adjusted_avg = base_avg * multiplier
    std_dev = adjusted_avg * 0.5
    
    if amount > adjusted_avg + (3 * std_dev):
        flags.append("AMOUNT_DEVIATION_HIGH")
        risk_score += 0.4
        
    if merchant == "UNKNOWN":
        flags.append("UNRECOGNIZED_MERCHANT")
        risk_score += 0.1
        
    # 2. Date/Time checks
    try:
        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
        if dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            flags.append("WEEKEND_EXPENSE")
            risk_score += 0.15
        
        ist_hour = (dt.hour + 5) % 24
        if ist_hour < 7 or ist_hour > 22:
            flags.append("OFF_HOURS_EXPENSE")
            risk_score += 0.2
    except ValueError:
        pass
        
    # 3. Real velocity scoring
    if recent_same_category_count >= 3:
        flags.append("HIGH_VELOCITY_SUSPICION")
        risk_score += 0.25
        
    if recent_same_amount_count >= 2:
        flags.append("DUPLICATE_AMOUNT_PATTERN")
        risk_score += 0.3
        
    # 4. Round number detection
    if amount % 100 == 0 and amount > 1000:
        flags.append("ROUND_NUMBER_SUSPICION")
        risk_score += 0.1
        
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
