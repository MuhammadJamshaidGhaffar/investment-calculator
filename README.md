# Dual-Currency Wealth Analytics Engine

<img width="1548" height="590" alt="image" src="https://github.com/user-attachments/assets/f66ed9cc-39c1-4821-a89d-a2df9b339309" />

A sophisticated financial simulation tool designed to track wealth growth across two different currency universes (**USD** and **PKR**). This engine accounts for real-world economic factors like inflation, currency devaluation, and religious obligations (Zakat) to provide a true picture of purchasing power over time.

## 🚀 Features

- **Dual-Currency Tracking**: Simultaneously analyze your portfolio in US Dollars and Pakistani Rupees.
- **Inflation-Adjusted Metrics**: See your "Real Buying Power" in both the US and Pakistan markets.
- **Currency Devaluation Logic**: Models the long-term devaluation of PKR against USD.
- **Zakat Optimization**: Compares two scenarios (With Zakat vs. Without Zakat) to visualize the impact of charitable giving on long-term wealth.
- **Interactive Reports**: Generates a self-contained HTML report with interactive Plotly charts, hover analytics, and deep metric breakdowns.

## � Core Scripts

This engine consists of three primary scripts designed for different analysis needs:

1.  **`main.py`**: A **projection engine** that uses fixed annual growth and inflation rates to simulate future wealth growth over long horizons (e.g., 20-50 years).
2.  **`calculator_on_real_data.py`**: A **historical simulator** that fetches real market data from Yahoo Finance and historical inflation rates to backtest performance from a specific start year.
3.  **`calculator_on_real_data_2.py`**: An **enhanced historical simulator** with refined logic for tracking real vs. nominal gains and multi-currency principal accumulation.

## �📊 Visual Report Preview

_(Add your screenshots here to showcase the interactive report)_

<!--
<p align="center">
  <img src="path/to/your/screenshot1.png" width="45%" />
  <img src="path/to/your/screenshot2.png" width="45%" />
</p>
-->

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone <repo-url>
   cd "investment calculator"
   ```

2. **Set up virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### 📥 Data Setup (For Historical Simulators)
To use the historical calculators (`calculator_on_real_data.py` & `calculator_on_real_data_2.py`), you need to download the global inflation dataset:

1.  Go to the [World Bank Open Data](https://data.worldbank.org/) website.
2.  Search for: **"Inflation, consumer prices (annual %)"**.
3.  Choose the **CSV** download option.
4.  Unzip the file and move the large CSV (e.g., `API_FP.CPI.TOTL.ZG_DS2_en_csv_v2_...csv`) into this project folder.
5.  Ensure the filename matches the one referenced in the scripts.

## 📈 Usage

The main logic resides in `main.py`. You can customize the simulation parameters at the bottom of the file:

```python
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
```

### 1. Future Projections (`main.py`)
Run the projection engine for hypothetical future scenarios:
```bash
python3 main.py
```

### 2. Historical Backtesting (`calculator_on_real_data.py`)
Run the historical engine to see how an investment would have performed in the past using real market and inflation data:
```bash
python3 calculator_on_real_data.py
```

After execution, open `wealth_analytics_report.html` in your browser to view your personalized interactive dashboard.

## 🧪 Simulation Parameters

- **Growth Rate**: Your projected annual return (e.g., 10% for S&P 500).
- **Inflation Rates**: Annual inflation for both USD and PKR environments.
- **PKR Devaluation**: The expected annual drop in PKR value against the USD.
- **Zakat**: Fixed at 2.5% of the total portfolio value (deducted annually).

---

_Created for strategic financial planning and wealth visualization._
