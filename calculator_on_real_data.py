import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import numpy as np

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

def collect_historical_data(ticker, start_year, end_year):
    print(f"Fetching historical market data for {ticker} from {start_year} to {end_year}...")
    
    try:
        stock_raw = yf.download(ticker, start=f"{start_year-1}-12-01", end=f"{end_year}-12-31", auto_adjust=True)
        pkr_raw = yf.download("USDPKR=X", start=f"{start_year-1}-12-01", end=f"{end_year}-12-31", auto_adjust=True)
        
        if stock_raw.empty:
            print(f"Error: No data found for ticker {ticker}.")
            return pd.DataFrame()

        if isinstance(stock_raw.columns, pd.MultiIndex):
            stock_data = stock_raw['Close'][ticker]
        else:
            stock_data = stock_raw['Close']

        if isinstance(pkr_raw.columns, pd.MultiIndex):
            pkr_data = pkr_raw['Close']['USDPKR=X']
        else:
            pkr_data = pkr_raw['Close']
            
        stock_annual = stock_data.resample('YE').last()
        pkr_annual = pkr_data.resample('YE').last()
        
        history_df = pd.DataFrame(index=stock_annual.index)
        history_df['Stock_Price_USD'] = stock_annual.values
        history_df['Exchange_Rate_PKR'] = pkr_annual.reindex(history_df.index, method='ffill').values
        
        history_df['Actual_Growth_Rate'] = history_df['Stock_Price_USD'].pct_change()
        history_df['Actual_PKR_Devaluation'] = history_df['Exchange_Rate_PKR'].pct_change()
        
        us_inf_map, pk_inflation_map = get_inflation_data()
        history_df['Year'] = history_df.index.year
        history_df['Actual_USD_Inflation'] = history_df['Year'].map(us_inf_map)
        history_df['Actual_PKR_Inflation'] = history_df['Year'].map(pk_inflation_map)
        
        history_df = history_df[history_df['Year'] >= start_year].dropna(subset=['Actual_Growth_Rate'])
        
        if history_df.empty:
            print("Warning: Historical range resulted in empty dataset.")
            return pd.DataFrame()

        history_df['Actual_USD_Inflation'] = history_df['Actual_USD_Inflation'].ffill().bfill().fillna(0.03)
        history_df['Actual_PKR_Inflation'] = history_df['Actual_PKR_Inflation'].ffill().bfill().fillna(0.09)
        
        return history_df
    except Exception as e:
        print(f"Error collecting data: {e}")
        return pd.DataFrame()

def run_historical_wealth_engine(
    historical_records,
    usd_initial_principal,
    usd_annual_contribution=0,
    usd_monthly_contribution=0,
    zakat_rate=0.025,
    ticker="STOCK"
):
    if historical_records.empty:
        print("No historical data available to run simulation.")
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
    years_axis = [int(first_row['Year']) - 1]
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
    
    ticker_price_hist = [first_row['Stock_Price_USD'] / (1 + first_row['Actual_Growth_Rate'])]
    exch_rate_hist = [initial_pkr_rate]
    us_inf_hist = [0] # Starting point placeholder
    pk_inf_hist = [0] # Starting point placeholder

    for idx, row in historical_records.iterrows():
        year = int(row['Year'])
        growth_rate = row['Actual_Growth_Rate']
        usd_inf = row['Actual_USD_Inflation']
        pkr_inf = row['Actual_PKR_Inflation']
        current_usd_to_pkr = row['Exchange_Rate_PKR']
        
        usd_cumulative_inflation_factor *= (1 + usd_inf)
        pkr_cumulative_inflation_factor *= (1 + pkr_inf)
        
        # Contributions
        year_usd_invested = (usd_monthly_contribution * 12) + usd_annual_contribution
        usd_cumulative_invested += year_usd_invested
        pkr_cumulative_invested += year_usd_invested * current_usd_to_pkr
        
        usd_real_principal_accumulated += year_usd_invested / usd_cumulative_inflation_factor
        pkr_real_principal_accumulated += (year_usd_invested * current_usd_to_pkr) / pkr_cumulative_inflation_factor
        
        # Portfolio Growth
        if usd_monthly_contribution > 0:
            monthly_growth = (1 + growth_rate) ** (1/12) - 1
            for _ in range(12):
                usd_nominal_with_zakat = (usd_nominal_with_zakat * (1 + monthly_growth)) + usd_monthly_contribution
                usd_nominal_no_zakat = (usd_nominal_no_zakat * (1 + monthly_growth)) + usd_monthly_contribution
            usd_nominal_with_zakat += usd_annual_contribution
            usd_nominal_no_zakat += usd_annual_contribution
        else:
            usd_nominal_with_zakat = usd_nominal_with_zakat * (1 + growth_rate) + usd_annual_contribution
            usd_nominal_no_zakat = usd_nominal_no_zakat * (1 + growth_rate) + usd_annual_contribution
            
        # Zakat
        annual_zakat = usd_nominal_with_zakat * zakat_rate
        usd_total_zakat_paid += annual_zakat
        usd_nominal_with_zakat -= annual_zakat
        
        # Snapshots
        years_axis.append(year)
        ticker_price_hist.append(row['Stock_Price_USD'])
        exch_rate_hist.append(current_usd_to_pkr)
        us_inf_hist.append(usd_inf * 100) # percentage
        pk_inf_hist.append(pkr_inf * 100) # percentage
        
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

    # Growth percentages
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
        rows=4, cols=2,
        subplot_titles=(
            "PKR Nominal Balances", "USD Nominal Balances",
            "True Pakistan Purchasing Power", "True US Purchasing Power",
            f"{ticker} Price History (USD)", "USD to PKR Exchange Rate",
            "Annual US Inflation %", "Annual Pakistan Inflation %"
        ),
        vertical_spacing=0.08, horizontal_spacing=0.1
    )

    def add_trace(x, y, name, row, col, color, dash=None, marker=None):
        fig.add_trace(go.Scatter(x=x, y=y, name=name, line=dict(color=color, width=2.5, dash=dash),
                                 mode='lines+markers' if marker else 'lines', marker=dict(symbol=marker) if marker else None,
                                 hovertemplate='%{y:,.2f}<extra></extra>'), row=row, col=col)

    add_trace(years_axis, pkr_nominal_with_z_hist, "S1: With Zakat (PKR Nom)", 1, 1, "#2ecc71", marker='circle')
    add_trace(years_axis, pkr_nominal_no_z_hist, "S2: No Zakat (PKR Nom)", 1, 1, "#27ae60", dash='dash', marker='x')
    add_trace(years_axis, pkr_nominal_principal_hist, "Total PKR Invested (Nominal)", 1, 1, "#95a5a6", dash='dot')

    add_trace(years_axis, usd_nominal_with_z_hist, "S1: With Zakat (USD Nom)", 1, 2, "#3498db", marker='circle')
    add_trace(years_axis, usd_nominal_no_z_hist, "S2: No Zakat (USD Nom)", 1, 2, "#2980b9", dash='dash', marker='x')
    add_trace(years_axis, usd_nominal_principal_hist, "Total USD Invested (Nominal)", 1, 2, "#7f8c8d", dash='dot')

    add_trace(years_axis, pkr_real_portfolio_with_z_hist, "S1: With Zakat (PKR Real)", 2, 1, "#e74c3c", marker='square')
    add_trace(years_axis, pkr_real_portfolio_no_z_hist, "S2: No Zakat (PKR Real)", 2, 1, "#9b59b6", dash='dash', marker='triangle-up')
    add_trace(years_axis, pkr_real_principal_hist, "Real Principal Value (PKR)", 2, 1, "#c0392b", dash='dot')

    add_trace(years_axis, usd_real_with_z_hist, "S1: With Zakat (USD Real)", 2, 2, "#e67e22", marker='square')
    add_trace(years_axis, usd_real_no_z_hist, "S2: No Zakat (USD Real)", 2, 2, "#d35400", dash='dash', marker='triangle-up')
    add_trace(years_axis, usd_real_principal_hist, "Real Principal Value (USD)", 2, 2, "#7f8c8d", dash='dot')

    add_trace(years_axis, ticker_price_hist, f"{ticker} Price (USD)", 3, 1, "#34495e")
    add_trace(years_axis, exch_rate_hist, "Exchange Rate (USD/PKR)", 3, 2, "#8e44ad")
    
    # Inflation charts (excluding Year 0 placeholder)
    add_trace(years_axis[1:], us_inf_hist[1:], "US Inflation %", 4, 1, "#e74c3c", marker='circle')
    add_trace(years_axis[1:], pk_inf_hist[1:], "PK Inflation %", 4, 2, "#f1c40f", marker='circle')

    fig.update_layout(title_text=f"Historical Dual-Currency Wealth Analytics: {ticker}", title_x=0.5, height=2000, template="plotly_white")

    avg_growth = historical_records['Actual_Growth_Rate'].mean()
    avg_us_inf = historical_records['Actual_USD_Inflation'].mean()
    avg_pk_inf = historical_records['Actual_PKR_Inflation'].mean()

    # --- HTML ---
    summary_html = f"""
    <html>
    <head><title>Historical Wealth Report</title><style>
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
        <h1>Historical Wealth Analytics: {ticker}</h1>
        <p style="text-align:center; color:#666;">Simulation Period: {years_axis[1]} to {years_axis[-1]}</p>

        <div class="params">
            <div><b>Financials:</b><br>• Initial: ${usd_initial_principal:,.0f}<br>• Monthly: ${usd_monthly_contribution:,.0f}</div>
            <div><b>Performance ({ticker}):</b><br>• Avg Growth: {avg_growth*100:.1f}%<br>• Zakat Rate: {zakat_rate*100:.2f}%</div>
            <div><b>Macro Indicators:</b><br>• Avg US Inf: {avg_us_inf*100:.1f}%<br>• Avg PK Inf: {avg_pk_inf*100:.1f}%</div>
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
    with open("wealth_analytics_report.html", "w") as f:
        f.write(summary_html)
    print(f"\n[SUCCESS] Final Report generated for {ticker} ({years_axis[1]}-{years_axis[-1]})")

if __name__ == "__main__":
    # TICKER = "SPUS"
    # TICKER = "NVDA"
    TICKER = "^GSPC"
    START_YEAR = 1970
    END_YEAR = 2026
    INITIAL_USD = 0
    MONTHLY_USD = 300
    ZAKAT_RATE = 0.025
    
    records = collect_historical_data(TICKER, START_YEAR, END_YEAR)
    if not records.empty:
        run_historical_wealth_engine(records, INITIAL_USD, 0, MONTHLY_USD, ZAKAT_RATE, TICKER)
