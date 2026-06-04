"""
Applied Strategies:
1. "Buy the Dip" (Value Averaging): 
   Dynamically increases monthly contributions (e.g., 2x) when the market price drops 
   a specific percentage (e.g., 20%) below its All-Time High (ATH). This allows 
   accumulating more shares during market corrections.

2. Multi-Asset Halal Split:
   Allocates monthly contributions across multiple Shariah-compliant assets 
   (e.g., 80% SPUS for growth, 20% SPSK for stability) based on configurable weightages.
   This diversification reduces sector-specific risk and provides cash reserves.
"""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np
from datetime import datetime

def get_inflation_data(csv_path="API_FP.CPI.TOTL.ZG_DS2_en_csv_v2_278989.csv"):
    if not os.path.exists(csv_path):
        print(f"Warning: Inflation CSV not found at {csv_path}. Using fallback values.")
        return {}, {}
    
    try:
        df = pd.read_csv(csv_path, skiprows=4)
        us_row = df[df['Country Name'] == 'United States']
        pk_row = df[df['Country Name'] == 'Pakistan']

        us_inflation = {}
        pk_inflation = {}

        for col in df.columns:
            if col.isdigit():
                year = int(col)
                us_val = us_row[col].values[0] if not us_row.empty else None
                pk_val = pk_row[col].values[0] if not pk_row.empty else None
                
                if us_val is not None and not pd.isna(us_val):
                    us_inflation[year] = float(us_val) / 100.0
                if pk_val is not None and not pd.isna(pk_val):
                    pk_inflation[year] = float(pk_val) / 100.0
        
        return us_inflation, pk_inflation
    except Exception as e:
        print(f"Error parsing inflation CSV: {e}")
        return {}, {}

def collect_historical_data(tickers, start_year, end_year):
    if isinstance(tickers, str):
        tickers = [tickers]
        
    print(f"Fetching historical market data for {tickers} from {start_year} to {end_year}...")
    
    try:
        all_symbols = tickers + ["USDPKR=X"]
        raw_data = yf.download(all_symbols, start=f"{start_year-1}-11-01", end=f"{end_year}-12-31", auto_adjust=True)
        
        if raw_data.empty:
            print(f"Error: No data found for tickers {tickers}.")
            return pd.DataFrame()

        if isinstance(raw_data.columns, pd.MultiIndex):
            close_data = raw_data['Close']
        else:
            close_data = pd.DataFrame({tickers[0]: raw_data['Close']})

        # Resample to Monthly (Month End)
        history_df = close_data.resample('ME').last()
        
        if "USDPKR=X" in history_df.columns:
            history_df.rename(columns={"USDPKR=X": "Exchange_Rate_PKR"}, inplace=True)
        else:
            # Fallback if USDPKR=X missing for some reason
            history_df['Exchange_Rate_PKR'] = 280.0 
            
        history_df['Actual_PKR_Devaluation'] = history_df['Exchange_Rate_PKR'].pct_change()
        
        us_inf_map, pk_inflation_map = get_inflation_data()
        history_df['Year'] = history_df.index.year
        
        history_df['USD_Inf_Annual'] = history_df['Year'].map(us_inf_map).ffill().bfill().fillna(0.03)
        history_df['PKR_Inf_Annual'] = history_df['Year'].map(pk_inflation_map).ffill().bfill().fillna(0.09)
        
        # Monthly inflation rates
        history_df['Actual_USD_Inflation'] = (1 + history_df['USD_Inf_Annual'])**(1/12) - 1
        history_df['Actual_PKR_Inflation'] = (1 + history_df['PKR_Inf_Annual'])**(1/12) - 1
        
        for t in tickers:
            history_df[f'{t}_Growth_Rate'] = history_df[t].pct_change()
        
        history_df = history_df[history_df['Year'] >= start_year].copy()
        history_df = history_df.dropna(subset=[f'{tickers[0]}_Growth_Rate'])
        
        if history_df.empty:
            print("Warning: Historical range resulted in empty dataset.")
            return pd.DataFrame()
            
        return history_df
    except Exception as e:
        print(f"Error collecting data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def run_historical_wealth_engine(
    historical_records,
    usd_initial_principal,
    portfolio_config,
    buy_the_dip_config,
    usd_annual_contribution=0,
    usd_monthly_contribution=0,
    zakat_rate=0.025
):
    if historical_records.empty:
        print("No historical data available to run simulation.")
        return

    # Validate Portfolio Weights
    if abs(sum(portfolio_config.values()) - 1.0) > 1e-6:
        print(f"Error: Portfolio weights must sum to 100%. Current sum: {sum(portfolio_config.values())}")
        return

    # Tracking Variables
    usd_nominal_with_zakat = usd_initial_principal
    usd_nominal_no_zakat = usd_initial_principal
    
    usd_cumulative_invested = usd_initial_principal
    usd_real_principal_accumulated = usd_initial_principal
    
    usd_cumulative_inflation_factor = 1.0
    pkr_cumulative_inflation_factor = 1.0
    usd_total_zakat_paid = 0
    
    first_row = historical_records.iloc[0]
    initial_pkr_rate = first_row['Exchange_Rate_PKR'] / (1 + first_row['Actual_PKR_Devaluation'])
    pkr_cumulative_invested = usd_initial_principal * initial_pkr_rate
    pkr_real_principal_accumulated = usd_initial_principal * initial_pkr_rate
    
    # History Lists
    years_axis = [historical_records.index[0].date()]
    usd_nominal_with_z_hist = [usd_initial_principal]
    usd_real_with_z_hist = [usd_initial_principal]
    pkr_nominal_with_z_hist = [usd_initial_principal * initial_pkr_rate]
    pkr_real_portfolio_with_z_hist = [usd_initial_principal * initial_pkr_rate]
    
    usd_nominal_no_z_hist = [usd_initial_principal]
    usd_real_no_z_hist = [usd_initial_principal]
    pkr_nominal_no_z_hist = [usd_initial_principal * initial_pkr_rate]
    pkr_real_portfolio_no_z_hist = [usd_initial_principal * initial_pkr_rate]
    
    usd_real_principal_hist = [usd_initial_principal]
    pkr_real_principal_hist = [usd_initial_principal * initial_pkr_rate]
    
    usd_nominal_principal_hist = [usd_initial_principal]
    pkr_nominal_principal_hist = [usd_initial_principal * initial_pkr_rate]
    
    ref_ticker = buy_the_dip_config.get('reference_ticker', list(portfolio_config.keys())[0])
    ticker_price_hist = [first_row[ref_ticker] / (1 + first_row[f'{ref_ticker}_Growth_Rate'])]
    exch_rate_hist = [initial_pkr_rate]
    us_inf_hist = [0]
    pk_inf_hist = [0]
    contribution_multiplier_hist = [1.0]

    ath_price = ticker_price_hist[0]

    for idx, row in historical_records.iterrows():
        # 1. Update Macro Factors
        usd_inf_mo = row['Actual_USD_Inflation']
        pkr_inf_mo = row['Actual_PKR_Inflation']
        current_usd_to_pkr = row['Exchange_Rate_PKR']
        
        usd_cumulative_inflation_factor *= (1 + usd_inf_mo)
        pkr_cumulative_inflation_factor *= (1 + pkr_inf_mo)
        
        # 2. Portfolio Growth Calculation (Weighted)
        portfolio_growth = sum(row[f'{t}_Growth_Rate'] * weight for t, weight in portfolio_config.items())
        
        # 3. Buy the Dip Logic
        current_ref_price = row[ref_ticker]
        if current_ref_price > ath_price:
            ath_price = current_ref_price
        
        multiplier = 1.0
        if buy_the_dip_config['enabled']:
            dip_pct = (ath_price - current_ref_price) / ath_price
            if dip_pct >= buy_the_dip_config['threshold']:
                multiplier = buy_the_dip_config['multiplier']
        
        # 4. Contributions
        monthly_usd_invested = usd_monthly_contribution * multiplier
        # For simplicity, we assume annual contribution happens once a year (e.g., in December)
        annual_step = usd_annual_contribution / 12 if usd_annual_contribution > 0 else 0
        total_mo_invested = monthly_usd_invested + annual_step
        
        usd_cumulative_invested += total_mo_invested
        pkr_cumulative_invested += total_mo_invested * current_usd_to_pkr
        
        usd_real_principal_accumulated += total_mo_invested / usd_cumulative_inflation_factor
        pkr_real_principal_accumulated += (total_mo_invested * current_usd_to_pkr) / pkr_cumulative_inflation_factor
        
        # 5. Apply Growth and Add Capital
        usd_nominal_with_zakat = (usd_nominal_with_zakat * (1 + portfolio_growth)) + total_mo_invested
        usd_nominal_no_zakat = (usd_nominal_no_zakat * (1 + portfolio_growth)) + total_mo_invested
            
        # 6. Zakat (Annual - applied every December)
        if row.name.month == 12:
            annual_zakat = usd_nominal_with_zakat * zakat_rate
            usd_total_zakat_paid += annual_zakat
            usd_nominal_with_zakat -= annual_zakat
        
        # 7. Snapshots
        years_axis.append(idx.date())
        ticker_price_hist.append(current_ref_price)
        exch_rate_hist.append(current_usd_to_pkr)
        us_inf_hist.append(row['USD_Inf_Annual'] * 100) 
        pk_inf_hist.append(pkr_inf_mo * 100 * 12) # Annualized monthly
        contribution_multiplier_hist.append(multiplier)
        
        usd_nominal_with_z_hist.append(usd_nominal_with_zakat)
        usd_real_with_z_hist.append(usd_nominal_with_zakat / usd_cumulative_inflation_factor)
        pkr_nom_z = usd_nominal_with_zakat * current_usd_to_pkr
        pkr_nominal_with_z_hist.append(pkr_nom_z)
        pkr_real_portfolio_with_z_hist.append(pkr_nom_z / pkr_cumulative_inflation_factor)
        
        usd_nominal_no_z_hist.append(usd_nominal_no_zakat)
        usd_real_no_z_hist.append(usd_nominal_no_zakat / usd_cumulative_inflation_factor)
        pkr_nom_no_z = usd_nominal_no_zakat * current_usd_to_pkr
        pkr_nominal_no_z_hist.append(pkr_nom_no_z)
        pkr_real_portfolio_no_z_hist.append(pkr_nom_no_z / pkr_cumulative_inflation_factor)
        
        usd_real_principal_hist.append(usd_real_principal_accumulated)
        pkr_real_principal_hist.append(pkr_real_principal_accumulated)
        usd_nominal_principal_hist.append(usd_cumulative_invested)
        pkr_nominal_principal_hist.append(pkr_cumulative_invested)

    # Final Stats
    def safe_pct(final, initial): return (final / initial - 1) * 100 if initial > 0 else 0
    usd_nom_pct_z = safe_pct(usd_nominal_with_zakat, usd_cumulative_invested)
    usd_real_pct_z = safe_pct(usd_nominal_with_zakat / usd_cumulative_inflation_factor, usd_real_principal_accumulated)
    pkr_nom_pct_z = safe_pct(usd_nominal_with_zakat * current_usd_to_pkr, pkr_cumulative_invested)
    pkr_real_pct_z = safe_pct((usd_nominal_with_zakat * current_usd_to_pkr) / pkr_cumulative_inflation_factor, pkr_real_principal_accumulated)
    
    usd_nom_pct_no_z = safe_pct(usd_nominal_no_zakat, usd_cumulative_invested)
    usd_real_pct_no_z = safe_pct(usd_nominal_no_zakat / usd_cumulative_inflation_factor, usd_real_principal_accumulated)
    pkr_nom_pct_no_z = safe_pct(usd_nominal_no_zakat * current_usd_to_pkr, pkr_cumulative_invested)
    pkr_real_pct_no_z = safe_pct((usd_nominal_no_zakat * current_usd_to_pkr) / pkr_cumulative_inflation_factor, pkr_real_principal_accumulated)

    # --- PLOTLY ---
    fig = make_subplots(
        rows=5, cols=2,
        subplot_titles=(
            "PKR Nominal Balances", "USD Nominal Balances",
            "True Pakistan Purchasing Power", "True US Purchasing Power",
            f"Reference Asset ({ref_ticker}) Price History", "USD to PKR Exchange Rate",
            "Annual US Inflation %", "Annual Pakistan Inflation %",
            "Contribution Multiplier (Buy the Dip)", ""
        ),
        vertical_spacing=0.06, horizontal_spacing=0.1
    )

    def add_trace(x, y, name, row, col, color, dash=None, marker=None):
        fig.add_trace(go.Scatter(x=x, y=y, name=name, line=dict(color=color, width=2.5, dash=dash),
                                 mode='lines+markers' if marker else 'lines', marker=dict(symbol=marker) if marker else None,
                                 hovertemplate='%{y:,.2f}<extra></extra>'), row=row, col=col)

    add_trace(years_axis, pkr_nominal_with_z_hist, "S1: With Zakat (PKR Nom)", 1, 1, "#2ecc71")
    add_trace(years_axis, pkr_nominal_no_z_hist, "S2: No Zakat (PKR Nom)", 1, 1, "#27ae60", dash='dash')
    add_trace(years_axis, pkr_nominal_principal_hist, "Total PKR Invested (Nominal)", 1, 1, "#95a5a6", dash='dot')

    add_trace(years_axis, usd_nominal_with_z_hist, "S1: With Zakat (USD Nom)", 1, 2, "#3498db")
    add_trace(years_axis, usd_nominal_no_z_hist, "S2: No Zakat (USD Nom)", 1, 2, "#2980b9", dash='dash')
    add_trace(years_axis, usd_nominal_principal_hist, "Total USD Invested (Nominal)", 1, 2, "#7f8c8d", dash='dot')

    add_trace(years_axis, pkr_real_portfolio_with_z_hist, "S1: With Zakat (PKR Real)", 2, 1, "#e74c3c")
    add_trace(years_axis, pkr_real_portfolio_no_z_hist, "S2: No Zakat (PKR Real)", 2, 1, "#9b59b6", dash='dash')
    add_trace(years_axis, pkr_real_principal_hist, "Real Principal Value (PKR)", 2, 1, "#c0392b", dash='dot')

    add_trace(years_axis, usd_real_with_z_hist, "S1: With Zakat (USD Real)", 2, 2, "#e67e22")
    add_trace(years_axis, usd_real_no_z_hist, "S2: No Zakat (USD Real)", 2, 2, "#d35400", dash='dash')
    add_trace(years_axis, usd_real_principal_hist, "Real Principal Value (USD)", 2, 2, "#7f8c8d", dash='dot')

    add_trace(years_axis, ticker_price_hist, f"{ref_ticker} Price (USD)", 3, 1, "#34495e")
    add_trace(years_axis, exch_rate_hist, "Exchange Rate (USD/PKR)", 3, 2, "#8e44ad")
    
    add_trace(years_axis[1:], us_inf_hist[1:], "US Inflation %", 4, 1, "#e74c3c")
    add_trace(years_axis[1:], pk_inf_hist[1:], "PK Inflation %", 4, 2, "#f1c40f")
    
    add_trace(years_axis, contribution_multiplier_hist, "Multiplier", 5, 1, "#1abc9c", marker='circle')

    fig.update_layout(title_text=f"Strategic Dual-Currency Wealth Analytics", title_x=0.5, height=2500, template="plotly_white")

    # --- HTML ---
    portfolio_str = ", ".join([f"{t} ({w*100:.0f}%)" for t, w in portfolio_config.items()])
    strategy_desc = f"Buy-the-Dip: {buy_the_dip_config['multiplier']}x at -{buy_the_dip_config['threshold']*100:.0f}% drop" if buy_the_dip_config['enabled'] else "Standard Dollar-Cost Averaging"

    summary_html = f"""
    <html>
    <head><title>Strategic Wealth Report</title><style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 1400px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }}
        h1, h3 {{ color: #2c3e50; text-align: center; }}
        .params {{ background: #f8f9fa; padding: 20px; border-left: 5px solid #3498db; margin-bottom: 30px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; font-size: 0.95em; }}
        .metric-group {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .metric-card {{ background: #fff; padding: 20px; border-top: 4px solid #3498db; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .metric-card.pkr {{ border-top-color: #27ae60; }}
        .metric-card.zakat {{ border-top-color: #e74c3c; }}
        .scenario {{ background: #fff; padding: 25px; border: 1px solid #eee; border-radius: 10px; margin-bottom: 30px; }}
        .scenario h3 {{ text-align: left; color: #2980b9; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
        .sub {{ background: #fafafa; padding: 15px; border-radius: 6px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 10px; display: flex; justify-content: space-between; border-bottom: 1px dashed #ddd; padding-bottom: 5px; }}
        .pct {{ background: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
    </style></head>
    <body><div class="container">
        <h1>Strategic Wealth Analytics</h1>
        <p style="text-align:center; color:#666;">Simulation: {years_axis[1]} to {years_axis[-1]}</p>

        <div class="params">
            <div><b>Portfolio Mix:</b><br>{portfolio_str}</div>
            <div><b>Contribution Strategy:</b><br>{strategy_desc}<br>Base Monthly: ${usd_monthly_contribution:,.0f}</div>
            <div><b>Zakat Policy:</b><br>{zakat_rate*100:.2f}% Annual Rate</div>
        </div>

        <div class="metric-group">
            <div class="metric-card"><p>Total Invested (USD)</p><h2>${usd_cumulative_invested:,.0f}</h2></div>
            <div class="metric-card pkr"><p>Total Invested (PKR)</p><h2>{pkr_cumulative_invested:,.0f}</h2></div>
            <div class="metric-card"><p>Final Exch Rate</p><h2>{current_usd_to_pkr:,.1f}</h2></div>
            <div class="metric-card zakat"><p>Total Zakat Paid</p><h2>${usd_total_zakat_paid:,.0f}</h2></div>
        </div>

        <div class="scenario">
            <h3>Scenario 1: With Zakat (Halal Optimized)</h3>
            <div class="grid">
                <div class="sub"><b>US Dollar Universe</b><ul>
                    <li><span>Invested Capital (Real)</span> <span>${usd_real_principal_accumulated:,.2f}</span></li>
                    <li><span>Final Portfolio (Nominal)</span> <span>${usd_nominal_with_zakat:,.2f}</span></li>
                    <li><span>Nominal Increase</span> <span class="pct">{usd_nom_pct_z:+.1f}%</span></li>
                    <li><span>Final Buying Power (Real)</span> <span>{usd_nominal_with_zakat / usd_cumulative_inflation_factor:,.2f}</span></li>
                    <li><span>Real Increase</span> <span class="pct">{usd_real_pct_z:+.1f}%</span></li>
                </ul></div>
                <div class="sub"><b>Pakistan Rupee Universe</b><ul>
                    <li><span>Invested Capital (Real)</span> <span>{pkr_real_principal_accumulated:,.0f} PKR</span></li>
                    <li><span>Final Portfolio (Nominal)</span> <span>{usd_nominal_with_zakat * current_usd_to_pkr:,.0f} PKR</span></li>
                    <li><span>Nominal Increase</span> <span class="pct">{pkr_nom_pct_z:+.1f}%</span></li>
                    <li><span>Final Buying Power (Real)</span> <span>{(usd_nominal_with_zakat * current_usd_to_pkr) / pkr_cumulative_inflation_factor:,.0f} PKR</span></li>
                    <li><span>Real Increase</span> <span class="pct">{pkr_real_pct_z:+.1f}%</span></li>
                </ul></div>
            </div>
        </div>

        <div class="scenario">
            <h3>Scenario 2: Without Zakat (Conventional)</h3>
            <div class="grid">
                <div class="sub"><b>US Dollar Universe</b><ul>
                    <li><span>Invested Capital (Real)</span> <span>${usd_real_principal_accumulated:,.2f}</span></li>
                    <li><span>Final Portfolio (Nominal)</span> <span>${usd_nominal_no_zakat:,.2f}</span></li>
                    <li><span>Nominal Increase</span> <span class="pct">{usd_nom_pct_no_z:+.1f}%</span></li>
                    <li><span>Final Buying Power (Real)</span> <span>{usd_nominal_no_zakat / usd_cumulative_inflation_factor:,.2f}</span></li>
                    <li><span>Real Increase</span> <span class="pct">{usd_real_pct_no_z:+.1f}%</span></li>
                </ul></div>
                <div class="sub"><b>Pakistan Rupee Universe</b><ul>
                    <li><span>Invested Capital (Real)</span> <span>{pkr_real_principal_accumulated:,.0f} PKR</span></li>
                    <li><span>Final Portfolio (Nominal)</span> <span>{usd_nominal_no_zakat * current_usd_to_pkr:,.0f} PKR</span></li>
                    <li><span>Nominal Increase</span> <span class="pct">{pkr_nom_pct_no_z:+.1f}%</span></li>
                    <li><span>Final Buying Power (Real)</span> <span>{(usd_nominal_no_zakat * current_usd_to_pkr) / pkr_cumulative_inflation_factor:,.0f} PKR</span></li>
                    <li><span>Real Increase</span> <span class="pct">{pkr_real_pct_no_z:+.1f}%</span></li>
                </ul></div>
            </div>
        </div>

        <div class="chart-container">{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>
    </div></body></html>
    """
    with open("wealth_analytics_report_strategic.html", "w") as f:
        f.write(summary_html)
    print(f"\n[SUCCESS] Strategic Report generated ({years_axis[1]} to {years_axis[-1]})")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    # Strategy 2: Multi-Asset Mix (Must sum to 1.0)
    PORTFOLIO_CONFIG = {
        "SPUS": 1.0,  # S&P 500 Sharia Industry Exclusions (Growth)
        # "SPSK": 0.20   # Global Sukuk ETF (Stability/Cash Reserve)
    }
    
    # Strategy 1: Buy the Dip (Value Averaging)
    BUY_THE_DIP_CONFIG = {
        "enabled": True,
        "threshold": 0.20,       # 20% drop from All-Time High
        "multiplier": 2.0,        # Double contribution during dip
        "reference_ticker": "SPUS" # Monitor this ticker for dips
    }

    START_YEAR = 2019
    END_YEAR = 2025
    INITIAL_USD = 1000
    MONTHLY_BASE_USD = 150
    ZAKAT_RATE = 0.025
    
    # 1. Collect Data for all tickers
    tickers_to_fetch = list(PORTFOLIO_CONFIG.keys())
    records = collect_historical_data(tickers_to_fetch, START_YEAR, END_YEAR)
    
    # 2. Run Engine
    if not records.empty:
        run_historical_wealth_engine(
            historical_records=records,
            usd_initial_principal=INITIAL_USD,
            portfolio_config=PORTFOLIO_CONFIG,
            buy_the_dip_config=BUY_THE_DIP_CONFIG,
            usd_annual_contribution=0,
            usd_monthly_contribution=MONTHLY_BASE_USD,
            zakat_rate=ZAKAT_RATE
        )
