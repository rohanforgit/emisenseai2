import math
from datetime import datetime, timedelta

def calculate_emi(principal, annual_rate, tenure_months):
    """
    Calculate the monthly EMI using standard compounding formula.
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if annual_rate <= 0:
        return principal / tenure_months
        
    r = (annual_rate / 12.0) / 100.0
    try:
        emi = principal * r * ((1 + r) ** tenure_months) / (((1 + r) ** tenure_months) - 1)
        return round(emi, 2)
    except ZeroDivisionError:
        return round(principal / tenure_months, 2)

def simulate_amortization(principal, annual_rate, tenure_months, 
                          extra_monthly=0.0, annual_prepayment=0.0, 
                          lump_sum=0.0, lump_sum_month=1):
    """
    Simulates a month-by-month amortization schedule, incorporating:
    - Standard monthly EMI
    - Additional monthly prepayments
    - Recurring annual prepayments (applied every 12 months)
    - A one-time lump-sum prepayment (applied at a specific month)
    
    Returns a list of monthly stats.
    """
    base_emi = calculate_emi(principal, annual_rate, tenure_months)
    r = (annual_rate / 12.0) / 100.0
    
    balance = principal
    schedule = []
    
    total_interest_paid = 0.0
    total_principal_paid = 0.0
    total_payment = 0.0
    
    month = 1
    max_months = 600  # 50 years safety limit
    
    if r > 0 and base_emi <= balance * r:
        # Prevent infinite loop if EMI is smaller than monthly interest
        base_emi = balance * r + 1.0
        
    while balance > 0.01 and month <= max_months:
        interest_this_month = balance * r if r > 0 else 0.0
        
        # Calculate base payment
        payment_this_month = base_emi
        if payment_this_month > (balance + interest_this_month):
            payment_this_month = balance + interest_this_month
            
        principal_this_month = payment_this_month - interest_this_month
        if principal_this_month < 0:
            principal_this_month = 0.0
            
        balance -= principal_this_month
        
        # Apply extra monthly payment
        applied_extra_monthly = 0.0
        if balance > 0 and extra_monthly > 0:
            applied_extra_monthly = min(extra_monthly, balance)
            balance -= applied_extra_monthly
            
        # Apply lump sum (one-time)
        applied_lump_sum = 0.0
        if balance > 0 and lump_sum > 0 and month == lump_sum_month:
            applied_lump_sum = min(lump_sum, balance)
            balance -= applied_lump_sum
            
        # Apply annual prepayment (every 12th month)
        applied_annual = 0.0
        if balance > 0 and annual_prepayment > 0 and month % 12 == 0:
            applied_annual = min(annual_prepayment, balance)
            balance -= applied_annual
            
        actual_paid_principal = principal_this_month + applied_extra_monthly + applied_lump_sum + applied_annual
        actual_paid_interest = interest_this_month
        actual_total_payment = payment_this_month + applied_extra_monthly + applied_lump_sum + applied_annual
        
        total_interest_paid += actual_paid_interest
        total_principal_paid += actual_paid_principal
        total_payment += actual_total_payment
        
        schedule.append({
            "month": month,
            "interest": round(actual_paid_interest, 2),
            "principal": round(actual_paid_principal, 2),
            "extra_payment": round(applied_extra_monthly + applied_lump_sum + applied_annual, 2),
            "total_payment": round(actual_total_payment, 2),
            "remaining_balance": round(max(0.0, balance), 2),
            "cumulative_interest": round(total_interest_paid, 2),
            "cumulative_principal": round(total_principal_paid, 2),
            "cumulative_payment": round(total_payment, 2)
        })
        
        month += 1
        
    return schedule

def calculate_base_loan_details(principal, annual_rate, tenure_months, start_date=None):
    """
    Computes baseline stats: EMI, total interest, total payment, debt-free date, etc.
    """
    if start_date is None:
        start_date = datetime.now()
        
    emi = calculate_emi(principal, annual_rate, tenure_months)
    schedule = simulate_amortization(principal, annual_rate, tenure_months)
    
    total_interest = sum(m["interest"] for m in schedule)
    total_payment = sum(m["total_payment"] for m in schedule)
    actual_tenure = len(schedule)
    
    interest_percentage = (total_interest / total_payment * 100.0) if total_payment > 0 else 0.0
    debt_free_date = start_date + timedelta(days=actual_tenure * 30.4375)
    
    return {
        "emi": emi,
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
        "interest_percentage": round(interest_percentage, 2),
        "actual_tenure_months": actual_tenure,
        "debt_free_date": debt_free_date,
        "schedule": schedule
    }

def simulate_emi_increase(principal, annual_rate, tenure_months, increase_percent):
    """
    Simulates scaling the standard EMI by a percentage.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    base_emi = base["emi"]
    
    new_emi = base_emi * (1.0 + increase_percent / 100.0)
    extra_monthly = new_emi - base_emi
    
    schedule = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=extra_monthly)
    
    new_total_interest = sum(m["interest"] for m in schedule)
    new_total_payment = sum(m["total_payment"] for m in schedule)
    new_tenure = len(schedule)
    
    interest_saved = base["total_interest"] - new_total_interest
    money_saved = base["total_payment"] - new_total_payment
    years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
    
    return {
        "new_emi": round(new_emi, 2),
        "new_tenure_months": new_tenure,
        "interest_saved": round(interest_saved, 2),
        "money_saved": round(money_saved, 2),
        "years_saved": round(max(0.0, years_saved), 2),
        "schedule": schedule
    }

def simulate_annual_prepayment(principal, annual_rate, tenure_months, annual_prepayment):
    """
    Simulates making a fixed extra payment once every 12 months.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    
    schedule = simulate_amortization(principal, annual_rate, tenure_months, annual_prepayment=annual_prepayment)
    
    new_total_interest = sum(m["interest"] for m in schedule)
    new_total_payment = sum(m["total_payment"] for m in schedule)
    new_tenure = len(schedule)
    
    interest_saved = base["total_interest"] - new_total_interest
    money_saved = base["total_payment"] - new_total_payment
    years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
    
    return {
        "new_tenure_months": new_tenure,
        "interest_saved": round(interest_saved, 2),
        "money_saved": round(money_saved, 2),
        "years_saved": round(max(0.0, years_saved), 2),
        "schedule": schedule
    }

def simulate_lump_sum(principal, annual_rate, tenure_months, lump_sum_amount, mode="reduce_tenure"):
    """
    Simulates a one-time lump sum payment at month 1.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    
    if mode == "reduce_tenure":
        schedule = simulate_amortization(principal, annual_rate, tenure_months, lump_sum=lump_sum_amount, lump_sum_month=1)
        new_total_interest = sum(m["interest"] for m in schedule)
        new_total_payment = sum(m["total_payment"] for m in schedule)
        new_tenure = len(schedule)
        
        interest_saved = base["total_interest"] - new_total_interest
        money_saved = base["total_payment"] - new_total_payment
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        return {
            "mode": "reduce_tenure",
            "reduced_principal": max(0.0, principal - lump_sum_amount),
            "new_emi": base["emi"],
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "money_saved": round(money_saved, 2),
            "years_saved": round(max(0.0, years_saved), 2),
            "schedule": schedule
        }
    else: # reduce_emi
        reduced_principal = max(0.0, principal - lump_sum_amount)
        new_emi = calculate_emi(reduced_principal, annual_rate, tenure_months)
        schedule = simulate_amortization(reduced_principal, annual_rate, tenure_months)
        
        new_total_interest = sum(m["interest"] for m in schedule)
        new_total_payment = sum(m["total_payment"] for m in schedule) + lump_sum_amount
        new_tenure = len(schedule)
        
        interest_saved = base["total_interest"] - new_total_interest
        money_saved = base["total_payment"] - new_total_payment
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        return {
            "mode": "reduce_emi",
            "reduced_principal": reduced_principal,
            "new_emi": round(new_emi, 2),
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "money_saved": round(money_saved, 2),
            "years_saved": round(max(0.0, years_saved), 2),
            "schedule": schedule
        }

def simulate_interest_rate_comparison(principal, tenure_months, current_rate):
    """
    Compares rate options from 7.0% to 12.0% against the current rate.
    """
    rates = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
    if current_rate not in rates:
        rates.append(current_rate)
    rates = sorted(list(set(rates)))
    
    base = calculate_base_loan_details(principal, current_rate, tenure_months)
    comparison = []
    
    for rate in rates:
        details = calculate_base_loan_details(principal, rate, tenure_months)
        emi_diff = details["emi"] - base["emi"]
        interest_diff = details["total_interest"] - base["total_interest"]
        savings = -interest_diff
        
        comparison.append({
            "rate": rate,
            "emi": details["emi"],
            "total_interest": details["total_interest"],
            "total_payment": details["total_payment"],
            "emi_difference": round(emi_diff, 2),
            "interest_difference": round(interest_diff, 2),
            "total_savings": round(savings, 2)
        })
        
    return comparison

def calculate_refinancing(principal, current_rate, remaining_tenure_months, new_rate, refinancing_cost):
    """
    Analyzes refinancing feasibility.
    """
    base = calculate_base_loan_details(principal, current_rate, remaining_tenure_months)
    new_loan = calculate_base_loan_details(principal, new_rate, remaining_tenure_months)
    
    monthly_saving = base["emi"] - new_loan["emi"]
    gross_interest_saved = base["total_interest"] - new_loan["total_interest"]
    net_savings = gross_interest_saved - refinancing_cost
    
    if monthly_saving > 0:
        break_even_months = refinancing_cost / monthly_saving
    else:
        break_even_months = float('inf')
        
    worth_refinancing = net_savings > 0 and break_even_months < remaining_tenure_months
    
    return {
        "current_emi": base["emi"],
        "new_emi": new_loan["emi"],
        "monthly_saving": round(monthly_saving, 2),
        "gross_interest_saved": round(gross_interest_saved, 2),
        "net_savings": round(net_savings, 2),
        "break_even_months": round(break_even_months, 2) if break_even_months != float('inf') else "N/A",
        "worth_refinancing": worth_refinancing
    }

def calculate_emi_to_income(monthly_emi, monthly_income):
    """
    Calculates Debt Ratio (EMI / Income) and classifies the risk.
    """
    if monthly_income <= 0:
        return 0.0, "Dangerous", "Invalid monthly income input."
        
    ratio = (monthly_emi / monthly_income) * 100.0
    
    if ratio < 20.0:
        category = "Excellent"
        advice = "Your debt load is very healthy. You have significant financial freedom."
    elif ratio < 30.0:
        category = "Good"
        advice = "Your debt load is manageable. Recommended to keep it under 30%."
    elif ratio < 40.0:
        category = "Average"
        advice = "You are spending a significant portion of income on debt. Avoid any new loans."
    elif ratio < 50.0:
        category = "Poor"
        advice = "Debt payments consume nearly half your income. Consider urgent optimization."
    else:
        category = "Danger"
        advice = "DANGER! Debt payments exceed 50% of income. High risk of financial distress."
        
    return round(ratio, 2), category, advice

def calculate_emergency_fund(monthly_expenses, monthly_emi, current_reserve):
    """
    Compares current reserves with 3/6/12 months of expenses + EMI.
    """
    monthly_outflow = monthly_expenses + monthly_emi
    
    fund_3m = monthly_outflow * 3
    fund_6m = monthly_outflow * 6
    fund_12m = monthly_outflow * 12
    
    recommended = fund_6m
    gap = recommended - current_reserve
    
    if current_reserve >= fund_12m:
        advice = "Superb! You have over 12 months of runway. You can aggressively prepay loans."
    elif current_reserve >= fund_6m:
        advice = "Excellent. Solid 6-month buffer. You are well-positioned to make prepayments."
    elif current_reserve >= fund_3m:
        advice = "Adequate. 3-month buffer. Grow it to 6 months before aggressively prepaying low-rate debt."
    else:
        advice = "Warning! Reserves below 3-month threshold. Focus on savings first."
        
    return {
        "monthly_outflow": round(monthly_outflow, 2),
        "fund_3m": round(fund_3m, 2),
        "fund_6m": round(fund_6m, 2),
        "fund_12m": round(fund_12m, 2),
        "recommended": round(recommended, 2),
        "current_reserve": round(current_reserve, 2),
        "gap": round(max(0.0, gap), 2),
        "advice": advice
    }

def calculate_health_score(principal, annual_rate, tenure_months, emi, income, 
                            expenses, current_reserve, extra_monthly, loan_type):
    """
    Computes a loan health score (0-100) based on weighted factors:
    - Interest rate burden relative to benchmark (25%)
    - EMI burden (EMI-to-Income) (25%)
    - Emergency savings buffer (20%)
    - Tenure length risk (15%)
    - Active prepayment allocation (15%)
    """
    score = 100.0
    deductions = []
    
    benchmarks = {
        "Home Loan": 8.0,
        "Car Loan": 9.0,
        "Bike Loan": 10.0,
        "Education Loan": 9.0,
        "Personal Loan": 11.5,
        "Business Loan": 10.5,
        "Gold Loan": 8.5,
        "Custom Loan": 9.5
    }
    
    benchmark = benchmarks.get(loan_type, 9.5)
    rate_diff = annual_rate - benchmark
    if rate_diff > 0:
        penalty = min(25.0, rate_diff * 4)
        score -= penalty
        deductions.append(f"Interest rate of {annual_rate}% is above benchmark for {loan_type} ({benchmark}%). (-{round(penalty, 1)} pts)")
        
    ratio = (emi / income * 100.0) if income > 0 else 100.0
    if ratio >= 50.0:
        score -= 25.0
        deductions.append(f"Critical: EMI consumes {round(ratio, 1)}% of monthly income. (-25 pts)")
    elif ratio >= 40.0:
        score -= 20.0
        deductions.append(f"High risk: EMI consumes {round(ratio, 1)}% of income. (-20 pts)")
    elif ratio >= 30.0:
        score -= 12.0
        deductions.append(f"Moderate risk: EMI consumes {round(ratio, 1)}% of income. (-12 pts)")
    elif ratio >= 20.0:
        score -= 5.0
        deductions.append(f"Low risk: EMI consumes {round(ratio, 1)}% of income. (-5 pts)")
        
    monthly_outflow = expenses + emi
    recommended_reserve = monthly_outflow * 6
    if recommended_reserve > 0:
        coverage = current_reserve / recommended_reserve
        if coverage < 0.2:
            score -= 20.0
            deductions.append("Critical: Emergency fund covers under 20% of required buffer. (-20 pts)")
        elif coverage < 0.5:
            score -= 15.0
            deductions.append("Warning: Emergency fund covers under 50% of required buffer. (-15 pts)")
        elif coverage < 1.0:
            score -= 8.0
            deductions.append("Moderate: Emergency fund is below the recommended 6-month buffer. (-8 pts)")
            
    if tenure_months > 240:
        score -= 15.0
        deductions.append(f"High tenure of {tenure_months} months increases compound interest paid. (-15 pts)")
    elif tenure_months > 120:
        score -= 8.0
        deductions.append(f"Moderate tenure of {tenure_months} months. (-8 pts)")
        
    if extra_monthly <= 0:
        score -= 15.0
        deductions.append("No active monthly prepayment budget allocated. (-15 pts)")
    elif extra_monthly < emi * 0.05:
        score -= 8.0
        deductions.append("Low monthly prepayment buffer relative to loan size. (-8 pts)")
        
    score = max(0.0, min(100.0, score))
    
    if score >= 90.0:
        status = "Excellent"
    elif score >= 75.0:
        status = "Good"
    elif score >= 60.0:
        status = "Average"
    elif score >= 40.0:
        status = "Poor"
    else:
        status = "Danger"
        
    return round(score, 0), status, deductions

def simulate_what_if_analysis(principal, annual_rate, tenure_months, income, expenses, current_reserve,
                               extra_monthly, risk_appetite, investments, inflation, age, retirement_age, salary_growth):
    """
    Simulates advanced what-if events and calculates their financial impact:
    - Higher Salary (+ salary_growth% income -> increases extra monthly budget)
    - Lower Salary (-15% income -> decreases extra budget)
    - Job Loss (Income = 0 for 6 months -> emergency fund drains)
    - Interest Rate Increase (+2% interest rate)
    - Interest Rate Decrease (-2% interest rate)
    - Marriage / Family Expansion (+30% expenses -> decreases extra budget)
    - Prepay vs Invest: Compares prepaying with extra_monthly vs compounding it in investments.
    """
    base = calculate_base_loan_details(principal, annual_rate, tenure_months)
    base_emi = base["emi"]
    
    # 1. Higher Salary using actual user expected salary growth
    growth_factor = 1.0 + (salary_growth / 100.0)
    new_inc_high = income * growth_factor
    added_budget = new_inc_high - income
    new_extra_monthly_high = extra_monthly + added_budget
    sim_high_sal = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=new_extra_monthly_high)
    high_sal_interest = sum(m["interest"] for m in sim_high_sal)
    high_sal_months = len(sim_high_sal)
    
    # 2. Lower Salary (-15%)
    new_inc_low = income * 0.85
    subtracted_budget = income - new_inc_low
    new_extra_monthly_low = max(0.0, extra_monthly - subtracted_budget)
    sim_low_sal = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=new_extra_monthly_low)
    low_sal_interest = sum(m["interest"] for m in sim_low_sal)
    low_sal_months = len(sim_low_sal)
    
    # 3. Job Loss
    monthly_outflow = expenses + base_emi
    cost_for_6_months = monthly_outflow * 6.0
    
    # 4. Interest Rate Increase (+2%)
    sim_rate_high = calculate_base_loan_details(principal, annual_rate + 2.0, tenure_months)
    
    # 5. Interest Rate Decrease (-2%)
    sim_rate_low = calculate_base_loan_details(principal, max(1.0, annual_rate - 2.0), tenure_months)
    
    # 6. Marriage (+30% expenses)
    new_exp_family = expenses * 1.30
    family_extra_budget = max(0.0, extra_monthly - (new_exp_family - expenses))
    sim_family = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=family_extra_budget)
    family_interest = sum(m["interest"] for m in sim_family)
    family_months = len(sim_family)
    
    # 7. Prepay vs Invest
    expected_returns = {
        "Conservative": 7.0,
        "Moderate": 10.0,
        "Aggressive": 13.0
    }
    return_rate = expected_returns.get(risk_appetite, 10.0)
    
    # Prepay loan simulation with extra_monthly
    prepay_sim = simulate_amortization(principal, annual_rate, tenure_months, extra_monthly=extra_monthly)
    prepay_interest_paid = sum(m["interest"] for m in prepay_sim)
    prepay_months = len(prepay_sim)
    
    # Compound investment simulation with inflation adjustment
    real_return_rate = return_rate - inflation
    r_inv_real = (max(1.0, real_return_rate) / 12.0) / 100.0
    total_months_to_compare = base["actual_tenure_months"]
    
    invested_value = 0.0
    total_invested_capital = 0.0
    for _ in range(total_months_to_compare):
        invested_value = (invested_value + extra_monthly) * (1.0 + r_inv_real)
        total_invested_capital += extra_monthly
        
    investment_profit = invested_value - total_invested_capital
    interest_saved_by_prepaying = base["total_interest"] - prepay_interest_paid
    
    full_investment_value = 0.0
    if prepay_months < total_months_to_compare:
        months_freed = total_months_to_compare - prepay_months
        for _ in range(months_freed):
            full_investment_value = (full_investment_value + base_emi + extra_monthly) * (1.0 + r_inv_real)
            
    total_value_prepay_strategy = invested_value + interest_saved_by_prepaying if prepay_months >= total_months_to_compare else full_investment_value + interest_saved_by_prepaying
    
    if return_rate > annual_rate:
        prepay_vs_invest_advice = f"Investing extra funds yields an expected {return_rate}% return ({real_return_rate:.1f}% inflation-adjusted), outperforming your {annual_rate}% loan rate. However, prepaying guarantees a risk-free savings equivalent to {annual_rate}% interest, shaving off {round((base['actual_tenure_months']-prepay_months)/12, 1)} years."
    else:
        prepay_vs_invest_advice = f"Prepaying your {annual_rate}% loan guarantees a higher savings than the expected {return_rate}% return from investments. Pay off the loan first."
        
    return {
        "higher_salary": {
            "new_tenure_months": high_sal_months,
            "interest_saved": round(base["total_interest"] - high_sal_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - high_sal_months) / 12.0, 1)
        },
        "lower_salary": {
            "new_tenure_months": low_sal_months,
            "interest_saved": round(base["total_interest"] - low_sal_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - low_sal_months) / 12.0, 1)
        },
        "job_loss": {
            "outflow_6m": round(cost_for_6_months, 2),
            "has_enough_reserve": current_reserve >= cost_for_6_months
        },
        "rate_increase": {
            "new_emi": sim_rate_high["emi"],
            "total_interest": sim_rate_high["total_interest"],
            "interest_difference": round(sim_rate_high["total_interest"] - base["total_interest"], 2)
        },
        "rate_decrease": {
            "new_emi": sim_rate_low["emi"],
            "total_interest": sim_rate_low["total_interest"],
            "interest_difference": round(sim_rate_low["total_interest"] - base["total_interest"], 2)
        },
        "family_expansion": {
            "new_tenure_months": family_months,
            "interest_saved": round(base["total_interest"] - family_interest, 2),
            "years_saved": round((base["actual_tenure_months"] - family_months) / 12.0, 1)
        },
        "prepay_vs_invest": {
            "investment_return_rate": return_rate,
            "investment_value": round(invested_value, 2),
            "investment_profit": round(investment_profit, 2),
            "interest_saved_prepay": round(interest_saved_by_prepaying, 2),
            "prepay_years_saved": round((base["actual_tenure_months"] - prepay_months) / 12.0, 1),
            "prepay_strategy_value": round(total_value_prepay_strategy, 2),
            "advice": prepay_vs_invest_advice
        }
    }

def get_loan_specific_features(loan_type, principal, annual_rate, tenure_months, base_emi):
    """
    Returns custom calculators, tips, and guidelines per loan type.
    """
    results = {}
    
    if loan_type == "Home Loan":
        results["advice"] = "💡 **Tax Benefits (e.g., Section 24b / 80C):** Deduct up to ₹2L on interest and ₹1.5L on principal. Consider refinancing or balance transfer if current market rates are >0.5% lower."
        special_sim = simulate_amortization(principal, annual_rate, tenure_months, annual_prepayment=base_emi)
        base = calculate_base_loan_details(principal, annual_rate, tenure_months)
        new_tenure = len(special_sim)
        interest_saved = base["total_interest"] - sum(m["interest"] for m in special_sim)
        years_saved = (base["actual_tenure_months"] - new_tenure) / 12.0
        
        results["extra_emi_effect"] = {
            "new_tenure_months": new_tenure,
            "interest_saved": round(interest_saved, 2),
            "years_saved": round(years_saved, 1)
        }
        
    elif loan_type == "Car Loan":
        car_val = principal
        value_timeline = []
        years = int(math.ceil(tenure_months / 12.0))
        for year in range(1, years + 1):
            car_val = car_val * 0.85
            value_timeline.append((year, round(car_val, 2)))
        results["depreciation_timeline"] = value_timeline
        results["advice"] = "⚠️ **Depreciation Risk:** Vehicles lose ~15% value annually. Ensure your remaining principal stays below the vehicle value to avoid negative equity."
        
    elif loan_type == "Bike Loan":
        results["advice"] = "⚡ **Fast Payoff Strategy:** Bike loans usually carry double-digit interest. Adding ₹1,000 monthly or making small prepayment bursts pays off the loan in half the time."
        
    elif loan_type == "Education Loan":
        results["advice"] = "🎓 **Moratorium Optimization:** Education loans feature moratorium periods (studies + grace). Paying off accruing interest monthly during college avoids capitalization into the principal."
        
    elif loan_type == "Personal Loan":
        results["advice"] = "🚨 **Consolidation Alert:** Personal loans have interest rates ranging from 12% to 24%. Consolidating multiple lines into a single lower-interest asset-backed loan is highly recommended."
        
    elif loan_type == "Business Loan":
        results["advice"] = "📈 **ROI Evaluation:** Ensure business returns (operating ROI) exceed the loan cost. If loan interest is 11% and business capital ROI is 15%, reinvesting profits is more lucrative than prepaying."
        
    elif loan_type == "Gold Loan":
        results["advice"] = "🪙 **LTV Margin Call Risk:** Gold loans are quick but tied to gold prices. A steep drop in gold market prices will trigger a Margin Call, requiring immediate principal paydowns."
        
    else:
        results["advice"] = "💡 Custom loan parameters. Review prepayment clauses and interest-saving options periodically."
        
    return results

def get_financial_milestones(age, retirement_age, current_tenure_months, optimized_tenure_months):
    """
    Computes milestones for loan duration.
    """
    current_tenure_years = current_tenure_months / 12.0
    optimized_tenure_years = optimized_tenure_months / 12.0
    
    loan_end_age = age + current_tenure_years
    debt_free_age = age + optimized_tenure_years
    
    retirement_gap_base = retirement_age - loan_end_age
    retirement_gap_opt = retirement_age - debt_free_age
    
    if debt_free_age < retirement_age:
        advice = f"Fantastic! You will be debt-free at age {round(debt_free_age, 1)}, which is {round(retirement_gap_opt, 1)} years before retirement. This gives you extra time to build investments."
    else:
        advice = f"Warning: Your debt timeline extends to age {round(debt_free_age, 1)}, which is past retirement ({retirement_age}). We recommend optimizing your schedule to finish earlier."
        
    return {
        "current_age": age,
        "loan_end_age": round(loan_end_age, 1),
        "debt_free_age": round(debt_free_age, 1),
        "retirement_gap_base": round(retirement_gap_base, 1),
        "retirement_gap_opt": round(retirement_gap_opt, 1),
        "advice": advice
    }

def generate_smart_alerts(principal, annual_rate, tenure_months, emi, income, expenses, current_reserve):
    """
    Finds critical risk points and outputs alerts.
    """
    alerts = []
    
    ratio = (emi / income * 100.0) if income > 0 else 100.0
    if ratio > 40.0:
        alerts.append({
            "type": "danger",
            "message": f"Debt ratio warning: Your EMI consumes {round(ratio, 1)}% of net monthly income (Recommended limit: <30%)."
        })
        
    monthly_outflow = expenses + emi
    six_month_fund = monthly_outflow * 6.0
    if current_reserve < six_month_fund:
        alerts.append({
            "type": "warning",
            "message": f"Emergency fund alert: Your reserve of {current_reserve:,.0f} is below the 6-month safety buffer of {six_month_fund:,.0f}."
        })
        
    if annual_rate > 11.5:
        alerts.append({
            "type": "warning",
            "message": f"High interest rate alert: {annual_rate}% is high. Consider refinancing or balance transfer."
        })
        
    if tenure_months > 180:
        alerts.append({
            "type": "info",
            "message": f"Long loan tenure alert: {tenure_months} months means substantial interest accrual. Prepayments will yield huge savings."
        })
        
    if current_reserve > six_month_fund * 1.5:
        alerts.append({
            "type": "success",
            "message": "Good prepayment opportunity: You have excess emergency reserves. You can safely execute a lump-sum payment."
        })
        
    return alerts
