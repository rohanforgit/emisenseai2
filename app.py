import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
import io
import os

# Load API Key and Provider from environment or local .env file
DEFAULT_PROVIDER = "Gemini (Free)"
DEFAULT_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""

if os.path.exists(".env"):
    try:
        with open(".env", "r") as f:
            content = f.read().strip()
            if "=" in content:
                for line in content.split("\n"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "GEMINI_API_KEY" or k == "GEMINI_KEY":
                            DEFAULT_KEY = v
                            DEFAULT_PROVIDER = "Gemini (Free)"
                            break
                        elif k == "OPENAI_API_KEY":
                            DEFAULT_KEY = v
                            DEFAULT_PROVIDER = "OpenAI (Paid)"
                if not DEFAULT_KEY:
                    parts = content.split("=", 1)
                    val = parts[1].strip().strip('"').strip("'")
                    DEFAULT_KEY = val
                    if val.startswith("AIzaSy") or val.startswith("AQ."):
                        DEFAULT_PROVIDER = "Gemini (Free)"
                    else:
                        DEFAULT_PROVIDER = "OpenAI (Paid)"
            else:
                DEFAULT_KEY = content
                if content.startswith("AIzaSy") or content.startswith("AQ."):
                    DEFAULT_PROVIDER = "Gemini (Free)"
                else:
                    DEFAULT_PROVIDER = "OpenAI (Paid)"
    except Exception:
        pass

if DEFAULT_KEY.startswith("AIzaSy") or DEFAULT_KEY.startswith("AQ."):
    DEFAULT_PROVIDER = "Gemini (Free)"
elif DEFAULT_KEY.startswith("sk-"):
    DEFAULT_PROVIDER = "OpenAI (Paid)"

# Import modular libraries
import calculations as calc
import charts
import ai_engine as ai
import pdf_generator as pdf

# 1. Page Configuration Setup
st.set_page_config(
    page_title="EMI Sense AI - Loan Optimization Platform",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Premium Fintech Dark CSS
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    
    /* Card Layouts */
    .fintech-card {
        background-color: #1E293B;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .fintech-card:hover {
        transform: translateY(-2px);
        border-color: #3B82F6;
    }
    
    .kpi-title {
        color: #94A3B8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    /* Metrics Deltas Overrides */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Rounded alert cards */
    .alert-card {
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 5px solid;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    .alert-danger {
        background-color: rgba(239, 68, 68, 0.1);
        border-left-color: #EF4444;
        color: #FCA5A5;
    }
    .alert-warning {
        background-color: rgba(245, 158, 11, 0.1);
        border-left-color: #F59E0B;
        color: #FDE047;
    }
    .alert-info {
        background-color: rgba(59, 130, 246, 0.1);
        border-left-color: #3B82F6;
        color: #93C5FD;
    }
    .alert-success {
        background-color: rgba(16, 185, 129, 0.1);
        border-left-color: #10B981;
        color: #6EE7B7;
    }
    
    /* Optimization Savings Highlight */
    .savings-gold {
        color: #EAB308;
        font-weight: 700;
    }
    
    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0F172A;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3B82F6;
    }
    
    /* Chat bubbles styling */
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 10px;
        max-width: 85%;
        line-height: 1.5;
    }
    .chat-user {
        background-color: #3B82F6;
        color: #FFFFFF;
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }
    .chat-assistant {
        background-color: #1E293B;
        color: #F8FAFC;
        border: 1px solid #334155;
        margin-right: auto;
        border-bottom-left-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "compare_loans" not in st.session_state:
    st.session_state.compare_loans = False

# Sidebar Header & Logo
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <h1 style="color: #3B82F6; font-size: 2.2rem; font-weight: 800; margin: 0; display: inline-flex; align-items: center; gap: 8px;">
        💡 EMI Sense AI
    </h1>
    <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 5px;">AI Loan Optimization Platform</p>
</div>
<hr style="border-color: #1E293B; margin-bottom: 20px;"/>
""", unsafe_allow_html=True)

# SIDEBAR: AI Configuration
st.sidebar.subheader("🤖 AI Advisor Config")
ai_provider = st.sidebar.selectbox("AI Provider", ["Gemini (Free)", "OpenAI (Paid)"], index=0 if DEFAULT_PROVIDER == "Gemini (Free)" else 1)
ai_api_key = st.sidebar.text_input("AI API Key", value=DEFAULT_KEY, type="password", help="Enter your Gemini or OpenAI API key. Leave blank for rule-based local advisor.")

# Dynamic model selection based on provider
if ai_provider == "Gemini (Free)":
    ai_model = st.sidebar.selectbox("AI Model", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"], index=0)
else:
    ai_model = st.sidebar.selectbox("AI Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)

st.sidebar.markdown("---")

# SIDEBAR: Base Customization
st.sidebar.subheader("⚙️ Global Settings")
currency = st.sidebar.selectbox("Currency Unit", ["₹", "$", "€", "£", "¥", "₱"], index=0)
compare_mode = st.sidebar.checkbox("Compare Loan Architectures", value=False, help="Toggle Loan Comparison Mode to compare two distinct structures side-by-side.")

st.sidebar.markdown("---")

# SIDEBAR: Session Controls
st.sidebar.subheader("💾 Control Center")
if st.sidebar.button("🔄 Reset System Session", use_container_width=True):
    st.session_state.chat_history = []
    st.toast("Dashboard reset back to base configuration.")
    st.rerun()

# --- SIDE-BY-SIDE COMPARISON MODAL OR SECTION ---
if compare_mode:
    st.title("👥 Loan Comparison Mode")
    st.markdown("Use this panel to run a side-by-side comparison of two distinct loan setups to choose the winner.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 🏛️ Loan Option A")
        comp_type_a = st.selectbox("Loan A Classification", ["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], index=0)
        comp_amt_a = st.number_input("Loan A Amount", value=5000000.0, step=50000.0)
        comp_rate_a = st.slider("Loan A Annual Rate (%)", min_value=1.0, max_value=30.0, value=8.5, step=0.1)
        comp_tenure_a = st.slider("Loan A Tenure (Months)", min_value=12, max_value=480, value=240, step=12)
        
    with col_b:
        st.markdown("### 🏛️ Loan Option B")
        comp_type_b = st.selectbox("Loan B Classification", ["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], index=1)
        comp_amt_b = st.number_input("Loan B Amount", value=5000000.0, step=50000.0)
        comp_rate_b = st.slider("Loan B Annual Rate (%)", min_value=1.0, max_value=30.0, value=7.5, step=0.1)
        comp_tenure_b = st.slider("Loan B Tenure (Months)", min_value=12, max_value=480, value=180, step=12)
        
    details_a = calc.calculate_base_loan_details(comp_amt_a, comp_rate_a, comp_tenure_a)
    details_b = calc.calculate_base_loan_details(comp_amt_b, comp_rate_b, comp_tenure_b)
    
    # Render Comparison Cards
    st.markdown("---")
    st.subheader("📊 side-by-side Parameters")
    
    grid_a, grid_b, grid_c = st.columns(3)
    
    with grid_a:
        st.markdown(f"""
        <div class="fintech-card">
            <div class="kpi-title">Monthly EMI</div>
            <div style="font-size: 1.3rem; font-weight: 700;">Option A: {currency}{details_a['emi']:,.2f}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #10B981;">Option B: {currency}{details_b['emi']:,.2f}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 8px;">Difference: {currency}{abs(details_a['emi'] - details_b['emi']):,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with grid_b:
        st.markdown(f"""
        <div class="fintech-card">
            <div class="kpi-title">Total Interest Payable</div>
            <div style="font-size: 1.3rem; font-weight: 700;">Option A: {currency}{details_a['total_interest']:,.2f}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #10B981;">Option B: {currency}{details_b['total_interest']:,.2f}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 8px;">Difference: {currency}{abs(details_a['total_interest'] - details_b['total_interest']):,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with grid_c:
        st.markdown(f"""
        <div class="fintech-card">
            <div class="kpi-title">Total Paid Amount</div>
            <div style="font-size: 1.3rem; font-weight: 700;">Option A: {currency}{details_a['total_payment']:,.2f}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #10B981;">Option B: {currency}{details_b['total_payment']:,.2f}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 8px;">Difference: {currency}{abs(details_a['total_payment'] - details_b['total_payment']):,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Declare the winner
    if details_a['total_payment'] < details_b['total_payment']:
        winner = "Loan Option A"
        diff_val = details_b['total_payment'] - details_a['total_payment']
    else:
        winner = "Loan Option B"
        diff_val = details_a['total_payment'] - details_b['total_payment']
        
    st.markdown(f"""
    <div class="alert-card alert-success">
        🏆 <b>Financial Winner:</b> <b>{winner}</b> is the cheaper structure overall, saving you <b>{currency}{diff_val:,.2f}</b> in total payments compared to the other option!
    </div>
    """, unsafe_allow_html=True)
    
    # Amortization Outstanding comparison chart
    st.markdown("### 📈 Remaining Principal Timeline Comparison")
    fig_comp = charts.generate_principal_remaining_chart(details_a['schedule'], details_b['schedule'], "Option B", currency)
    st.plotly_chart(fig_comp, use_container_width=True)
    
else:
    # --- PRIMARY MAIN DASHBOARD MODE ---
    st.title("💡 EMI Sense AI – AI Powered Loan Optimization Platform")
    st.markdown("Traditional calculators tell you your EMI. We help you optimize your debt, save interest, and become debt-free faster.")
    st.markdown("---")
    
    # --- INPUT SECTION GRID (CARD STYLE CONTAINER) ---
    with st.container():
        st.subheader("📥 Financial Inputs & Profile Setup")
        
        in_col1, in_col2, in_col3 = st.columns(3)
        
        with in_col1:
            st.markdown("<h4 style='color: #3B82F6; margin-bottom: 10px;'>🏛️ Loan Setup</h4>", unsafe_allow_html=True)
            loan_type = st.selectbox("Loan Classification", ["Home Loan", "Car Loan", "Bike Loan", "Education Loan", "Personal Loan", "Business Loan", "Gold Loan", "Custom Loan"], index=0)
            loan_amount = st.number_input("Loan Principal Amount", min_value=1000.0, value=5000000.0, step=50000.0)
            interest_rate = st.slider("Interest Rate (% Annual)", min_value=0.5, max_value=30.0, value=8.5, step=0.1)
            loan_tenure_months = st.slider("Loan Tenure (Months)", min_value=12, max_value=480, value=240, step=12)
            
        with in_col2:
            st.markdown("<h4 style='color: #10B981; margin-bottom: 10px;'>💵 Financial Profile</h4>", unsafe_allow_html=True)
            monthly_income = st.number_input("Monthly Net Income", min_value=1000.0, value=150000.0, step=5000.0)
            monthly_expenses = st.number_input("Monthly Living Expenses", min_value=0.0, value=50000.0, step=2000.0)
            current_savings = st.number_input("Current Cash Savings", min_value=0.0, value=500000.0, step=10000.0)
            current_investments = st.number_input("Current Investment Portfolio", min_value=0.0, value=1000000.0, step=50000.0)
            emergency_fund = st.number_input("Liquid Emergency Reserves", min_value=0.0, value=300000.0, step=10000.0)
            
        with in_col3:
            st.markdown("<h4 style='color: #EAB308; margin-bottom: 10px;'>⚡ Optimization Targets</h4>", unsafe_allow_html=True)
            extra_monthly_budget = st.number_input("Extra Monthly EMI Budget", min_value=0.0, value=15000.0, step=1000.0)
            annual_bonus = st.number_input("Expected Annual Bonus", min_value=0.0, value=100000.0, step=5000.0)
            current_age = st.slider("Your Current Age", min_value=18, max_value=85, value=30)
            retirement_age = st.slider("Target Retirement Age", min_value=40, max_value=90, value=60)
            expected_salary_growth = st.slider("Expected Yearly Salary Growth (%)", min_value=0, max_value=40, value=8)
            expected_inflation = st.slider("Expected Annual Inflation (%)", min_value=0, max_value=20, value=6)
            risk_appetite = st.selectbox("Portfolio Risk Profile", ["Conservative", "Moderate", "Aggressive"], index=1)
            
    # --- AUTOMATIC CALCULATIONS & AMORTIZATIONS ---
    base = calc.calculate_base_loan_details(loan_amount, interest_rate, loan_tenure_months)
    
    # Standard simulations
    sim_emi = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, 10.0) # default 10% emi bump
    sim_annual = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, annual_bonus * 0.5) # assume 50% of bonus goes to prepayment
    sim_lump = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, current_savings * 0.2, mode="reduce_tenure") # assume 20% savings goes to lump sum
    
    # Combined strategy (extra monthly + 50% annual bonus + 20% savings lump sum at month 1)
    combined_sim = calc.simulate_amortization(
        loan_amount, interest_rate, loan_tenure_months,
        extra_monthly=extra_monthly_budget,
        annual_prepayment=annual_bonus * 0.5,
        lump_sum=current_savings * 0.2,
        lump_sum_month=1
    )
    
    combined_interest = sum(m["interest"] for m in combined_sim)
    combined_savings = base["total_interest"] - combined_interest
    combined_tenure = len(combined_sim)
    
    # Refinance parameters
    refinance_rate = interest_rate - 0.75  # Target rate typical refinancing discount
    refinance_cost = loan_amount * 0.005  # Assume 0.5% transfer charges
    refinance = calc.calculate_refinancing(loan_amount, interest_rate, loan_tenure_months, refinance_rate, refinance_cost)
    
    # Risk and Runway details
    emi_ratio, emi_status, emi_advice = calc.calculate_emi_to_income(base["emi"], monthly_income)
    em_fund = calc.calculate_emergency_fund(monthly_expenses, base["emi"], emergency_fund)
    
    # Health Score
    score, status, deductions = calc.calculate_health_score(
        loan_amount, interest_rate, loan_tenure_months, base["emi"],
        monthly_income, monthly_expenses, emergency_fund, extra_monthly_budget, loan_type
    )
    
    # Alerts
    alerts = calc.generate_smart_alerts(loan_amount, interest_rate, loan_tenure_months, base["emi"], monthly_income, monthly_expenses, emergency_fund)
    
    # Milestones
    milestones = calc.get_financial_milestones(current_age, retirement_age, loan_tenure_months, combined_tenure)
    
    # Loan specific features
    specifics = calc.get_loan_specific_features(loan_type, loan_amount, interest_rate, loan_tenure_months, base["emi"])
    
    # Save parameter bundle for LLM
    loan_data = {
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "loan_tenure_months": loan_tenure_months,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "extra_monthly_budget": extra_monthly_budget,
        "annual_prepayment": annual_bonus * 0.5,
        "lump_sum_amount": current_savings * 0.2,
        "emi_increase_pct": 10.0,
        "refinance_rate": refinance_rate,
        "refinance_cost": refinance_cost,
        "refinance_net_savings": refinance.get("net_savings", 0),
        "currency": currency,
        "emi_ratio": emi_ratio,
        "emergency_savings": emergency_fund,
        "risk_appetite": risk_appetite,
        "loan_type": loan_type,
        "home_loan_special_savings": specifics.get("extra_emi_effect", {}).get("interest_saved", 0.0) if loan_type == "Home Loan" else 0.0,
        "home_loan_special_years": specifics.get("extra_emi_effect", {}).get("years_saved", 0.0) if loan_type == "Home Loan" else 0.0,
        "depreciation_text": str(specifics.get("depreciation_timeline", "N/A")) if loan_type == "Car Loan" else "N/A"
    }
    
    # --- EXECUTIVE AI ADVICE OR RULE-BASED ADVICE BLOCK ---
    @st.cache_data
    def fetch_ai_recommendations(loan_bundle, base_details, sim_emi, sim_annual, sim_lump, refinance, score, status, deductions, provider, api_key, model_name):
        return ai.get_ai_recommendations(
            loan_bundle, base_details, sim_emi, sim_annual, sim_lump, refinance,
            score, status, deductions, provider, api_key, model_name
        )
        
    ai_advice = fetch_ai_recommendations(
        loan_data, base, sim_emi, sim_annual, sim_lump, refinance,
        score, status, deductions, ai_provider, ai_api_key, ai_model
    )
    
    # --- TOP MAIN DASHBOARD METRICS ---
    st.markdown("---")
    st.subheader("📊 Advisor Dashboard Overview")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    
    with kpi_col1:
        st.metric("Monthly EMI", f"{currency}{base['emi']:,.2f}", delta=None, help="Base monthly loan EMI.")
    with kpi_col2:
        st.metric("Total Interest", f"{currency}{base['total_interest']:,.2f}", delta=None, help="Cumulative interest payable over tenure.")
    with kpi_col3:
        st.metric("Total Payment", f"{currency}{base['total_payment']:,.2f}", delta=None, help="Sum of principal and interest costs.")
    with kpi_col4:
        st.metric("Potential Savings", f"{currency}{combined_savings:,.2f}", delta=f"{currency}{combined_savings:,.0f} saved", delta_color="normal", help="Total interest saved by running the combined prepayment plan.")
    with kpi_col5:
        st.metric("Loan Health Score", f"{score:.0f}/100", delta=status, delta_color="off" if status in ["Poor", "Danger"] else "normal", help="Weighted financial health score.")
    with kpi_col6:
        opt_months_delta = base["actual_tenure_months"] - combined_tenure
        st.metric("Years to Debt Free", f"{combined_tenure/12.0:.1f} Yrs", delta=f"-{opt_months_delta/12.0:.1f} Yrs", delta_color="inverse", help="Optimized time required to fully clear the debt.")
        
    # --- MAIN CORE TABS ---
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Loan Summary", 
        "⚡ Optimization", 
        "🔍 What If Analysis", 
        "📈 Interactive Charts", 
        "🛡️ Loan Health", 
        "💬 AI Coach", 
        "📄 Export Report"
    ])
    
    # TAB 1: LOAN SUMMARY
    with tab1:
        st.subheader("🏛️ Baseline Loan Breakdown & Strategy")
        
        sum_col1, sum_col2 = st.columns([1, 1.5])
        
        with sum_col1:
            st.markdown(f"""
            <div class="fintech-card">
                <h4 style="color:#3B82F6;margin-top:0;">Base Loan Details</h4>
                <table style="width:100%; border-collapse: collapse;">
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Loan Type</td><td style="text-align:right;font-weight:600;">{loan_type}</td></tr>
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Base Monthly EMI</td><td style="text-align:right;font-weight:600;color:#3B82F6;">{currency}{base['emi']:,.2f}</td></tr>
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Total Principal</td><td style="text-align:right;font-weight:600;">{currency}{loan_amount:,.2f}</td></tr>
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Interest Payable</td><td style="text-align:right;font-weight:600;color:#EF4444;">{currency}{base['total_interest']:,.2f}</td></tr>
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Interest Ratio</td><td style="text-align:right;font-weight:600;color:#EAB308;">{base['interest_percentage']}% of total</td></tr>
                    <tr style="border-bottom:1px solid #334155;"><td style="padding:8px 0;color:#94A3B8;">Baseline Duration</td><td style="text-align:right;font-weight:600;">{round(loan_tenure_months/12.0, 1)} years</td></tr>
                    <tr><td style="padding:8px 0;color:#94A3B8;">Baseline Payoff Date</td><td style="text-align:right;font-weight:600;color:#10B981;">{base['debt_free_date'].strftime('%b %Y')}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            # Smart Alerts box
            st.markdown("#### 🚨 Smart Health Alerts")
            if alerts:
                for a in alerts:
                    theme_class = f"alert-{a['type']}"
                    icon = "🚨" if a["type"] == "danger" else "⚠️" if a["type"] == "warning" else "✅" if a["type"] == "success" else "💡"
                    st.markdown(f"""
                    <div class="alert-card {theme_class}">
                        <b>{icon} Alert:</b> {a['message']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="alert-card alert-success">
                    ✅ <b>Financial Checklist Clear:</b> No high-risk items found on your loan parameters.
                </div>
                """, unsafe_allow_html=True)
                
        with sum_col2:
            st.markdown("#### 🏆 Top Actions & Recommendations")
            st.markdown(ai_advice)
            
            # Top 3 Actions summary block rendered locally for extra premium visuals
            st.markdown("---")
            st.markdown("### ⚡ Ranked Action Steps by Interest Savings")
            actions_list = []
            if sim_emi["interest_saved"] > 0:
                actions_list.append(("Increase EMI by 10%", sim_emi["interest_saved"], f"Bumps your monthly EMI, saving {currency}{sim_emi['interest_saved']:,.2f} in interest and finishing {sim_emi['years_saved']} years early."))
            if sim_annual["interest_saved"] > 0:
                actions_list.append((f"Yearly Prepay of {currency}{(annual_bonus * 0.5):,.0f}", sim_annual["interest_saved"], f"Apply 50% of annual bonus to prepayment, saving {currency}{sim_annual['interest_saved']:,.2f}."))
            if sim_lump["interest_saved"] > 0:
                actions_list.append((f"Lump Sum Prepay of {currency}{(current_savings * 0.2):,.0f}", sim_lump["interest_saved"], f"Deploy 20% savings immediately, saving {currency}{sim_lump['interest_saved']:,.2f} in interest."))
            if refinance.get("worth_refinancing"):
                actions_list.append(("Refinance / Balance Transfer", refinance["net_savings"], f"Refinance target to {refinance_rate}%, saving {currency}{refinance['net_savings']:,.2f} net of costs."))
                
            actions_list = sorted(actions_list, key=lambda x: x[1], reverse=True)
            
            cols_act = st.columns(3)
            for idx, act in enumerate(actions_list[:3]):
                with cols_act[idx]:
                    st.markdown(f"""
                    <div class="fintech-card" style="border-color:#EAB308;">
                        <div style="font-size:0.75rem;color:#EAB308;font-weight:700;text-transform:uppercase;">Rank {idx+1}</div>
                        <div style="font-weight:700;font-size:1.15rem;margin:5px 0;">{act[0]}</div>
                        <div style="font-size:1rem;color:#10B981;font-weight:600;margin-bottom:8px;">Saves {currency}{act[1]:,.2f}</div>
                        <div style="font-size:0.8rem;color:#94A3B8;">{act[2]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
    # TAB 2: OPTIMIZATION
    with tab2:
        st.subheader("⚡ Prepayment & Refinance Simulator")
        st.markdown("Simulate different financial acceleration paths to see how much interest and tenure you can save.")
        
        opt_col1, opt_col2 = st.columns(2)
        
        with opt_col1:
            st.markdown("### 📈 Section A: Increase Monthly EMI")
            emi_pct = st.slider("EMI Increase Percentage", min_value=0, max_value=100, value=10, step=5, help="Increases baseline monthly payment by a fixed percentage.")
            sim_emi_val = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, emi_pct)
            
            st.markdown(f"""
            <div class="fintech-card">
                <b>New Adjusted EMI:</b> {currency}{sim_emi_val['new_emi']:,.2f}<br/>
                <b>Tenure Reduced To:</b> {sim_emi_val['new_tenure_months']} months<br/>
                <span class="savings-gold"><b>Total Interest Saved:</b> {currency}{sim_emi_val['interest_saved']:,.2f}</span><br/>
                <b>Years Trimmed:</b> {sim_emi_val['years_saved']} years
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 💰 Section B: Annual Extra Prepayment")
            ann_prepay = st.number_input("Annual Extra Prepayment Amount", min_value=0.0, value=annual_bonus * 0.5, step=5000.0)
            sim_ann_val = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, ann_prepay)
            
            st.markdown(f"""
            <div class="fintech-card">
                <b>New Optimized Tenure:</b> {sim_ann_val['new_tenure_months']} months<br/>
                <span class="savings-gold"><b>Total Interest Saved:</b> {currency}{sim_ann_val['interest_saved']:,.2f}</span><br/>
                <b>Years Trimmed:</b> {sim_ann_val['years_saved']} years
            </div>
            """, unsafe_allow_html=True)
            
        with opt_col2:
            st.markdown("### 🏦 Section C: One-Time Lump Sum")
            lump_amount = st.number_input("One-Time Prepayment Amount", min_value=0.0, value=current_savings * 0.2, step=5000.0)
            sim_lump_val = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, lump_amount, mode="reduce_tenure")
            
            st.markdown(f"""
            <div class="fintech-card">
                <b>New Optimized Tenure:</b> {sim_lump_val['new_tenure_months']} months<br/>
                <span class="savings-gold"><b>Total Interest Saved:</b> {currency}{sim_lump_val['interest_saved']:,.2f}</span><br/>
                <b>Years Trimmed:</b> {sim_lump_val['years_saved']} years<br/>
                <b>New Principal Balance (immediate):</b> {currency}{sim_lump_val['reduced_principal']:,.2f}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 🔄 Section D & E: Rate Reduction & Refinance")
            tgt_rate = st.slider("Target Interest Rate (%)", min_value=1.0, max_value=30.0, value=interest_rate - 1.0, step=0.1)
            ref_cost_input = st.number_input("Balance Transfer Fees / Costs", min_value=0.0, value=loan_amount * 0.005, step=1000.0)
            
            sim_ref = calc.calculate_refinancing(loan_amount, interest_rate, loan_tenure_months, tgt_rate, ref_cost_input)
            ref_badge = "<span style='color:#10B981;font-weight:700;'>RECOMMENDED</span>" if sim_ref['worth_refinancing'] else "<span style='color:#EF4444;font-weight:700;'>NOT RECOMMENDED</span>"
            
            st.markdown(f"""
            <div class="fintech-card">
                <b>New Refinanced EMI:</b> {currency}{sim_ref['new_emi']:,.2f}<br/>
                <b>Monthly Cash Flow Savings:</b> {currency}{sim_ref['monthly_saving']:,.2f}/mo<br/>
                <span class="savings-gold"><b>Net Lifetime Savings (after costs):</b> {currency}{sim_ref['net_savings']:,.2f}</span><br/>
                <b>Break-Even Point:</b> {sim_ref['break_even_months']} months<br/>
                <b>Refinance Decision:</b> {ref_badge}
            </div>
            """, unsafe_allow_html=True)
            
    # TAB 3: WHAT IF ANALYSIS
    with tab3:
        st.subheader("🔍 What-If Risk Simulations & Asset Allocation")
        st.markdown("Model different financial events to see how cash changes impact your debt schedule.")
        
        event_col, prepay_col = st.columns([1.5, 1])
        
        with event_col:
            st.markdown("### 🌪️ Scenario Matrix Analysis")
            
            # Interactive Sliders for Custom Scenario overrides
            st.markdown("##### Adjust Scenario Parameters")
            over_salary_growth = st.slider("Salary growth scenario override (%)", min_value=0, max_value=50, value=expected_salary_growth)
            over_rate_increase = st.slider("Rate shock (+ %)", min_value=0.0, max_value=10.0, value=2.0, step=0.5)
            
            # Run scenarios using calculations library
            what_if = calc.simulate_what_if_analysis(
                loan_amount, interest_rate, loan_tenure_months, monthly_income, monthly_expenses, emergency_fund,
                extra_monthly_budget, risk_appetite, current_investments, expected_inflation, current_age, retirement_age, over_salary_growth
            )
            
            # Job loss analysis
            jl = what_if["job_loss"]
            jl_status = f"<span style='color:#10B981;font-weight:600;'>SECURE</span>" if jl["has_enough_reserve"] else f"<span style='color:#EF4444;font-weight:600;'>RISKY (Deficit: {currency}{abs(emergency_fund - jl['outflow_6m']):,.2f})</span>"
            
            # Scenario Dataframe
            sc_data = [
                ["Higher Income (Uses salary growth slider)", f"{what_if['higher_salary']['new_tenure_months']} months", f"Saves {currency}{what_if['higher_salary']['interest_saved']:,.2f}", f"+{what_if['higher_salary']['years_saved']} years"],
                ["Lower Income (-15% salary drop)", f"{what_if['lower_salary']['new_tenure_months']} months", f"Cost: -{currency}{abs(what_if['lower_salary']['interest_saved']):,.2f}", f"{what_if['lower_salary']['years_saved']} years"],
                ["Family Expansion (+30% expenses)", f"{what_if['family_expansion']['new_tenure_months']} months", f"Cost: -{currency}{abs(what_if['family_expansion']['interest_saved']):,.2f}", f"{what_if['family_expansion']['years_saved']} years"],
                [f"Interest Rate Jump (+{over_rate_increase}%)", f"{loan_tenure_months} months (fixed)", f"Cost: +{currency}{(calculations := calc.calculate_base_loan_details(loan_amount, interest_rate + over_rate_increase, loan_tenure_months))['total_interest'] - base['total_interest']:,.2f}", "0 (EMI Adjusted)"],
                ["Moratorium / Career Break", " moratorium", "Interest continues compiling during break", "Moratorium analysis"],
            ]
            df_sc = pd.DataFrame(sc_data, columns=["What-If Event Scenario", "Optimized Tenure", "Interest Saved / Extra Cost", "Years Impact"])
            st.dataframe(df_sc, use_container_width=True, hide_index=True)
            
            st.markdown(f"""
            <div class="fintech-card">
                <b>💼 6-Month Job Loss Security Test:</b><br/>
                Required reserve buffer for 6 months EMIs + expenses: <b>{currency}{jl['outflow_6m']:,.2f}</b><br/>
                Current emergency reserves: <b>{currency}{emergency_fund:,.2f}</b><br/>
                Reserves classification: {jl_status}
            </div>
            """, unsafe_allow_html=True)
            
        with prepay_col:
            st.markdown("### ⚖️ Prepay Debt vs. Invest Capital")
            st.markdown("Compare compounding excess monthly budget in standard investment portfolios vs. paying off loan principal.")
            
            p_vs_i = what_if["prepay_vs_invest"]
            st.markdown(f"""
            <div class="fintech-card">
                <h5 style="color:#EAB308;margin-top:0;">Option A: Prepay Loan (Guaranteed Return)</h5>
                Loan rate: <b>{interest_rate}% guaranteed tax-free return</b><br/>
                Lifetime interest savings: <b>{currency}{p_vs_i['interest_saved_prepay']:,.2f}</b><br/>
                Debt-free target: <b>{p_vs_i['prepay_years_saved']} years faster</b>
            </div>
            
            <div class="fintech-card">
                <h5 style="color:#3B82F6;margin-top:0;">Option B: Invest Capital ({risk_appetite} Profile)</h5>
                Expected return rate: <b>{p_vs_i['investment_return_rate']}% annual ({p_vs_i['investment_return_rate'] - expected_inflation:.1f}% real rate)</b><br/>
                Total compounded value: <b>{currency}{p_vs_i['investment_value']:,.2f}</b><br/>
                Net investment profit: <b>{currency}{p_vs_i['investment_profit']:,.2f}</b>
            </div>
            
            <div class="alert-card alert-info">
                ℹ️ <b>Comparison Summary:</b><br/>
                Prepay strategy total net value (including compound reinvestment of freed EMI): <b>{currency}{p_vs_i['prepay_strategy_value']:,.2f}</b><br/>
                <b>Advisor Advice:</b> {p_vs_i['advice']}
            </div>
            """, unsafe_allow_html=True)
            
    # TAB 4: CHARTS
    with tab4:
        st.subheader("📈 Interactive Schedules & Timeline Analytics")
        st.markdown("Visualise and analyze balance tracks, interest accruals, and scenario payoffs.")
        
        c_sub1, c_sub2, c_sub3 = st.tabs(["📊 Debt Composition", "🗓️ Remaining Balance & Cash Flows", "⚡ Prepayment Scenarios Comparison"])
        
        with c_sub1:
            st.plotly_chart(charts.generate_emi_breakdown_chart(loan_amount, base["total_interest"], currency), use_container_width=True)
            st.plotly_chart(charts.generate_rate_comparison_chart(loan_amount, loan_tenure_months, interest_rate, currency), use_container_width=True)
            
        with c_sub2:
            st.plotly_chart(charts.generate_combined_timeline_chart(loan_amount, interest_rate, loan_tenure_months, extra_monthly_budget, annual_bonus * 0.5, current_savings * 0.2, currency), use_container_width=True)
            
            st.markdown("##### Cumulative Paid Principal vs Interest")
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.plotly_chart(charts.generate_principal_paid_chart(base["schedule"], combined_sim, "Combined Strategy", currency), use_container_width=True)
            with c_col2:
                st.plotly_chart(charts.generate_interest_paid_chart(base["schedule"], combined_sim, "Combined Strategy", currency), use_container_width=True)
                
        with c_sub3:
            st.plotly_chart(charts.generate_debt_free_timeline_chart(current_age, loan_tenure_months, sim_emi["new_tenure_months"], sim_annual["new_tenure_months"], sim_lump["new_tenure_months"], combined_tenure), use_container_width=True)
            
            c_col3, c_col4 = st.columns(2)
            with c_col3:
                st.plotly_chart(charts.generate_emi_increase_savings_chart(loan_amount, interest_rate, loan_tenure_months, currency), use_container_width=True)
            with c_col4:
                st.plotly_chart(charts.generate_lump_sum_savings_chart(loan_amount, interest_rate, loan_tenure_months, currency), use_container_width=True)
                
    # TAB 5: LOAN HEALTH
    with tab5:
        st.subheader("🛡️ Loan Health Assessment Index")
        st.markdown("We assess leverage capacity, rate spreads, and financial cushion buffers to calculate your debt health score.")
        
        h_col1, h_col2 = st.columns([1, 1.2])
        
        with h_col1:
            st.plotly_chart(charts.generate_health_gauge_chart(score, status), use_container_width=True)
            
            st.markdown(f"""
            <div class="fintech-card">
                <h4 style="color:#3B82F6;margin-top:0;">Assessment Checklist Parameters</h4>
                <ul>
                    <li>Interest rate benchmark target for <b>{loan_type}</b>.</li>
                    <li>EMI-to-Income capacity (DTI).</li>
                    <li>Emergency reserve buffer coverage.</li>
                    <li>Amortization tenure duration length.</li>
                    <li>Prepayment capacity.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with h_col2:
            st.markdown("### Score Deductions & Areas for Improvement")
            if deductions:
                for d in deductions:
                    st.markdown(f"- 🔴 {d}")
            else:
                st.markdown("- ✅ **Perfect score!** Your debt structures and cash cushions are optimal.")
                
            st.markdown("---")
            st.markdown("### 🏛️ Loan Type Special Advice")
            st.markdown(specifics.get("advice", "Review loan specific structures."))
            
            if loan_type == "Home Loan" and "extra_emi_effect" in specifics:
                eff = specifics["extra_emi_effect"]
                st.markdown(f"""
                <div class="alert-card alert-success">
                    💡 <b>Extra 1 EMI Prepayment Effect (Home Loan):</b><br/>
                    Paying one additional standard EMI (₹{base['emi']:,.2f}) every 12 months will save you <b>{currency}{eff['interest_saved']:,.2f}</b> in interest and trim <b>{eff['years_saved']} years</b> off your tenure!
                </div>
                """, unsafe_allow_html=True)
                
            elif loan_type == "Car Loan" and "depreciation_timeline" in specifics:
                with st.expander("🚘 Vehicle Depreciation Timeline"):
                    df_dep = pd.DataFrame(specifics["depreciation_timeline"], columns=["Year", f"Vehicle Value ({currency})"])
                    st.dataframe(df_dep, use_container_width=True, hide_index=True)
                    
            st.markdown("---")
            st.markdown("### 🗓️ Financial Milestones Age Line")
            st.markdown(f"""
            - **Current Age:** {current_age} years old
            - **Baseline Loan Payoff Age:** **{milestones['loan_end_age']}** years old
            - **Optimized Loan Payoff Age:** **{milestones['debt_free_age']}** years old
            - **Retirement Target Age:** {retirement_age} years old
            - **Retirement Gap (Optimized):** Debt-free **{milestones['retirement_gap_opt']} years** before retirement.
            """)
            st.info(milestones["advice"])
            
    # TAB 6: AI COACH
    with tab6:
        st.subheader("💬 EMI Sense AI Loan Coach")
        st.markdown("Chat with our AI advisor about prepayments, investments, and balance transfers. Ask anything about your calculation outcomes.")
        
        # Suggested questions row
        st.markdown("##### 💡 Frequently Asked Questions")
        s_col1, s_col2, s_col3, s_col4 = st.columns(4)
        clicked_question = None
        
        with s_col1:
            if st.button("Should I increase my monthly EMI?", use_container_width=True):
                clicked_question = "Should I increase my monthly EMI?"
        with s_col2:
            if st.button("Should I invest extra funds or prepay loan?", use_container_width=True):
                clicked_question = "Should I invest extra funds or prepay my loan?"
        with s_col3:
            if st.button("Is refinancing worth it for my interest rate?", use_container_width=True):
                clicked_question = "Is refinancing worth it for my interest rate?"
        with s_col4:
            if st.button("How can I utilize my annual bonus to payoff?", use_container_width=True):
                clicked_question = "How can I utilize my annual bonus to pay off the loan faster?"
                
        # Render historical chat
        for q, a_resp in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(q)
            with st.chat_message("assistant"):
                st.write(a_resp)
                
        user_chat_input = st.chat_input("Ask your EMI Sense Coach...")
        
        # Process chat interaction
        input_to_process = user_chat_input or clicked_question
        if input_to_process:
            with st.chat_message("user"):
                st.write(input_to_process)
                
            with st.chat_message("assistant"):
                with st.spinner("AI Coach is analyzing numbers..."):
                    coach_response = ai.chat_with_coach(
                        st.session_state.chat_history, input_to_process, loan_data, base,
                        score, status, sim_emi, sim_annual, sim_lump, ai_provider, ai_api_key, ai_model
                    )
                    st.write(coach_response)
                    
            st.session_state.chat_history.append((input_to_process, coach_response))
            st.rerun()
            
    # TAB 7: EXPORTS & PDF REPORTS
    with tab7:
        st.subheader("📄 Generate Professional Financial Report")
        st.markdown("Export a complete breakdown of your loan, optimization schedules, health scoring, and AI advice as a professional PDF report.")
        
        rep_col1, rep_col2 = st.columns([1.5, 1])
        
        with rep_col1:
            st.markdown("""
            ### Report Contents Overview
            - **Executive Summary:** Overall assessment of debt health.
            - **Baseline Loan Parameters Table:** Core details of interest percentages, payment size, and tenure.
            - **Optimizations Simulations Matrix:** Side-by-side comparison of EMIs, lump-sum additions, and savings.
            - **Financial Health Analysis:** Deductions list and smart advisor warning alerts.
            - **Amortization Path Visuals:** Cumulative payment schedules and timelines.
            - **AI Advisor Strategic Action Plan:** Curated checklist of optimization steps.
            """)
            
            # Generate PDF in memory
            try:
                pdf_data_bytes = pdf.generate_pdf_report(
                    loan_data, base, sim_emi, sim_annual, sim_lump, combined_sim, refinance,
                    score, status, deductions, alerts, ai_advice
                )
                
                st.download_button(
                    label="📥 Download Professional PDF Report",
                    data=pdf_data_bytes,
                    file_name=f"EMI_Sense_AI_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("PDF Report compiled successfully and is ready for download.")
            except Exception as pdf_ex:
                st.error("Error occurred while compiling the ReportLab PDF.")
                st.code(traceback.format_exc())
                
        with rep_col2:
            st.markdown(f"""
            <div class="fintech-card" style="text-align:center;">
                <h4 style="color:#EAB308;margin-top:0;">Optimization Target Summary</h4>
                <div style="font-size:2.8rem;font-weight:700;color:#10B981;margin:15px 0;">{currency}{combined_savings:,.2f}</div>
                <div style="font-size:1.15rem;font-weight:600;margin-bottom:10px;">Total Cumulative Savings</div>
                <div style="font-size:0.95rem;color:#94A3B8;">By allocating your extra monthly budget, annual bonus prepayments, and lump-sum savings, you save substantial interest and finish your loan early.</div>
            </div>
            """, unsafe_allow_html=True)
