import plotly.graph_objects as go
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from calculations import (
    simulate_amortization,
    simulate_emi_increase,
    simulate_annual_prepayment,
    simulate_lump_sum,
    simulate_interest_rate_comparison
)

# Dark Theme parameters matching Streamlit styles
DARK_THEME_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#F8FAFC', size=11),
    margin=dict(l=40, r=40, t=40, b=40),
    hoverlabel=dict(bgcolor='#1E293B', font_color='#F8FAFC', font_family='Inter'),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
        font=dict(size=10, color='#F8FAFC')
    )
)

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor='#334155',
    linecolor='#475569',
    tickcolor='#475569',
    zeroline=False
)

def style_fig(fig):
    """
    Styles figures for the premium dark fintech experience.
    """
    fig.update_layout(**DARK_THEME_LAYOUT)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig

# 1. EMI Breakdown Chart (Pie)
def generate_emi_breakdown_chart(principal, total_interest, currency="₹"):
    labels = ['Principal Amount', 'Total Interest Payable']
    values = [principal, total_interest]
    colors = ['#3B82F6', '#EF4444']  # Accent Blue, Danger Red
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.5,
        marker=dict(colors=colors, line=dict(color='#0F172A', width=2)),
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Amount: " + currency + "%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
    )])
    fig.update_layout(title="EMI Composition (Principal vs Interest)")
    return style_fig(fig)

# 2. Principal Remaining Timeline (Line)
def generate_principal_remaining_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized", currency="₹"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    bal_base = [m["remaining_balance"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=bal_base, 
        mode='lines', 
        name='Baseline Loan',
        line=dict(color='#64748B', width=3),
        hovertemplate="Month %{x}<br>Balance: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        bal_opt = [m["remaining_balance"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=bal_opt, 
            mode='lines', 
            name=label_opt,
            line=dict(color='#EAB308', width=3, dash='dash'),
            hovertemplate="Month %{x}<br>Balance: " + currency + "%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        title="Remaining Principal Balance Over Time",
        xaxis_title="Month",
        yaxis_title="Outstanding Balance"
    )
    return style_fig(fig)

# 3. Interest Paid Over Time (Line)
def generate_interest_paid_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized", currency="₹"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    int_base = [m["cumulative_interest"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=int_base, 
        mode='lines', 
        name='Baseline Loan Interest',
        line=dict(color='#EF4444', width=2.5),
        hovertemplate="Month %{x}<br>Cum. Interest: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        int_opt = [m["cumulative_interest"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=int_opt, 
            mode='lines', 
            name=f'{label_opt} Interest',
            line=dict(color='#EAB308', width=3, dash='dot'),
            hovertemplate="Month %{x}<br>Cum. Interest: " + currency + "%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        title="Cumulative Interest Paid Over Time",
        xaxis_title="Month",
        yaxis_title="Cumulative Interest"
    )
    return style_fig(fig)

# 4. Principal Paid Over Time (Line)
def generate_principal_paid_chart(baseline_schedule, optimized_schedule=None, label_opt="Optimized", currency="₹"):
    fig = go.Figure()
    
    months_base = [m["month"] for m in baseline_schedule]
    pr_base = [m["cumulative_principal"] for m in baseline_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=pr_base, 
        mode='lines', 
        name='Baseline Principal Paid',
        line=dict(color='#3B82F6', width=2.5),
        hovertemplate="Month %{x}<br>Cum. Principal: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        pr_opt = [m["cumulative_principal"] for m in optimized_schedule]
        fig.add_trace(go.Scatter(
            x=months_opt, 
            y=pr_opt, 
            mode='lines', 
            name=f'{label_opt} Principal Paid',
            line=dict(color='#10B981', width=3, dash='dot'),
            hovertemplate="Month %{x}<br>Cum. Principal: " + currency + "%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        title="Cumulative Principal Paid Over Time",
        xaxis_title="Month",
        yaxis_title="Cumulative Principal"
    )
    return style_fig(fig)

# 5. Savings from EMI Increase (Bar)
def generate_emi_increase_savings_chart(principal, annual_rate, tenure_months, currency="₹"):
    percentages = [5, 10, 15, 20, 25, 50]
    savings = []
    
    for pct in percentages:
        res = simulate_emi_increase(principal, annual_rate, tenure_months, pct)
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"+{p}% EMI" for p in percentages],
        y=savings,
        marker_color='#3B82F6',
        text=[f"{currency}{s:,.0f}" for s in savings],
        textposition='outside',
        hovertemplate="Scenario: +%{x}<br>Savings: " + currency + "%{y:,.2f}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Interest Saved by EMI Increase % Scenarios",
        xaxis_title="EMI Increase Scenario",
        yaxis_title="Interest Saved",
        uniformtext_mode='hide'
    )
    return style_fig(fig)

# 6. Savings from Lump Sum Payment (Bar)
def generate_lump_sum_savings_chart(principal, annual_rate, tenure_months, currency="₹"):
    percentages = [5, 10, 20]
    amounts = [principal * (p / 100.0) for p in percentages]
    savings = []
    
    for amt in amounts:
        res = simulate_lump_sum(principal, annual_rate, tenure_months, amt, mode="reduce_tenure")
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"{p}% (Amount: {currency}{amounts[idx]:,.0f})" for idx, p in enumerate(percentages)],
        y=savings,
        marker_color='#EAB308',
        text=[f"{currency}{s:,.0f}" for s in savings],
        textposition='outside',
        hovertemplate="Lump Sum Level: %{x}<br>Savings: " + currency + "%{y:,.2f}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Interest Saved by One-time Lump Sum Payment Levels",
        xaxis_title="Lump Sum Amount",
        yaxis_title="Interest Saved"
    )
    return style_fig(fig)

# 7. Savings from Annual Prepayment (Bar)
def generate_annual_prepayment_savings_chart(principal, annual_rate, tenure_months, currency="₹"):
    percentages = [1, 2.5, 5]
    amounts = [principal * (p / 100.0) for p in percentages]
    savings = []
    
    for amt in amounts:
        res = simulate_annual_prepayment(principal, annual_rate, tenure_months, amt)
        savings.append(res["interest_saved"])
        
    fig = go.Figure(data=[go.Bar(
        x=[f"{p}% ({currency}{amounts[idx]:,.0f}/yr)" for idx, p in enumerate(percentages)],
        y=savings,
        marker_color='#10B981',
        text=[f"{currency}{s:,.0f}" for s in savings],
        textposition='outside',
        hovertemplate="Annual Prepay Level: %{x}<br>Savings: " + currency + "%{y:,.2f}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Interest Saved by Recurring Annual Prepayment Levels",
        xaxis_title="Annual Prepayment Level",
        yaxis_title="Interest Saved"
    )
    return style_fig(fig)

# 8. Interest Rate Comparison Chart (Grouped Bar)
def generate_rate_comparison_chart(principal, tenure_months, current_rate, currency="₹"):
    comparison = simulate_interest_rate_comparison(principal, tenure_months, current_rate)
    
    rates = [f"{c['rate']}%" for c in comparison]
    emis = [c['emi'] for c in comparison]
    total_interests = [c['total_interest'] for c in comparison]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rates,
        y=emis,
        name='Monthly EMI',
        marker_color='#3B82F6',
        hovertemplate="EMI: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=rates,
        y=total_interests,
        name='Total Interest',
        marker_color='#EF4444',
        hovertemplate="Interest: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="EMI and Total Interest Under Different Rates",
        xaxis_title="Interest Rate",
        yaxis_title="Amount",
        barmode='group'
    )
    return style_fig(fig)

# 9. Loan Balance Timeline - Combined prepays vs baseline (Line)
def generate_combined_timeline_chart(principal, annual_rate, tenure_months, 
                                     extra_monthly=0.0, annual_prepayment=0.0, lump_sum=0.0, currency="₹"):
    fig = go.Figure()
    
    base_schedule = simulate_amortization(principal, annual_rate, tenure_months)
    months_base = [m["month"] for m in base_schedule]
    bal_base = [m["remaining_balance"] for m in base_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_base, 
        y=bal_base, 
        mode='lines', 
        name='Baseline (No prepayments)',
        line=dict(color='#64748B', width=2.5),
        hovertemplate="Month %{x}<br>Balance: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    opt_schedule = simulate_amortization(
        principal, annual_rate, tenure_months, 
        extra_monthly=extra_monthly, 
        annual_prepayment=annual_prepayment, 
        lump_sum=lump_sum, 
        lump_sum_month=1
    )
    months_opt = [m["month"] for m in opt_schedule]
    bal_opt = [m["remaining_balance"] for m in opt_schedule]
    
    fig.add_trace(go.Scatter(
        x=months_opt, 
        y=bal_opt, 
        mode='lines', 
        name='Combined Strategy (Active Prepayments)',
        line=dict(color='#10B981', width=3),
        hovertemplate="Month %{x}<br>Balance: " + currency + "%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Amortization Paths: Baseline vs. Prepayment Plan",
        xaxis_title="Month",
        yaxis_title="Loan Balance"
    )
    return style_fig(fig)

# 10. Debt Free Timeline (Horizontal Bar Chart)
def generate_debt_free_timeline_chart(age, base_months, opt_months_emi, opt_months_annual, opt_months_lump, opt_months_combined):
    scenarios = ['Baseline', 'EMI Increase', 'Annual Prepay', 'Lump Sum Prepay', 'Combined Plan']
    months = [base_months, opt_months_emi, opt_months_annual, opt_months_lump, opt_months_combined]
    
    years = [m / 12.0 for m in months]
    ages = [age + y for y in years]
    
    fig = go.Figure()
    
    # We display the age at which the user becomes debt-free
    fig.add_trace(go.Bar(
        y=scenarios,
        x=ages,
        orientation='h',
        marker_color=['#64748B', '#3B82F6', '#10B981', '#EAB308', '#22C55E'],
        text=[f"Age {a:.1f} ({y:.1f} yrs)" for a, y in zip(ages, years)],
        textposition='inside',
        insidetextanchor='end',
        hovertemplate="Age: %{x:.1f} years old<extra></extra>"
    ))
    
    fig.update_layout(
        title="Debt-Free Age Milestones by Prepayment Strategy",
        xaxis_title="Age",
        yaxis_title="Scenario",
        xaxis=dict(range=[age, max(ages) + 2])
    )
    return style_fig(fig)

# Loan Health Gauge Chart
def generate_health_gauge_chart(score, status):
    """
    Renders a Plotly Indicator Gauge representing the loan health score.
    """
    colors = {
        "Excellent": "#10B981", # Green
        "Good": "#3B82F6",      # Blue
        "Average": "#F59E0B",   # Orange
        "Poor": "#EF4444",      # Red
        "Danger": "#991B1B"     # Deep Red
    }
    color = colors.get(status, "#3B82F6")
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        title = {'text': f"Health Assessment: {status}", 'font': {'size': 16, 'color': '#F8FAFC'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#F8FAFC"},
            'bar': {'color': color},
            'bgcolor': "rgba(30, 41, 59, 0.5)",
            'borderwidth': 2,
            'bordercolor': "#475569",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.15)'},
                {'range': [40, 60], 'color': 'rgba(245, 158, 11, 0.15)'},
                {'range': [60, 75], 'color': 'rgba(59, 130, 246, 0.15)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.15)'}
            ]
        },
        number = {'font': {'color': '#F8FAFC', 'size': 44}}
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#F8FAFC'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=240
    )
    return fig


# =====================================================================
# MATPLOTLIB HELPER FUNCTIONS FOR PDF REPORT EMBEDDING
# These functions output static figures saved as bytes arrays.
# =====================================================================

def generate_static_pie_chart(principal, total_interest):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 4), facecolor='#1E293B')
    ax.set_facecolor('#1E293B')
    
    labels = ['Principal', 'Interest']
    sizes = [principal, total_interest]
    colors = ['#3B82F6', '#EF4444']
    
    ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=colors, 
        textprops={'color': '#F8FAFC', 'fontsize': 10},
        wedgeprops=dict(width=0.4, edgecolor='#1E293B', linewidth=2)
    )
    
    ax.set_title("EMI Composition", color='#F8FAFC', fontsize=12, pad=15)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def generate_static_timeline_chart(baseline_schedule, optimized_schedule=None):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4), facecolor='#1E293B')
    ax.set_facecolor('#1E293B')
    
    months_base = [m["month"] for m in baseline_schedule]
    bal_base = [m["remaining_balance"] for m in baseline_schedule]
    ax.plot(months_base, bal_base, color='#64748B', linewidth=2.5, label='Baseline')
    
    if optimized_schedule:
        months_opt = [m["month"] for m in optimized_schedule]
        bal_opt = [m["remaining_balance"] for m in optimized_schedule]
        ax.plot(months_opt, bal_opt, color='#10B981', linewidth=2.5, linestyle='--', label='Optimized Combined')
        
    ax.set_title("Outstanding Principal Balance Timeline", color='#F8FAFC', fontsize=12)
    ax.set_xlabel("Month", color='#F8FAFC')
    ax.set_ylabel("Balance Outstanding", color='#F8FAFC')
    ax.tick_params(colors='#F8FAFC')
    ax.grid(True, color='#334155', linestyle=':')
    ax.legend(facecolor='#1E293B', edgecolor='#334155')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
