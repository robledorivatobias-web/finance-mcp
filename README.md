# Finance MCP Server

Unified MCP server providing Claude with access to financial and macroeconomic data from Yahoo Finance, FRED, BCRA (Argentina), and the World Bank.

## Features

- **Yahoo Finance**: Stock/ETF price history, fundamentals, valuation metrics
- **FRED**: US macroeconomic time series (GDP, CPI, Fed Funds, Treasury yields, etc.)
- **BCRA**: Argentine monetary variables and exchange rates
- **World Bank**: Global development indicators for any country

## Prerequisites

- Python 3.10 or higher
- A free FRED API key ([get one here](https://fred.stlouisfed.org/docs/api/api_key.html))
- Claude Pro, Max, Team, or Enterprise plan (for custom MCP support)
- A Railway or Render account (both offer free tiers)
- A GitHub account

## Project Structure

```
finance-mcp/
├── server.py           # Main MCP server with all tools
├── requirements.txt    # Python dependencies
├── railway.toml        # Railway deployment config
├── .env.example        # Environment variables template
├── .gitignore
└── README.md
```

## Local Testing

1. Clone or download this project and `cd` into it.

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy the environment template and add your FRED API key:

```bash
cp .env.example .env
# Edit .env and paste your FRED_API_KEY
```

4. Run the server locally:

```bash
export FRED_API_KEY="your_key_here"
python server.py
```

The server will start on `http://localhost:8000`.

5. Test with MCP Inspector (optional):

```bash
npx @modelcontextprotocol/inspector http://localhost:8000
```

## Deployment to Railway (Free Hosting)

Railway gives you $5/month in free credits, more than enough for this server.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Finance MCP server"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/finance-mcp.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `finance-mcp` repository
4. Railway will auto-detect Python and start building
5. Go to the **Variables** tab and add:
   - `FRED_API_KEY` = your FRED API key
6. Go to **Settings** → **Networking** → click **Generate Domain**
7. Copy the generated URL (something like `your-app.up.railway.app`)

### Step 3: Connect to Claude

1. Open Claude at [claude.ai](https://claude.ai)
2. Go to **Settings** → **Connectors** → **Add custom connector**
3. Paste your Railway URL followed by `/mcp` (e.g., `https://your-app.up.railway.app/mcp`)
4. Give it a name like "Finance Data"
5. Enable it

Claude will now have access to all the tools in this server.

## Available Tools

### Yahoo Finance
- `yf_get_price_history(ticker, period, interval)` - Historical OHLCV data
- `yf_get_fundamentals(ticker)` - Valuation and financial health metrics

### FRED
- `fred_get_series(series_id, observation_start, observation_end)` - Time series data
- `fred_search_series(search_text, limit)` - Search for series by keyword

### BCRA
- `bcra_list_variables()` - List all available monetary variables
- `bcra_get_variable_history(variable_id, date_from, date_to)` - Historical values
- `bcra_get_exchange_rates(currency, date_from, date_to)` - Exchange rate history

### World Bank
- `worldbank_get_indicator(country_code, indicator, date_range)` - Country-level indicators

## Example Queries (Once Connected to Claude)

Once the server is connected, you can ask Claude things like:

- "Get me Apple's price history for the last year and calculate its annualized volatility"
- "Compare the P/E ratios of JPM, BAC, and C"
- "Pull the 10-year Treasury yield from FRED since 2020 and plot it"
- "What are BCRA's international reserves over the last 6 months?"
- "Compare Argentina's inflation rate with Brazil's using World Bank data"
- "Get the USD/ARS official exchange rate for the last 90 days"

## FRED Series Cheat Sheet

| Series ID | Description |
|-----------|-------------|
| GDP | US Nominal GDP |
| GDPC1 | US Real GDP |
| CPIAUCSL | Consumer Price Index |
| CPILFESL | Core CPI |
| UNRATE | US Unemployment Rate |
| FEDFUNDS | Federal Funds Rate |
| DGS10 | 10-Year Treasury Yield |
| DGS2 | 2-Year Treasury Yield |
| T10Y2Y | 10Y-2Y Spread (recession signal) |
| VIXCLS | VIX Volatility Index |
| DTWEXBGS | Trade-Weighted Dollar Index |
| M2SL | M2 Money Supply |

## World Bank Indicator Cheat Sheet

| Indicator | Description |
|-----------|-------------|
| NY.GDP.MKTP.CD | GDP (current USD) |
| NY.GDP.MKTP.KD.ZG | GDP growth (%) |
| NY.GDP.PCAP.CD | GDP per capita (USD) |
| FP.CPI.TOTL.ZG | Inflation (%) |
| SL.UEM.TOTL.ZS | Unemployment (%) |
| GC.DOD.TOTL.GD.ZS | Government debt (% GDP) |
| BN.CAB.XOKA.GD.ZS | Current account balance (% GDP) |
| NE.EXP.GNFS.ZS | Exports (% GDP) |

## Country Codes (World Bank)

Argentina: ARG, USA: USA, Brazil: BRA, Chile: CHL, China: CHN, Germany: DEU, Japan: JPN, United Kingdom: GBR, Mexico: MEX, Spain: ESP

## Troubleshooting

**Server won't start locally**: Make sure Python 3.10+ is installed (`python --version`) and dependencies are in a venv.

**BCRA returns SSL errors**: The code disables SSL verification for BCRA's API because their cert is sometimes outdated. This is known behavior.

**FRED returns "API key not configured"**: Make sure you've set `FRED_API_KEY` either in `.env` for local or as a Railway variable for deployment.

**Claude doesn't see the connector**: Make sure the URL ends with `/mcp`. Restart the Claude session after adding.

## License

MIT - Educational project by Tobias Robledo
