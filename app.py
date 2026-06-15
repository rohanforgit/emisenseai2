import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
import tempfile
import traceback

# Import modular libraries
import calculations as calc
import charts
import ai_engine as ai
import pdf_generator as pdf
import ai_config

# 1. Page Configuration Setup
st.set_page_config(
    page_title="EMI Sense AI - Loan Optimization Platform",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject style.css directly for premium styling
if os.path.exists("style.css"):
    with open("style.css", "r") as f:
        custom_css = f.read()
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #0F172A; color: #F8FAFC; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 3. Initialize Session State Configuration
if "config" not in st.session_state:
    st.session_state.config = {
        "loan_type": "Home Loan",
        "loan_amount": 5000000.0,
        "interest_rate": 8.5,
        "loan_tenure_months": 240,
        "monthly_income": 200000.0,
        "monthly_expenses": 80000.0,
        "current_reserve": 400000.0,
        "extra_monthly_budget": 20000.0,
        "annual_prepayment": 100000.0,
        "lump_sum_amount": 200000.0,
        "emi_increase_pct": 10.0,
        "refinance_rate": 8.0,
        "refinance_cost": 10000.0,
        "risk_appetite": "Moderate",
        "existing_investments": 500000.0,
        "inflation": 6.0,
        "current_age": 30,
        "retirement_age": 60,
        "currency": "₹"
    }

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Helper function to render KPI cards
def render_kpi_cards(emi, total_interest, total_payment, savings, health_score, health_status, debt_free_date, currency):
    health_colors = {
        "Excellent": "success",
        "Good": "success",
        "Average": "info",
        "Poor": "warning",
        "Danger": "danger"
    }
    hc = health_colors.get(health_status, "info")
    
    if isinstance(debt_free_date, datetime):
        df_str = debt_free_date.strftime("%b %Y")
    else:
        df_str = str(debt_free_date)
        
    # Semicircle SVG Gauge calculations
    score_val = max(0.0, min(100.0, float(health_score)))
    dash_offset = 110.0 - (110.0 * (score_val / 100.0))
    
    html = f"""
    <div class="kpi-grid">
      <div class="kpi-card border-accent">
        <div class="kpi-label">Monthly EMI</div>
        <div class="kpi-val accent">{currency}{emi:,.2f}</div>
        <div class="kpi-subtext">Baseline monthly EMI</div>
      </div>
      <div class="kpi-card border-danger">
        <div class="kpi-label">Interest Payable</div>
        <div class="kpi-val danger">{currency}{total_interest:,.2f}</div>
        <div class="kpi-subtext">Cumulative interest cost</div>
      </div>
      <div class="kpi-card border-accent">
        <div class="kpi-label">Total Payment</div>
        <div class="kpi-val">{currency}{total_payment:,.2f}</div>
        <div class="kpi-subtext">Principal + Interest</div>
      </div>
      <div class="kpi-card border-savings">
        <div class="kpi-label">Potential Savings</div>
        <div class="kpi-val savings">{currency}{savings:,.2f}</div>
        <div class="kpi-subtext">With prepayment plan</div>
      </div>
      <div class="kpi-card border-{hc}">
        <div class="kpi-label">Health Score</div>
        <div class="gauge-container" style="--dash-offset: {dash_offset:,.1f}px;">
          <svg class="gauge-svg" viewBox="0 0 100 60">
            <defs>
              <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#EF4444" />
                <stop offset="50%" stop-color="#FBBF24" />
                <stop offset="100%" stop-color="#34D399" />
              </linearGradient>
            </defs>
            <path class="gauge-track" d="M 15 50 A 35 35 0 0 1 85 50" />
            <path class="gauge-fill" d="M 15 50 A 35 35 0 0 1 85 50" />
          </svg>
          <div class="gauge-value">{score_val:.0f}</div>
          <div class="gauge-label">{health_status}</div>
        </div>
      </div>
      <div class="kpi-card border-success">
        <div class="kpi-label">Debt Free Date</div>
        <div class="kpi-val success">{df_str}</div>
        <div class="kpi-subtext">At optimized schedule</div>
      </div>
    </div>
    """
    return html

# Helper function to render Alert boxes
def render_alert_box(alerts):
    if not alerts:
        return "<div class='alert-box success'>✅ <b>Financial Checklist Clear:</b> No high-risk items found on your loan parameters.</div>"
        
    html = ""
    for a in alerts:
        icon = "🚨" if a["type"] == "danger" else "⚠️" if a["type"] == "warning" else "💡" if a["type"] == "info" else "✅"
        html += f"""
        <div class="alert-box {a['type']}">
            <span style="font-size: 1.2rem; margin-right: 10px;">{icon}</span>
            <span>{a['message']}</span>
        </div>
        """
    return html

# Header banner HTML
st.markdown("""
<div class="app-header">
    <h1>EMI Sense AI</h1>
    <p>💡 "Don't just calculate your loan. Optimize it." — Premium AI-Powered Financial Loan Optimization Advisor</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR: Hugging Face Configuration Module
ai_api_key, ai_model = ai_config.select_ai_settings()
st.sidebar.markdown("---")

# SIDEBAR: Config Upload/Download
st.sidebar.subheader("💾 Session Controls")
uploaded_file = st.sidebar.file_uploader("Upload Session Config File (.json)", type=["json"])
if uploaded_file is not None:
    try:
        uploaded_config = json.load(uploaded_file)
        for key in st.session_state.config:
            if key in uploaded_config:
                st.session_state.config[key] = uploaded_config[key]
        st.sidebar.success("Session Config Loaded!")
    except Exception as e:
        st.sidebar.error(f"Error loading config: {str(e)}")

# Save Config File Download
config_json = json.dumps(st.session_state.config, indent=4)
st.sidebar.download_button(
    label="📂 Save Config File",
    data=config_json,
    file_name="emi_sense_session.json",
    mime="application/json",
    use_container_width=True
)

if st.sidebar.button("🔄 Reset Dashboard", use_container_width=True):
    st.session_state.config = {
        "loan_type": "Home Loan",
        "loan_amount": 5000000.0,
        "interest_rate": 8.5,
        "loan_tenure_months": 240,
        "monthly_income": 200000.0,
        "monthly_expenses": 80000.0,
        "current_reserve": 400000.0,
        "extra_monthly_budget": 20000.0,
        "annual_prepayment": 100000.0,
        "lump_sum_amount": 200000.0,
        "emi_increase_pct": 10.0,
        "refinance_rate": 8.0,
        "refinance_cost": 10000.0,
        "risk_appetite": "Moderate",
        "existing_investments": 500000.0,
        "inflation": 6.0,
        "current_age": 30,
        "retirement_age": 60,
        "currency": "₹"
    }
    st.session_state.chat_history = []
    st.toast("Dashboard parameters reset back to defaults.")
    st.rerun()

st.sidebar.markdown("---")

# SIDEBAR: Core Settings Widgets
st.sidebar.subheader("⚙️ Parameter Setup")
currency = st.sidebar.selectbox("Currency Symbol", ["₹", "$", "€", "£", "¥"], index=["₹", "$", "€", "£", "¥"].index(st.session_state.config["currency"]))
loan_type = st.sidebar.selectbox("Loan Classification", ["Home Loan", "Car Loan", "Bike Loan", "Education Loan", "Personal Loan", "Business Loan", "Gold Loan", "Custom Loan"], index=["Home Loan", "Car Loan", "Bike Loan", "Education Loan", "Personal Loan", "Business Loan", "Gold Loan", "Custom Loan"].index(st.session_state.config["loan_type"]))

loan_amount = st.sidebar.number_input("Loan Principal Amount", min_value=1000.0, value=float(st.session_state.config["loan_amount"]), step=50000.0)
interest_rate = st.sidebar.slider("Interest Rate (% Annual)", min_value=0.5, max_value=30.0, value=float(st.session_state.config["interest_rate"]), step=0.1)
loan_tenure_months = st.sidebar.slider("Loan Tenure (Months)", min_value=12, max_value=480, value=int(st.session_state.config["loan_tenure_months"]), step=12)

# Cash Flow
monthly_income = st.sidebar.number_input("Monthly Net Income", min_value=0.0, value=float(st.session_state.config["monthly_income"]), step=5000.0)
monthly_expenses = st.sidebar.number_input("Monthly Living Expenses", min_value=0.0, value=float(st.session_state.config["monthly_expenses"]), step=2000.0)
current_reserve = st.sidebar.number_input("Emergency Cash Reserve", min_value=0.0, value=float(st.session_state.config["current_reserve"]), step=10000.0)
extra_monthly_budget = st.sidebar.number_input("Extra Monthly Prepay Budget", min_value=0.0, value=float(st.session_state.config["extra_monthly_budget"]), step=1000.0)

# Risk Profile Accordion
with st.sidebar.expander("⚖️ Risk & Strategy Profile"):
    risk_appetite = st.selectbox("Risk Appetite", ["Conservative", "Moderate", "Aggressive"], index=["Conservative", "Moderate", "Aggressive"].index(st.session_state.config["risk_appetite"]))
    existing_investments = st.number_input("Existing Investments Total", min_value=0.0, value=float(st.session_state.config["existing_investments"]), step=10000.0)
    inflation = st.slider("Expected Inflation Rate (%)", min_value=0.0, max_value=15.0, value=float(st.session_state.config["inflation"]), step=0.5)
    current_age = st.slider("Your Current Age", min_value=18, max_value=80, value=int(st.session_state.config["current_age"]), step=1)
    retirement_age = st.slider("Expected Retirement Age", min_value=40, max_value=90, value=int(st.session_state.config["retirement_age"]), step=1)

# Sync sidebar widget parameters with config dict
st.session_state.config.update({
    "currency": currency,
    "loan_type": loan_type,
    "loan_amount": loan_amount,
    "interest_rate": interest_rate,
    "loan_tenure_months": loan_tenure_months,
    "monthly_income": monthly_income,
    "monthly_expenses": monthly_expenses,
    "current_reserve": current_reserve,
    "extra_monthly_budget": extra_monthly_budget,
    "risk_appetite": risk_appetite,
    "existing_investments": existing_investments,
    "inflation": inflation,
    "current_age": current_age,
    "retirement_age": retirement_age
})

# Pre-calculations
extra_monthly_budget_calc = min(extra_monthly_budget, loan_amount)
annual_prepayment_calc = min(float(st.session_state.config["annual_prepayment"]), loan_amount)
lump_sum_amount_calc = min(float(st.session_state.config["lump_sum_amount"]), loan_amount)

base = calc.calculate_base_loan_details(loan_amount, interest_rate, loan_tenure_months)
sim_emi = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, float(st.session_state.config["emi_increase_pct"]))
sim_annual = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, annual_prepayment_calc)
sim_lump = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, lump_sum_amount_calc, mode="reduce_tenure")

combined_sim = calc.simulate_amortization(
    loan_amount, interest_rate, loan_tenure_months, 
    extra_monthly=extra_monthly_budget_calc, 
    annual_prepayment=annual_prepayment_calc, 
    lump_sum=lump_sum_amount_calc, 
    lump_sum_month=1
)
combined_interest = sum(m["interest"] for m in combined_sim)
combined_savings = base["total_interest"] - combined_interest
combined_tenure = len(combined_sim)

refinance = calc.calculate_refinancing(loan_amount, interest_rate, loan_tenure_months, float(st.session_state.config["refinance_rate"]), float(st.session_state.config["refinance_cost"]))
emi_ratio, emi_status, emi_advice = calc.calculate_emi_to_income(base["emi"], monthly_income)
em_fund = calc.calculate_emergency_fund(monthly_expenses, base["emi"], current_reserve)

score, status, deductions = calc.calculate_health_score(
    loan_amount, interest_rate, loan_tenure_months, base["emi"],
    monthly_income, monthly_expenses, current_reserve, extra_monthly_budget_calc, loan_type
)

alerts = calc.generate_smart_alerts(loan_amount, interest_rate, loan_tenure_months, base["emi"], monthly_income, monthly_expenses, current_reserve)
milestones = calc.get_financial_milestones(current_age, retirement_age, loan_tenure_months, combined_tenure)

what_if = calc.simulate_what_if_analysis(
    loan_amount, interest_rate, loan_tenure_months, monthly_income, monthly_expenses, current_reserve,
    extra_monthly_budget_calc, risk_appetite, existing_investments, inflation, current_age, retirement_age
)

specifics = calc.get_loan_specific_features(loan_type, loan_amount, interest_rate, loan_tenure_months, base["emi"])

# Package data for AI model context
loan_data = {
    "loan_amount": loan_amount,
    "interest_rate": interest_rate,
    "loan_tenure_months": loan_tenure_months,
    "monthly_income": monthly_income,
    "monthly_expenses": monthly_expenses,
    "extra_monthly_budget": extra_monthly_budget_calc,
    "annual_prepayment": annual_prepayment_calc,
    "lump_sum_amount": lump_sum_amount_calc,
    "emi_increase_pct": st.session_state.config["emi_increase_pct"],
    "refinance_rate": st.session_state.config["refinance_rate"],
    "refinance_cost": st.session_state.config["refinance_cost"],
    "refinance_net_savings": refinance.get("net_savings", 0),
    "currency": currency,
    "emi_ratio": emi_ratio,
    "emergency_savings": current_reserve,
    "risk_appetite": risk_appetite,
    "loan_type": loan_type,
    "home_loan_special_savings": specifics.get("extra_emi_effect", {}).get("interest_saved", 0.0) if loan_type == "Home Loan" else 0.0,
    "home_loan_special_years": specifics.get("extra_emi_effect", {}).get("years_saved", 0.0) if loan_type == "Home Loan" else 0.0,
    "depreciation_text": str(specifics.get("depreciation_timeline", "N/A")) if loan_type == "Car Loan" else "N/A"
}

# AI Recommendations (cached based on parameters)
@st.cache_data
def fetch_ai_recommendations(loan_bundle, base_details, sim_emi, sim_annual, sim_lump, refinance, score, status, deductions, api_key, model_name):
    return ai.get_ai_recommendations(
        loan_bundle, base_details, sim_emi, sim_annual, sim_lump, refinance,
        score, status, deductions, api_key, model_name
    )

ai_advice = fetch_ai_recommendations(
    loan_data, base, sim_emi, sim_annual, sim_lump, refinance,
    score, status, deductions, ai_api_key, ai_model
)

# Render PDF Generation Button directly in sidebar
try:
    pdf_bytes = pdf.generate_pdf_report(
        loan_data, base, sim_emi, sim_annual, sim_lump, combined_sim, refinance,
        score, status, deductions, alerts, ai_advice
    )
    st.sidebar.download_button(
        label="📄 Export PDF Report",
        data=pdf_bytes,
        file_name="EMI_Sense_AI_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )
except Exception as pdf_ex:
    st.sidebar.error("Error generating PDF: NameError or package mismatch.")
    st.sidebar.code(traceback.format_exc())

# --- MAIN PAGE TABS ---
tab_diagnostic, tab_prepayment, tab_risk, tab_charts = st.tabs([
    "📊 Advisor Diagnostic & AI Recommendation", 
    "⚡ Real-time Prepayment Simulators", 
    "🔍 Risk & Strategic Analyses", 
    "📈 Interactive Schedules & Timelines Charts"
])

# TAB 1: Diagnostic & AI Advisor
with tab_diagnostic:
    # KPI display cards
    kpi_html = render_kpi_cards(
        base["emi"], base["total_interest"], base["total_payment"], 
        combined_savings, score, status, 
        base["debt_free_date"] - (base["debt_free_date"] - datetime.now()) * (1 - (combined_tenure / loan_tenure_months)), 
        currency
    )
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    # Alerts Box
    alert_html = render_alert_box(alerts)
    st.markdown(alert_html, unsafe_allow_html=True)
    
    # Summary and AI recommendations layout
    col_sum, col_ai = st.columns([2, 3])
    
    with col_sum:
        st.markdown("### 📌 Executive Loan Analysis Summary")
        summary_markdown = f"""
        #### Base Loan Breakdown
        * **Monthly EMI:** {currency}{base['emi']:,.2f}
        * **Total Interest Payable:** {currency}{base['total_interest']:,.2f}
        * **Total Repayment:** {currency}{base['total_payment']:,.2f}
        * **Interest to Principal Ratio:** {base['interest_percentage']}% of total amount goes to interest!
        * **Debt Free Date:** {base['debt_free_date'].strftime('%d %B %Y')} ({round(loan_tenure_months / 12.0, 1)} years duration)
        
        #### 📊 Base vs. Optimized Combined Schedule
        * **New Optimized Tenure:** **{combined_tenure} months** (Saved **{round((loan_tenure_months - combined_tenure)/12.0, 1)} years**!)
        * **Interest Payable with Optimizations:** {currency}{combined_interest:,.2f}
        * **Net Financial Savings:** **{currency}{combined_savings:,.2f}**
        """
        st.markdown(summary_markdown)
        
    with col_ai:
        st.markdown("### 🏆 AI Coach Recommendations & Top Actions")
        st.markdown(ai_advice)
        
    # AI Chat room
    st.markdown("---")
    st.markdown("### 💬 AI Loan Coach Chat Room")
    
    # Suggested FAQs
    st.markdown("##### 💡 Frequently Asked Questions")
    faq_col1, faq_col2, faq_col3, faq_col4 = st.columns(4)
    clicked_question = None
    if faq_col1.button("Should I increase my monthly EMI?", use_container_width=True):
        clicked_question = "Should I increase my monthly EMI?"
    if faq_col2.button("Should I invest extra funds or prepay my loan?", use_container_width=True):
        clicked_question = "Should I invest extra funds or prepay my loan?"
    if faq_col3.button("Is refinancing worth it for my interest rate?", use_container_width=True):
        clicked_question = "Is refinancing worth it for my interest rate?"
    if faq_col4.button("How can I utilize my annual bonus to payoff?", use_container_width=True):
        clicked_question = "How can I utilize my annual bonus to pay off the loan faster?"
        
    # Historical Chat display
    for q, a_resp in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.write(a_resp)
            
    user_chat_input = st.chat_input("Ask your EMI Sense Coach...")
    
    input_to_process = user_chat_input or clicked_question
    if input_to_process:
        with st.chat_message("user"):
            st.write(input_to_process)
        with st.chat_message("assistant"):
            with st.spinner("AI Coach is analyzing numbers..."):
                coach_response = ai.chat_with_coach(
                    st.session_state.chat_history, input_to_process, loan_data, base,
                    score, status, sim_emi, sim_annual, sim_lump, ai_api_key, ai_model
                )
                st.write(coach_response)
        st.session_state.chat_history.append((input_to_process, coach_response))
        st.rerun()

# TAB 2: Prepayment Simulators
with tab_prepayment:
    st.markdown("Use the controls below to run real-time what-if simulations on prepayments and interest rates.")
    
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        st.markdown("### 📈 EMI Increase Simulator")
        emi_increase_pct = st.slider("Increase Monthly EMI By %", min_value=0, max_value=100, value=int(st.session_state.config["emi_increase_pct"]), step=5, key="tab2_emi_inc")
        st.session_state.config["emi_increase_pct"] = emi_increase_pct
        
        res_emi = calc.simulate_emi_increase(loan_amount, interest_rate, loan_tenure_months, emi_increase_pct)
        st.markdown(f"""
        * **New Adjusted EMI:** {currency}{res_emi['new_emi']:,.2f}
        * **Interest Saved:** {currency}{res_emi['interest_saved']:,.2f}
        * **Years Trimmed Off Tenure:** {res_emi['years_saved']} years
        * **Remaining Months:** {res_emi['new_tenure_months']} months
        """)
        fig_emi = charts.generate_emi_increase_savings_chart(loan_amount, interest_rate, loan_tenure_months)
        st.plotly_chart(fig_emi, use_container_width=True)

    with col_sim2:
        st.markdown("### 💰 One-Time Lump Sum Simulator")
        lump_sum_amount = st.number_input("Lump Sum Prepayment Amount", min_value=0.0, value=float(st.session_state.config["lump_sum_amount"]), step=10000.0, key="tab2_lump_sum")
        st.session_state.config["lump_sum_amount"] = lump_sum_amount
        
        res_lump = calc.simulate_lump_sum(loan_amount, interest_rate, loan_tenure_months, min(lump_sum_amount, loan_amount), mode="reduce_tenure")
        st.markdown(f"""
        * **One-time Prepayment:** {currency}{min(lump_sum_amount, loan_amount):,.2f}
        * **Interest Saved:** {currency}{res_lump['interest_saved']:,.2f}
        * **Years Trimmed Off Tenure:** {res_lump['years_saved']} years
        * **Remaining Months:** {res_lump['new_tenure_months']} months
        """)
        fig_lump = charts.generate_lump_sum_savings_chart(loan_amount, interest_rate, loan_tenure_months)
        st.plotly_chart(fig_lump, use_container_width=True)

    col_sim3, col_sim4 = st.columns(2)
    
    with col_sim3:
        st.markdown("### 🗓️ Recurring Annual Prepayment Simulator")
        annual_prepayment = st.number_input("Annual Prepayment Amount", min_value=0.0, value=float(st.session_state.config["annual_prepayment"]), step=5000.0, key="tab2_annual")
        st.session_state.config["annual_prepayment"] = annual_prepayment
        
        res_annual = calc.simulate_annual_prepayment(loan_amount, interest_rate, loan_tenure_months, min(annual_prepayment, loan_amount))
        st.markdown(f"""
        * **Annual Extra Prepayment:** {currency}{min(annual_prepayment, loan_amount):,.2f} / year
        * **Interest Saved:** {currency}{res_annual['interest_saved']:,.2f}
        * **Years Trimmed Off Tenure:** {res_annual['years_saved']} years
        * **Remaining Months:** {res_annual['new_tenure_months']} months
        """)
        fig_annual = charts.generate_annual_prepayment_savings_chart(loan_amount, interest_rate, loan_tenure_months)
        st.plotly_chart(fig_annual, use_container_width=True)

    with col_sim4:
        st.markdown("### 🔄 Balance Transfer & Refinance Analyzer")
        refinance_rate = st.slider("Target Refinance Interest Rate (%)", min_value=4.0, max_value=20.0, value=float(st.session_state.config["refinance_rate"]), step=0.1, key="tab2_ref_rate")
        refinance_cost = st.number_input("Refinancing Cost / Balance Transfer Fees", min_value=0.0, value=float(st.session_state.config["refinance_cost"]), step=1000.0, key="tab2_ref_cost")
        st.session_state.config["refinance_rate"] = refinance_rate
        st.session_state.config["refinance_cost"] = refinance_cost
        
        res_ref = calc.calculate_refinancing(loan_amount, interest_rate, loan_tenure_months, refinance_rate, refinance_cost)
        ref_status = "success" if res_ref["worth_refinancing"] else "danger"
        ref_text = "RECOMMENDED" if res_ref["worth_refinancing"] else "NOT RECOMMENDED"
        
        st.markdown(f"""
        <div class="premium-card" style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin: 0; color: #F8FAFC;">Refinance Assessment</h4>
                <div class="status-pill {ref_status}">{ref_text}</div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Current EMI</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #94A3B8;">{currency}{res_ref['current_emi']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">New Refinanced EMI</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #60A5FA;">{currency}{res_ref['new_emi']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Monthly Savings</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #34D399;">{currency}{res_ref['monthly_saving']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Break-Even Period</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FBBF24;">{res_ref['break_even_months']} Months</div>
                </div>
            </div>
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #94A3B8; font-size: 0.85rem;">Net Lifetime Savings:</span>
                <span style="font-size: 1.25rem; font-weight: 800; color: #34D399;">{currency}{res_ref['net_savings']:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        fig_rate = charts.generate_rate_comparison_chart(loan_amount, loan_tenure_months, interest_rate)
        st.plotly_chart(fig_rate, use_container_width=True)

# TAB 3: Risk & Strategic
with tab_risk:
    col_risk1, col_risk2 = st.columns(2)
    
    with col_risk1:
        ratio_status = "success" if emi_ratio < 30.0 else "warning" if emi_ratio < 40.0 else "danger"
        st.markdown(f"""
        <div class="premium-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #F8FAFC;">⚖️ Debt-to-Income (DTI) Ratio</h4>
                <div class="status-pill {ratio_status}">{emi_status}</div>
            </div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 5px;">
                {emi_ratio}%
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; line-height: 1.4;">
                {emi_advice}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        runway_status = "success" if em_fund["current_reserve"] >= em_fund["fund_6m"] else "warning" if em_fund["current_reserve"] >= em_fund["fund_3m"] else "danger"
        runway_pill = "Safe Runway" if em_fund["current_reserve"] >= em_fund["fund_6m"] else "Low Buffer" if em_fund["current_reserve"] >= em_fund["fund_3m"] else "Critical Buffer"
        st.markdown(f"""
        <div class="premium-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; color: #F8FAFC;">🛡️ Emergency Runway Buffer</h4>
                <div class="status-pill {runway_status}">{runway_pill}</div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Current Reserve</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #34D399;">{currency}{em_fund['current_reserve']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Monthly Outflow</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #F87171;">{currency}{em_fund['monthly_outflow']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">6-Month Buffer (Target)</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FBBF24;">{currency}{em_fund['fund_6m']:,.2f}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Required Gap</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: { '#34D399' if em_fund['gap'] <= 0 else '#F87171' };">
                        {currency}{em_fund['gap']:,.2f}
                    </div>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; font-size: 0.85rem; color: #94A3B8; line-height: 1.4;">
                {em_fund['advice']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_risk2:
        st.markdown(f"### 🛡️ Loan Health Index Score: {score}/100 ({status})")
        st.markdown("The health index checks interest rates, leverage levels, prepayment options, emergency funds, and overall cash buffers.")
        st.markdown("**Health Score Deductions / Areas of Concern:**")
        if deductions:
            for d in deductions:
                st.markdown(f"- 🔴 {d}")
        else:
            st.markdown("- ✅ **Perfect score!** Your loan and capital structures are highly optimized.")
            
        st.markdown("### 🗓️ Debt Payoff Milestones Timeline")
        
        # Calculate dynamic width percentages for the timeline nodes
        years_saved_val = round((loan_tenure_months - combined_tenure) / 12.0, 1)
        
        timeline_html = f"""
        <div class="timeline-container">
          <div class="timeline-line"></div>
          <div class="timeline-progress" style="width: 38%;"></div>
          
          <div class="timeline-node completed">
            <div class="timeline-dot"></div>
            <div class="timeline-age">{current_age}</div>
            <div class="timeline-title">Current Age</div>
            <div class="timeline-desc">Baseline Start</div>
          </div>
          
          <div class="timeline-node target">
            <div class="timeline-dot"></div>
            <div class="timeline-age">{milestones['debt_free_age']}</div>
            <div class="timeline-title">Debt Free (Opt)</div>
            <div class="timeline-desc">Saved {years_saved_val} Yrs!</div>
          </div>
          
          <div class="timeline-node active">
            <div class="timeline-dot"></div>
            <div class="timeline-age">{milestones['loan_end_age']}</div>
            <div class="timeline-title">Base Payoff</div>
            <div class="timeline-desc">Contract End</div>
          </div>
          
          <div class="timeline-node">
            <div class="timeline-dot"></div>
            <div class="timeline-age">{retirement_age}</div>
            <div class="timeline-title">Retirement</div>
            <div class="timeline-desc">Target Age</div>
          </div>
        </div>
        """
        st.markdown(timeline_html, unsafe_allow_html=True)
        st.write(milestones['advice'])

    st.markdown("---")
    
    col_sc, col_trade = st.columns([3, 2])
    with col_sc:
        st.markdown("### 🌪️ Advanced What-If Scenario Simulations Matrix")
        what_if_data = [
            ["Higher Salary (+15% income)", f"{what_if['higher_salary']['new_tenure_months']} months", f"{currency}{what_if['higher_salary']['interest_saved']:,.2f}", f"+{what_if['higher_salary']['years_saved']} yrs"],
            ["Lower Salary (-15% income)", f"{what_if['lower_salary']['new_tenure_months']} months", f"-{currency}{abs(what_if['lower_salary']['interest_saved']):,.2f}", f"{what_if['lower_salary']['years_saved']} yrs"],
            ["Family Expansion (+30% expenses)", f"{what_if['family_expansion']['new_tenure_months']} months", f"-{currency}{abs(what_if['family_expansion']['interest_saved']):,.2f}", f"{what_if['family_expansion']['years_saved']} yrs"],
            ["Interest Rate Jump (+2.0%)", f"{loan_tenure_months} (fixed)", f"Cost: +{currency}{what_if['rate_increase']['interest_difference']:,.2f}", "0 (EMI Adjusted)"],
            ["Interest Rate Drop (-2.0%)", f"{loan_tenure_months} (fixed)", f"Saved: {currency}{abs(what_if['rate_decrease']['interest_difference']):,.2f}", "0 (EMI Adjusted)"]
        ]
        df_sc = pd.DataFrame(what_if_data, columns=["What-If Scenario Event", "Tenure Months", "Interest Saved / Extra Cost", "Years Trimmed"])
        st.dataframe(df_sc, use_container_width=True, hide_index=True)
        
    with col_trade:
        st.markdown("### ⚖️ Prepay vs. Investment Growth Trade-off")
        p_vs_i = what_if["prepay_vs_invest"]
        st.markdown(f"""
        #### Option A: Prepay Loan (Guaranteed Return)
        * **Interest Rate Saved:** **{interest_rate}%**
        * **Guaranteed Lifetime Interest Savings:** {currency}{p_vs_i['interest_saved_prepay']:,.2f}
        * **Payoff speedup:** debt-free {p_vs_i['prepay_years_saved']} years faster.
        
        #### Option B: Invest Extra Budget (Expected Return)
        * **Investment Profile:** {risk_appetite} Risk Profile
        * **Expected Return Rate:** **{p_vs_i['investment_return_rate']}%**
        * **Estimated Investment Value:** {currency}{p_vs_i['investment_value']:,.2f} (Profit: {currency}{p_vs_i['investment_profit']:,.2f})
        
        #### ⚖️ Comparison & Advice
        * **Prepay Strategy Net Value:** {currency}{p_vs_i['prepay_strategy_value']:,.2f} (includes freed EMI compound value)
        * **Advisor Suggestion:** {p_vs_i['advice']}
        """)
        
    st.markdown("---")
    
    st.markdown("### ⚔️ Compare Two Distinct Loan Structures")
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        st.markdown("**Structure A Parameters**")
        comp_type_a = st.selectbox("Loan A Type", ["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], index=0, key="comp_a_type")
        comp_amt_a = st.number_input("Loan A Amount", value=5000000.0, step=50000.0, key="comp_a_amt")
        comp_rate_a = st.slider("Loan A Rate", min_value=0.5, max_value=30.0, value=8.5, step=0.1, key="comp_a_rate")
        comp_tenure_a = st.slider("Loan A Tenure (Months)", min_value=12, max_value=480, value=240, step=12, key="comp_a_tenure")
        
    with comp_col2:
        st.markdown("**Structure B Parameters**")
        comp_type_b = st.selectbox("Loan B Type", ["Home Loan", "Car Loan", "Personal Loan", "Custom Loan"], index=1, key="comp_b_type")
        comp_amt_b = st.number_input("Loan B Amount", value=5000000.0, step=50000.0, key="comp_b_amt")
        comp_rate_b = st.slider("Loan B Rate", min_value=0.5, max_value=30.0, value=7.5, step=0.1, key="comp_b_rate")
        comp_tenure_b = st.slider("Loan B Tenure (Months)", min_value=12, max_value=480, value=180, step=12, key="comp_b_tenure")
        
    base_a = calc.calculate_base_loan_details(comp_amt_a, comp_rate_a, comp_tenure_a)
    base_b = calc.calculate_base_loan_details(comp_amt_b, comp_rate_b, comp_tenure_b)
    
    class_a = "recommended" if base_a["total_payment"] < base_b["total_payment"] else ""
    class_b = "recommended" if base_b["total_payment"] < base_a["total_payment"] else ""
    badge_a = "Recommended (Lower Cost)" if class_a else "Loan Option A"
    badge_b = "Recommended (Lower Cost)" if class_b else "Loan Option B"
    
    comp_html = f"""
    <div class="comp-card-grid">
      <div class="comp-card {class_a}">
        <div class="comp-header">
          <div class="comp-title">{comp_type_a}</div>
          <div class="comp-badge">{badge_a}</div>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Principal Borrowed</span>
          <span class="comp-metric-val">{currency}{comp_amt_a:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Interest Rate</span>
          <span class="comp-metric-val">{comp_rate_a}%</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Tenure</span>
          <span class="comp-metric-val">{comp_tenure_a} Months</span>
        </div>
        <div class="comp-metric" style="margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.06);">
          <span class="comp-metric-label">Monthly EMI</span>
          <span class="comp-metric-val" style="color: #60A5FA;">{currency}{base_a['emi']:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Interest Payable</span>
          <span class="comp-metric-val" style="color: #F87171;">{currency}{base_a['total_interest']:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Total Repayment</span>
          <span class="comp-metric-val" style="font-size: 1.15rem; color: #F8FAFC;">{currency}{base_a['total_payment']:,.2f}</span>
        </div>
      </div>

      <div class="comp-card {class_b}">
        <div class="comp-header">
          <div class="comp-title">{comp_type_b}</div>
          <div class="comp-badge">{badge_b}</div>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Principal Borrowed</span>
          <span class="comp-metric-val">{currency}{comp_amt_b:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Interest Rate</span>
          <span class="comp-metric-val">{comp_rate_b}%</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Tenure</span>
          <span class="comp-metric-val">{comp_tenure_b} Months</span>
        </div>
        <div class="comp-metric" style="margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.06);">
          <span class="comp-metric-label">Monthly EMI</span>
          <span class="comp-metric-val" style="color: #60A5FA;">{currency}{base_b['emi']:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Interest Payable</span>
          <span class="comp-metric-val" style="color: #F87171;">{currency}{base_b['total_interest']:,.2f}</span>
        </div>
        <div class="comp-metric">
          <span class="comp-metric-label">Total Repayment</span>
          <span class="comp-metric-val" style="font-size: 1.15rem; color: #F8FAFC;">{currency}{base_b['total_payment']:,.2f}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(comp_html, unsafe_allow_html=True)
    
    comparison_rows = [
        ["Loan Type", comp_type_a, comp_type_b, "-"],
        ["Principal Borrowed", f"{currency}{comp_amt_a:,.2f}", f"{currency}{comp_amt_b:,.2f}", f"{currency}{(comp_amt_a - comp_amt_b):,.2f}"],
        ["Interest Rate", f"{comp_rate_a}%", f"{comp_rate_b}%", f"{round(comp_rate_a - comp_rate_b, 2)}%"],
        ["Tenure (Months)", f"{comp_tenure_a} months", f"{comp_tenure_b} months", f"{comp_tenure_a - comp_tenure_b} months"],
        ["Monthly EMI", f"{currency}{base_a['emi']:,.2f}", f"{currency}{base_b['emi']:,.2f}", f"{currency}{(base_a['emi'] - base_b['emi']):,.2f}"],
        ["Total Interest Payable", f"{currency}{base_a['total_interest']:,.2f}", f"{currency}{base_b['total_interest']:,.2f}", f"{currency}{(base_a['total_interest'] - base_b['total_interest']):,.2f}"],
        ["Total Repayment", f"{currency}{base_a['total_payment']:,.2f}", f"{currency}{base_b['total_payment']:,.2f}", f"{currency}{(base_a['total_payment'] - base_b['total_payment']):,.2f}"],
        ["Interest % of Payment", f"{base_a['interest_percentage']}%", f"{base_b['interest_percentage']}%", f"{round(base_a['interest_percentage'] - base_b['interest_percentage'], 2)}%"]
    ]
    df_comparison = pd.DataFrame(comparison_rows, columns=["Financial Parameter", "Loan Option A", "Loan Option B", "Difference"])
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)

# TAB 4: Interactive Charts
with tab_charts:
    st.markdown("Select tabs below to zoom, hover, and analyze details of the amortization timelines.")
    
    subtab1, subtab2, subtab3, subtab4, subtab5, subtab6 = st.tabs([
        "EMI Composition", 
        "Principal Outstanding", 
        "Cumulative Interest", 
        "Cumulative Principal", 
        "Baseline vs Prepay Strategy", 
        "Debt-Free Age Milestone"
    ])
    
    with subtab1:
        fig_pie = charts.generate_emi_breakdown_chart(loan_amount, base["total_interest"])
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with subtab2:
        fig_pr = charts.generate_principal_remaining_chart(base["schedule"], combined_sim, "Combined Strategy")
        st.plotly_chart(fig_pr, use_container_width=True)
        
    with subtab3:
        fig_int = charts.generate_interest_paid_chart(base["schedule"], combined_sim, "Combined Strategy")
        st.plotly_chart(fig_int, use_container_width=True)
        
    with subtab4:
        fig_cum_pr = charts.generate_principal_paid_chart(base["schedule"], combined_sim, "Combined Strategy")
        st.plotly_chart(fig_cum_pr, use_container_width=True)
        
    with subtab5:
        fig_comb = charts.generate_combined_timeline_chart(loan_amount, interest_rate, loan_tenure_months, extra_monthly_budget_calc, annual_prepayment_calc, lump_sum_amount_calc)
        st.plotly_chart(fig_comb, use_container_width=True)
        
    with subtab6:
        fig_df = charts.generate_debt_free_timeline_chart(current_age, loan_tenure_months, sim_emi["new_tenure_months"], sim_annual["new_tenure_months"], sim_lump["new_tenure_months"], combined_tenure)
        st.plotly_chart(fig_df, use_container_width=True)
