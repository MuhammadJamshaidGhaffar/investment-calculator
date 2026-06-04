import plotly.graph_objects as go
from plotly.subplots import make_subplots

def run_ultimate_wealth_analytics_engine(
    usd_initial_principal, 
    usd_annual_contribution=0, 
    usd_monthly_contribution=0, 
    growth_rate=0.10, 
    usd_inflation_rate=0.03, 
    zakat_rate=0.025, 
    years=20,
    initial_usd_to_pkr=278.0,       # Current baseline exchange rate
    pkr_annual_devaluation=0.06,    # Projected annual PKR devaluation rate (6%)
    pkr_inflation_rate=0.09          # Average long-term inflation rate in Pakistan (9%)
):
    # Setup initial tracking variables for both universes (USD)
    usd_nominal_with_zakat = usd_initial_principal
    usd_nominal_no_zakat = usd_initial_principal
    
    usd_cumulative_invested = usd_initial_principal
    usd_cumulative_inflation_factor = 1.0
    usd_total_zakat_paid = 0
    
    # Tracking variables for the PKR layer
    current_usd_to_pkr = initial_usd_to_pkr
    pkr_cumulative_inflation_factor = 1.0
    
    pkr_cumulative_invested = usd_initial_principal * initial_usd_to_pkr 
    monthly_growth_rate = (1 + growth_rate) ** (1/12) - 1
    
    # History Tracking Lists for Plotting
    years_axis = [0]
    
    # Universe A (With Zakat) History
    usd_nominal_with_z_hist = [usd_initial_principal]
    usd_real_with_z_hist = [usd_initial_principal]
    pkr_nominal_with_z_hist = [usd_initial_principal * initial_usd_to_pkr]
    pkr_real_portfolio_with_z_hist = [usd_initial_principal * initial_usd_to_pkr]
    
    # Universe B (No Zakat) History
    usd_nominal_no_z_hist = [usd_initial_principal]
    usd_real_no_z_hist = [usd_initial_principal]
    pkr_nominal_no_z_hist = [usd_initial_principal * initial_usd_to_pkr]
    pkr_real_portfolio_no_z_hist = [usd_initial_principal * initial_usd_to_pkr]
    
    # Baseline Reference Principal History
    usd_real_principal_hist = [usd_initial_principal]
    pkr_real_principal_hist = [usd_initial_principal * initial_usd_to_pkr]
    
    # Run the compounding loop over the years
    for year in range(1, years + 1):
        usd_cumulative_inflation_factor *= (1 + usd_inflation_rate)
        current_usd_to_pkr *= (1 + pkr_annual_devaluation)
        pkr_cumulative_inflation_factor *= (1 + pkr_inflation_rate)
        
        # --- UNIVERSE A: WITH ZAKAT ---
        if usd_monthly_contribution > 0:
            for month in range(12):
                usd_nominal_with_zakat = (usd_nominal_with_zakat * (1 + monthly_growth_rate)) + usd_monthly_contribution
                pkr_cumulative_invested += usd_monthly_contribution * current_usd_to_pkr
            usd_nominal_with_zakat += usd_annual_contribution
            pkr_cumulative_invested += usd_annual_contribution * current_usd_to_pkr
            # Fix: Update cumulative invested USD inside the loop
            usd_cumulative_invested += (usd_monthly_contribution * 12) + usd_annual_contribution
        else:
            usd_nominal_with_zakat = usd_nominal_with_zakat * (1 + growth_rate) + usd_annual_contribution
            pkr_cumulative_invested += usd_annual_contribution * current_usd_to_pkr
            # Fix: Update cumulative invested USD inside the loop
            usd_cumulative_invested += usd_annual_contribution
            
        # Capture state right BEFORE Zakat is deducted for tracking/analytics
        usd_val_pre_zakat = usd_nominal_with_zakat
            
        # Deduct Zakat at the end of the year
        annual_zakat = usd_nominal_with_zakat * zakat_rate
        usd_total_zakat_paid += annual_zakat
        usd_nominal_with_zakat -= annual_zakat
        
        # Convert final post-Zakat metrics to PKR for this specific year
        pkr_nominal_with_zakat = usd_nominal_with_zakat * current_usd_to_pkr
        pkr_real_portfolio_with_zakat = pkr_nominal_with_zakat / pkr_cumulative_inflation_factor
        pkr_real_value_of_principal = pkr_cumulative_invested / pkr_cumulative_inflation_factor
        
        # --- UNIVERSE B: WITHOUT ZAKAT ---
        if usd_monthly_contribution > 0:
            for month in range(12):
                usd_nominal_no_zakat = (usd_nominal_no_zakat * (1 + monthly_growth_rate)) + usd_monthly_contribution
            usd_nominal_no_zakat += usd_annual_contribution
        else:
            usd_nominal_no_zakat = usd_nominal_no_zakat * (1 + growth_rate) + usd_annual_contribution
            
        # --- COMPUTE & APPEND YEARLY HISTORICAL SNAPSHOTS FOR PLOTTING ---
        years_axis.append(year)
        
        # Universe A Snapshots (Post-Zakat values for the year)
        usd_nominal_with_z_hist.append(usd_nominal_with_zakat)
        usd_real_with_z_hist.append(usd_nominal_with_zakat / usd_cumulative_inflation_factor)
        pkr_nominal_with_z_hist.append(pkr_nominal_with_zakat)
        pkr_real_portfolio_with_z_hist.append(pkr_real_portfolio_with_zakat)
        
        # Universe B Snapshots
        pkr_nominal_no_zakat_year = usd_nominal_no_zakat * current_usd_to_pkr
        usd_nominal_no_z_hist.append(usd_nominal_no_zakat)
        usd_real_no_z_hist.append(usd_nominal_no_zakat / usd_cumulative_inflation_factor)
        pkr_nominal_no_z_hist.append(pkr_nominal_no_zakat_year)
        pkr_real_portfolio_no_z_hist.append(pkr_nominal_no_zakat_year / pkr_cumulative_inflation_factor)
        
        # Baseline Reference Cash Principal Snapshots
        usd_real_principal_hist.append(usd_cumulative_invested / usd_cumulative_inflation_factor)
        pkr_real_principal_hist.append(pkr_real_value_of_principal)
    
    # (Removed redundant post-loop update)

    # --- POST-SIMULATION DEEP METRICS (USD) ---
    # 1. Nominal USD Comparisons
    usd_nominal_post_zakat = usd_nominal_with_zakat
    usd_nominal_gain_with_zakat = usd_nominal_post_zakat - usd_cumulative_invested
    
    # 2. Real USD Comparisons (True US Purchasing Power)
    usd_real_value_of_principal = usd_cumulative_invested / usd_cumulative_inflation_factor
    usd_real_portfolio_post_zakat = usd_nominal_post_zakat / usd_cumulative_inflation_factor
    usd_real_gain_with_zakat = usd_real_portfolio_post_zakat - usd_real_value_of_principal
    
    # Universe B (No Zakat USD Metrics)
    usd_real_portfolio_no_zakat = usd_nominal_no_zakat / usd_cumulative_inflation_factor
    usd_real_gain_no_zakat = usd_real_portfolio_no_zakat - usd_real_value_of_principal

    # --- POST-SIMULATION METRICS (PKR LAYER) ---
    pkr_nominal_with_zakat = usd_nominal_with_zakat * current_usd_to_pkr
    pkr_nominal_no_zakat = usd_nominal_no_zakat * current_usd_to_pkr
    
    pkr_nominal_gain_with_zakat = pkr_nominal_with_zakat - pkr_cumulative_invested
    pkr_nominal_gain_no_zakat = pkr_nominal_no_zakat - pkr_cumulative_invested
    
    pkr_real_portfolio_with_zakat = pkr_nominal_with_zakat / pkr_cumulative_inflation_factor
    pkr_real_portfolio_no_zakat = pkr_nominal_no_zakat / pkr_cumulative_inflation_factor
    pkr_real_value_of_principal = pkr_cumulative_invested / pkr_cumulative_inflation_factor
    
    pkr_real_gain_with_zakat = pkr_real_portfolio_with_zakat - pkr_real_value_of_principal
    pkr_real_gain_no_zakat = pkr_real_portfolio_no_zakat - pkr_real_value_of_principal

    # --- PRINTING THE COMPARATIVE DEEP REPORT ---
    print("=" * 75)
    print(f"            DEEP DUAL-CURRENCY WEALTH REPORT (OVER {years} YEARS)")
    print("=" * 75)
    print(f"• Total Out-of-Pocket Cash Paid (Principal)       : ${usd_cumulative_invested:,.2f} USD")
    print(f"• Total Literal PKR Invested (At historical rates): {pkr_cumulative_invested:,.2f} PKR")
    print(f"• Projected Final USD to PKR Exchange Rate         : {current_usd_to_pkr:,.2f} PKR per 1 USD")
    print("-" * 75)
    
    print("[ SCENARIO 1: WITH FULL ANNUAL ZAKAT (100% Halal Optimization) ]")
    print(f"  ======= THE US DOLLAR (USD) UNIVERSE =======")
    print(f"  --- NOMINAL VALUE COMPARISON (App Screen USD vs. Deposited USD) ---")
    print(f"  -> Total Nominal USD Invested (Sum of Deposits) : ${usd_cumulative_invested:,.2f} USD")
    print(f"  -> Final Nominal Portfolio Value (Post-Zakat)   : ${usd_nominal_post_zakat:,.2f} USD")
    print(f"  => NET NOMINAL USD GAIN                         : ${usd_nominal_gain_with_zakat:,.2f} USD")
    print(f"")
    print(f"  --- REAL VALUE COMPARISON (True US Purchasing Power) ---")
    print(f"  -> Real Buying Power of Invested USD Capital    : ${usd_real_value_of_principal:,.2f} USD")
    print(f"  -> Final Real Buying Power of Portfolio (Post-Z): ${usd_real_portfolio_post_zakat:,.2f} USD")
    print(f"  => NET REAL USD GAIN (True Value Added)         : ${usd_real_gain_with_zakat:,.2f} USD")
    print(f"")
    print(f"  ======= THE PAKISTANI RUPEE (PKR) UNIVERSE =======")
    print(f"  --- NOMINAL VALUE COMPARISON (App Screen Rupees vs. Deposited Rupees) ---")
    print(f"  -> Total Nominal PKR Invested (Sum of Deposits) : {pkr_cumulative_invested:,.2f} PKR")
    print(f"  -> Final Nominal Portfolio Value (In PKR)       : {pkr_nominal_with_zakat:,.2f} PKR")
    print(f"  => NET NOMINAL PKR GAIN                         : {pkr_nominal_gain_with_zakat:,.2f} PKR")
    print(f"")
    print(f"  --- REAL VALUE COMPARISON (True Pakistan Purchasing Power) ---")
    print(f"  -> Real Buying Power of Invested PKR Capital    : {pkr_real_value_of_principal:,.2f} PKR")
    print(f"  -> Final Real Buying Power of Portfolio (Post-Z): {pkr_real_portfolio_with_zakat:,.2f} PKR")
    print(f"  => NET REAL PKR GAIN (True Value Added)         : {pkr_real_gain_with_zakat:,.2f} PKR")
    print(f"  -----------------------------------------------------------------")
    print(f"  -> Total Cumulative Zakat Given to Charity       : ${usd_total_zakat_paid:,.2f} USD")
    
    print("[ SCENARIO 2: WITHOUT ANY ZAKAT DEDUCTION ]")
    print(f"  ======= THE US DOLLAR (USD) UNIVERSE =======")
    print(f"  --- NOMINAL VALUE COMPARISON (App Screen USD vs. Deposited USD) ---")
    print(f"  -> Total Nominal USD Invested (Sum of Deposits) : ${usd_cumulative_invested:,.2f} USD")
    print(f"  -> Final Nominal Portfolio Value (No Zakat)     : ${usd_nominal_no_zakat:,.2f} USD")
    print(f"  => NET NOMINAL USD GAIN                         : ${usd_nominal_no_zakat - usd_cumulative_invested:,.2f} USD")
    print(f"")
    print(f"  --- REAL VALUE COMPARISON (True US Purchasing Power) ---")
    print(f"  -> Real Buying Power of Invested USD Capital    : ${usd_real_value_of_principal:,.2f} USD")
    print(f"  -> Final Real Buying Power of Portfolio (No Z)  : ${usd_real_portfolio_no_zakat:,.2f} USD")
    print(f"  => NET REAL USD GAIN (True Value Added)         : ${usd_real_gain_no_zakat:,.2f} USD")
    print(f"")
    print(f"  ======= THE PAKISTANI RUPEE (PKR) UNIVERSE =======")
    print(f"  --- NOMINAL VALUE COMPARISON (App Screen Rupees vs. Deposited Rupees) ---")
    print(f"  -> Total Nominal PKR Invested (Sum of Deposits) : {pkr_cumulative_invested:,.2f} PKR")
    print(f"  -> Final Nominal Portfolio Value (In PKR)       : {pkr_nominal_no_zakat:,.2f} PKR")
    print(f"  => NET NOMINAL PKR GAIN                         : {pkr_nominal_gain_no_zakat:,.2f} PKR")
    print(f"")
    print(f"  --- REAL VALUE COMPARISON (True Pakistan Purchasing Power) ---")
    print(f"  -> Real Buying Power of Invested PKR Capital    : {pkr_real_value_of_principal:,.2f} PKR")
    print(f"  -> Final Real Buying Power of Portfolio (No Z)  : {pkr_real_portfolio_no_zakat:,.2f} PKR")
    print(f"  => NET REAL PKR GAIN (True Value Added)         : {pkr_real_gain_no_zakat:,.2f} PKR")
    print("=" * 75)

    # --- INTERACTIVE CHART GENERATION LAYER (PLOTLY) ---
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "PKR Nominal Balances (App Screen Evaluation)",
            "USD Nominal Balances (Broker Account Value)",
            "True Pakistan Purchasing Power (PK Inflation Adj)",
            "True US Purchasing Power (US Inflation Adj)"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # Helper function to add traces
    def add_trace_to_fig(x, y, name, row, col, color, dash=None, marker=None):
        fig.add_trace(
            go.Scatter(
                x=x, y=y, name=name,
                line=dict(color=color, width=2.5, dash=dash),
                mode='lines+markers' if marker else 'lines',
                marker=dict(symbol=marker) if marker else None,
                hovertemplate='%{y:,.0f}<extra></extra>'
            ),
            row=row, col=col
        )

    # Row 1, Col 1: PKR Nominal
    add_trace_to_fig(years_axis, pkr_nominal_with_z_hist, "S1: With Zakat (PKR Nom)", 1, 1, "#2ecc71", marker='circle')
    add_trace_to_fig(years_axis, pkr_nominal_no_z_hist, "S2: No Zakat (PKR Nom)", 1, 1, "#27ae60", dash='dash', marker='x')
    add_trace_to_fig(years_axis, [pkr_cumulative_invested * (y/years) if y > 0 else pkr_nominal_with_z_hist[0] for y in years_axis], "Total PKR Invested", 1, 1, "#95a5a6", dash='dot')

    # Row 1, Col 2: USD Nominal
    add_trace_to_fig(years_axis, usd_nominal_with_z_hist, "S1: With Zakat (USD Nom)", 1, 2, "#3498db", marker='circle')
    add_trace_to_fig(years_axis, usd_nominal_no_z_hist, "S2: No Zakat (USD Nom)", 1, 2, "#2980b9", dash='dash', marker='x')
    add_trace_to_fig(years_axis, [usd_cumulative_invested * (y/years) if y > 0 else usd_nominal_with_z_hist[0] for y in years_axis], "Total USD Invested", 1, 2, "#95a5a6", dash='dot')

    # Row 2, Col 1: PKR Real
    add_trace_to_fig(years_axis, pkr_real_portfolio_with_z_hist, "S1: With Zakat (PKR Real)", 2, 1, "#e74c3c", marker='square')
    add_trace_to_fig(years_axis, pkr_real_portfolio_no_z_hist, "S2: No Zakat (PKR Real)", 2, 1, "#9b59b6", dash='dash', marker='triangle-up')
    add_trace_to_fig(years_axis, pkr_real_principal_hist, "Real Value of Principal (PKR)", 2, 1, "#c0392b", dash='dot')

    # Row 2, Col 2: USD Real
    add_trace_to_fig(years_axis, usd_real_with_z_hist, "S1: With Zakat (USD Real)", 2, 2, "#e67e22", marker='square')
    add_trace_to_fig(years_axis, usd_real_no_z_hist, "S2: No Zakat (USD Real)", 2, 2, "#d35400", dash='dash', marker='triangle-up')
    add_trace_to_fig(years_axis, usd_real_principal_hist, "Real Value of Principal (USD)", 2, 2, "#7f8c8d", dash='dot')

    # Update Layout
    fig.update_layout(
        title_text=f"Strategic Wealth Analytics Over {years} Years: With Zakat vs. No Zakat",
        title_x=0.5,
        title_y=0.98,
        title_font=dict(size=24, color="#2c3e50"),
        height=1300,
        showlegend=True,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
            bgcolor="rgba(255, 255, 255, 0.5)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1
        ),
        margin=dict(l=50, r=200, t=100, b=50)
    )

    # Set Y-axis formats
    fig.update_yaxes(tickformat=",.0f", title_text="Value in PKR", row=1, col=1)
    fig.update_yaxes(tickformat="$,.0f", title_text="Value in USD", row=1, col=2)
    fig.update_yaxes(tickformat=",.0f", title_text="Buying Power (PKR)", row=2, col=1)
    fig.update_yaxes(tickformat="$,.0f", title_text="Buying Power (USD)", row=2, col=2)
    fig.update_xaxes(title_text="Years")

    # --- HTML REPORT WRAPPING ---
    summary_html = f"""
    <html>
    <head>
        <title>Wealth Analytics Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f0f2f5; color: #333; }}
            .container {{ max-width: 1500px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 2.5em; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-top: 40px; }}
            .metric-group {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: #fff; padding: 25px; border-top: 5px solid #3498db; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }}
            .metric-card.pkr {{ border-top-color: #27ae60; }}
            .metric-card.zakat {{ border-top-color: #e74c3c; }}
            .metric-card p {{ margin: 0; color: #7f8c8d; text-transform: uppercase; font-size: 0.85em; font-weight: bold; letter-spacing: 1px; }}
            .metric-card h2 {{ border: none; margin: 10px 0 0; font-size: 1.8em; color: #2c3e50; }}
            
            .scenario {{ background: #ffffff; padding: 30px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #e1e4e8; }}
            .scenario h3 {{ margin-top: 0; color: #2980b9; font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; }}
            .sub-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
            .highlight {{ font-weight: bold; color: #2c3e50; display: block; margin-bottom: 15px; font-size: 1.1em; }}
            .gain {{ color: #27ae60; font-weight: bold; }}
            ul {{ list-style-type: none; padding: 0; margin: 0; }}
            li {{ margin-bottom: 12px; font-size: 1em; display: flex; justify-content: space-between; border-bottom: 1px dashed #ddd; padding-bottom: 5px; }}
            li span:last-child {{ font-weight: 600; }}
            
            .chart-container {{ margin-top: 30px; padding: 20px; background: #fff; border-radius: 12px; border: 1px solid #eee; overflow: hidden; }}
            .footer {{ text-align: center; margin-top: 60px; color: #bdc3c7; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Wealth Analytics Report</h1>
            <p style="text-align:center; color:#7f8c8d; font-size:1.1em;">Projection for a <span class="highlight" style="display:inline;">{years} Year</span> investment horizon</p>

            <div class="scenario" style="background: #f1f3f5; border-left: 5px solid #2c3e50;">
                <h3 style="color: #2c3e50; font-size: 1.1em; margin-bottom: 10px;">Simulation Parameters</h3>
                <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; font-size: 0.9em;">
                    <div>
                        <strong>Financials:</strong><br>
                        • Initial: ${usd_initial_principal:,.0f}<br>
                        • Monthly: ${usd_monthly_contribution:,.0f}<br>
                        • Annual: ${usd_annual_contribution:,.0f}
                    </div>
                    <div>
                        <strong>Rates & Growth:</strong><br>
                        • Growth: {growth_rate*100:.1f}%<br>
                        • US Inflation: {usd_inflation_rate*100:.1f}%<br>
                        • Zakat: {zakat_rate*100:.2f}%
                    </div>
                    <div>
                        <strong>PKR Dynamics:</strong><br>
                        • Start Rate: {initial_usd_to_pkr:,.1f}<br>
                        • Devaluation: {pkr_annual_devaluation*100:.1f}%<br>
                        • PK Inflation: {pkr_inflation_rate*100:.1f}%
                    </div>
                </div>
            </div>

            <div class="metric-group">
                <div class="metric-card">
                    <p>Principal (USD)</p>
                    <h2>${usd_cumulative_invested:,.0f}</h2>
                </div>
                <div class="metric-card pkr">
                    <p>Principal (PKR)</p>
                    <h2>{pkr_cumulative_invested:,.0f}</h2>
                </div>
                <div class="metric-card">
                    <p>Final Rate (PKR/USD)</p>
                    <h2>{current_usd_to_pkr:,.0f}</h2>
                </div>
                <div class="metric-card zakat">
                    <p>Total Zakat (USD)</p>
                    <h2>${usd_total_zakat_paid:,.0f}</h2>
                </div>
            </div>

            <div class="scenario">
                <h3>Scenario 1: With Annual Zakat (Halal Optimized)</h3>
                <div class="grid">
                    <div class="sub-section">
                        <span class="highlight">US Dollar Universe</span>
                        <ul>
                            <li><span>Invested Capital (Real)</span> <span>${usd_real_value_of_principal:,.2f}</span></li>
                            <li><span>Final Portfolio (Nominal)</span> <span>${usd_nominal_post_zakat:,.2f}</span></li>
                            <li><span>Nominal Net Gain</span> <span class="gain">${usd_nominal_gain_with_zakat:,.2f}</span></li>
                            <li><span>Final Buying Power (Real)</span> <span>${usd_real_portfolio_post_zakat:,.2f}</span></li>
                            <li><span>True Value Added (Real)</span> <span class="gain">${usd_real_gain_with_zakat:,.2f}</span></li>
                        </ul>
                    </div>
                    <div class="sub-section">
                        <span class="highlight">Pakistan Rupee Universe</span>
                        <ul>
                            <li><span>Invested Capital (Real)</span> <span>{pkr_real_value_of_principal:,.0f} PKR</span></li>
                            <li><span>Final Portfolio (Nominal)</span> <span>{pkr_nominal_with_zakat:,.0f} PKR</span></li>
                            <li><span>Nominal Net Gain</span> <span class="gain">{pkr_nominal_gain_with_zakat:,.0f} PKR</span></li>
                            <li><span>Final Buying Power (Real)</span> <span>{pkr_real_portfolio_with_zakat:,.0f} PKR</span></li>
                            <li><span>True Value Added (Real)</span> <span class="gain">{pkr_real_gain_with_zakat:,.0f} PKR</span></li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="scenario">
                <h3>Scenario 2: Without Zakat (Conventional)</h3>
                <div class="grid">
                    <div class="sub-section">
                        <span class="highlight">US Dollar Universe</span>
                        <ul>
                            <li><span>Invested Capital (Real)</span> <span>${usd_real_value_of_principal:,.2f}</span></li>
                            <li><span>Final Portfolio (Nominal)</span> <span>${usd_nominal_no_zakat:,.2f}</span></li>
                            <li><span>Nominal Net Gain</span> <span class="gain">${usd_nominal_no_zakat - usd_cumulative_invested:,.2f}</span></li>
                            <li><span>Final Buying Power (Real)</span> <span>${usd_real_portfolio_no_zakat:,.2f}</span></li>
                            <li><span>True Value Added (Real)</span> <span class="gain">${usd_real_gain_no_zakat:,.2f}</span></li>
                        </ul>
                    </div>
                    <div class="sub-section">
                        <span class="highlight">Pakistan Rupee Universe</span>
                        <ul>
                            <li><span>Invested Capital (Real)</span> <span>{pkr_real_value_of_principal:,.0f} PKR</span></li>
                            <li><span>Final Portfolio (Nominal)</span> <span>{pkr_nominal_no_zakat:,.0f} PKR</span></li>
                            <li><span>Nominal Net Gain</span> <span class="gain">{pkr_nominal_gain_no_zakat:,.0f} PKR</span></li>
                            <li><span>Final Buying Power (Real)</span> <span>{pkr_real_portfolio_no_zakat:,.0f} PKR</span></li>
                            <li><span>True Value Added (Real)</span> <span class="gain">{pkr_real_gain_no_zakat:,.0f} PKR</span></li>
                        </ul>
                    </div>
                </div>
            </div>

            <h2>Interactive Visual Analytics</h2>
            <div class="chart-container">
                {fig.to_html(full_html=False, include_plotlyjs='cdn')}
            </div>

            <div class="footer">
                Report generated for analysis of long-term wealth compounding and inflation hedging.
            </div>
        </div>
    </body>
    </html>
    """

    output_path = "wealth_analytics_report.html"
    with open(output_path, "w") as f:
        f.write(summary_html)
    
    print(f"\n[SUCCESS] Self-contained report saved to: {output_path}")
    print("Open this file in any browser to see the summary and interactive charts.")

# Run execution loop with user specifications ($500/monthly DCA)
run_ultimate_wealth_analytics_engine(
    usd_initial_principal=0, 
    usd_annual_contribution=0, 
    usd_monthly_contribution=500, 
    growth_rate=0.10, 
    usd_inflation_rate=0.03, 
    zakat_rate=0.025, 
    years=10,
    initial_usd_to_pkr=278.0,
    pkr_annual_devaluation=0.06,
    pkr_inflation_rate=0.09
)