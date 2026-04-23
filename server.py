"""
Finance MCP Server
Unified access to financial and macroeconomic data from:
- Yahoo Finance (equities, ETFs, indices)
- FRED (US macroeconomic series)
- BCRA (Argentine central bank data)
- World Bank (global development indicators)

Author: Tobias Robledo
"""

import os
from datetime import datetime, timedelta
from typing import Any

import httpx
import yfinance as yf
from fastmcp import FastMCP

# ============================================================
# SERVER INITIALIZATION
# ============================================================
mcp = FastMCP("finance-mcp")

# Environment variables
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Shared HTTP client config
HTTP_TIMEOUT = 30.0
USER_AGENT = "finance-mcp/1.0 (educational use)"


# ============================================================
# YAHOO FINANCE TOOLS
# ============================================================
@mcp.tool()
def yf_get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> dict[str, Any]:
    """
    Get historical price data for a stock, ETF, or index from Yahoo Finance.

    Args:
        ticker: Symbol (e.g., "AAPL", "SPY", "^GSPC", "YPFD.BA" for Argentine stocks)
        period: Time range. Options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: Data granularity. Options: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo

    Returns:
        Dict with dates, OHLCV data, and summary statistics.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return {"error": f"No data found for ticker {ticker}"}

        return {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "rows": len(hist),
            "start_date": hist.index[0].strftime("%Y-%m-%d"),
            "end_date": hist.index[-1].strftime("%Y-%m-%d"),
            "first_close": float(hist["Close"].iloc[0]),
            "last_close": float(hist["Close"].iloc[-1]),
            "pct_return": float((hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100),
            "max_price": float(hist["High"].max()),
            "min_price": float(hist["Low"].min()),
            "avg_volume": float(hist["Volume"].mean()),
            "data": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if row["Volume"] else 0,
                }
                for idx, row in hist.iterrows()
            ],
        }
    except Exception as e:
        return {"error": f"Failed to fetch {ticker}: {str(e)}"}


@mcp.tool()
def yf_get_fundamentals(ticker: str) -> dict[str, Any]:
    """
    Get company fundamentals from Yahoo Finance: valuation, profitability,
    financial health, and key metrics.

    Args:
        ticker: Stock symbol (e.g., "AAPL", "JPM", "KO")

    Returns:
        Dict with P/E, market cap, margins, debt ratios, dividend, etc.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "country": info.get("country", ""),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "recommendation": info.get("recommendationKey"),
            "target_mean_price": info.get("targetMeanPrice"),
        }
    except Exception as e:
        return {"error": f"Failed to fetch fundamentals for {ticker}: {str(e)}"}


# ============================================================
# FRED TOOLS (Federal Reserve Economic Data)
# ============================================================
@mcp.tool()
async def fred_get_series(
    series_id: str,
    observation_start: str = "2020-01-01",
    observation_end: str | None = None,
) -> dict[str, Any]:
    """
    Fetch a macroeconomic time series from FRED (Federal Reserve Economic Data).
    Requires FRED_API_KEY environment variable.

    Common series IDs:
        GDP: GDP, GDPC1 (real)
        Inflation: CPIAUCSL, CPILFESL (core)
        Unemployment: UNRATE
        Fed Funds Rate: FEDFUNDS, DFF
        10Y Treasury: DGS10
        VIX: VIXCLS
        USD Index: DTWEXBGS

    Args:
        series_id: FRED series identifier
        observation_start: Start date (YYYY-MM-DD)
        observation_end: End date (YYYY-MM-DD), defaults to today
    """
    if not FRED_API_KEY:
        return {
            "error": "FRED_API_KEY not configured. Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        }

    if observation_end is None:
        observation_end = datetime.now().strftime("%Y-%m-%d")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": observation_start,
        "observation_end": observation_end,
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            observations = data.get("observations", [])
            # Filter missing values marked as "."
            clean_obs = [
                {"date": obs["date"], "value": float(obs["value"])}
                for obs in observations
                if obs["value"] != "."
            ]

            if not clean_obs:
                return {"error": f"No valid observations for {series_id}"}

            values = [o["value"] for o in clean_obs]
            return {
                "series_id": series_id,
                "observations_count": len(clean_obs),
                "start_date": clean_obs[0]["date"],
                "end_date": clean_obs[-1]["date"],
                "first_value": clean_obs[0]["value"],
                "last_value": clean_obs[-1]["value"],
                "pct_change": ((values[-1] / values[0]) - 1) * 100 if values[0] != 0 else None,
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": sum(values) / len(values),
                "data": clean_obs,
            }
        except httpx.HTTPError as e:
            return {"error": f"FRED API error: {str(e)}"}


@mcp.tool()
async def fred_search_series(search_text: str, limit: int = 10) -> dict[str, Any]:
    """
    Search for FRED series by keyword. Useful when you don't know the exact series ID.

    Args:
        search_text: Keywords to search (e.g., "inflation", "unemployment argentina")
        limit: Max results to return
    """
    if not FRED_API_KEY:
        return {"error": "FRED_API_KEY not configured"}

    url = "https://api.stlouisfed.org/fred/series/search"
    params = {
        "search_text": search_text,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": limit,
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "query": search_text,
                "count": len(data.get("seriess", [])),
                "results": [
                    {
                        "id": s["id"],
                        "title": s["title"],
                        "frequency": s.get("frequency", ""),
                        "units": s.get("units", ""),
                        "start": s.get("observation_start", ""),
                        "end": s.get("observation_end", ""),
                    }
                    for s in data.get("seriess", [])
                ],
            }
        except httpx.HTTPError as e:
            return {"error": f"FRED search error: {str(e)}"}


# ============================================================
# BCRA TOOLS (Banco Central de la República Argentina)
# ============================================================
BCRA_BASE = "https://api.bcra.gob.ar"


@mcp.tool()
async def bcra_list_variables() -> dict[str, Any]:
    """
    List all available monetary variables from BCRA Principales Variables API.
    Returns variable IDs, descriptions, and latest values.
    Common variables: reservas, base monetaria, tipo de cambio, tasas.
    """
    url = f"{BCRA_BASE}/estadisticas/v3.0/monetarias"
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, verify=False) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return {
                "status": data.get("status"),
                "count": len(data.get("results", [])),
                "variables": [
                    {
                        "id": v.get("idVariable"),
                        "description": v.get("descripcion"),
                        "category": v.get("categoria"),
                        "latest_date": v.get("fecha"),
                        "latest_value": v.get("valor"),
                    }
                    for v in data.get("results", [])
                ],
            }
        except httpx.HTTPError as e:
            return {"error": f"BCRA API error: {str(e)}"}


@mcp.tool()
async def bcra_get_variable_history(
    variable_id: int,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Get historical values for a specific BCRA monetary variable.
    Use bcra_list_variables() first to find the variable_id you need.

    Args:
        variable_id: BCRA variable ID (integer)
        date_from: Start date YYYY-MM-DD (default: 1 year ago)
        date_to: End date YYYY-MM-DD (default: today)
    """
    if date_from is None:
        date_from = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if date_to is None:
        date_to = datetime.now().strftime("%Y-%m-%d")

    url = f"{BCRA_BASE}/estadisticas/v3.0/monetarias/{variable_id}"
    params = {"desde": date_from, "hasta": date_to, "limit": 3000}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, verify=False) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return {"error": f"No data for variable {variable_id}"}

            values = [float(r["valor"]) for r in results]
            return {
                "variable_id": variable_id,
                "count": len(results),
                "first_value": values[0],
                "last_value": values[-1],
                "pct_change": ((values[-1] / values[0]) - 1) * 100 if values[0] != 0 else None,
                "data": [
                    {"date": r["fecha"], "value": float(r["valor"])}
                    for r in results
                ],
            }
        except httpx.HTTPError as e:
            return {"error": f"BCRA API error: {str(e)}"}


@mcp.tool()
async def bcra_get_exchange_rates(
    currency: str = "USD",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """
    Get exchange rate history from BCRA Estadísticas Cambiarias API.

    Args:
        currency: ISO code (USD, EUR, BRL, etc.)
        date_from: YYYY-MM-DD (default: 90 days ago)
        date_to: YYYY-MM-DD (default: today)
    """
    if date_from is None:
        date_from = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if date_to is None:
        date_to = datetime.now().strftime("%Y-%m-%d")

    url = f"{BCRA_BASE}/estadisticascambiarias/v1.0/Cotizaciones/{currency}"
    params = {"fechadesde": date_from, "fechahasta": date_to}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, verify=False) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            # Flatten to simple list
            rates = []
            for r in results:
                for detail in r.get("detalle", []):
                    rates.append({
                        "date": r["fecha"],
                        "currency": detail.get("codigoMoneda"),
                        "description": detail.get("descripcion"),
                        "buy": detail.get("tipoCotizacion"),
                        "sell": detail.get("tipoPase"),
                    })

            return {
                "currency": currency,
                "date_from": date_from,
                "date_to": date_to,
                "count": len(rates),
                "data": rates,
            }
        except httpx.HTTPError as e:
            return {"error": f"BCRA exchange API error: {str(e)}"}


# ============================================================
# WORLD BANK TOOLS
# ============================================================
@mcp.tool()
async def worldbank_get_indicator(
    country_code: str,
    indicator: str,
    date_range: str = "2010:2024",
) -> dict[str, Any]:
    """
    Get World Bank indicator data for a country.

    Common indicators:
        NY.GDP.MKTP.CD - GDP (current USD)
        NY.GDP.MKTP.KD.ZG - GDP growth (%)
        FP.CPI.TOTL.ZG - Inflation, consumer prices (%)
        SL.UEM.TOTL.ZS - Unemployment (%)
        NE.EXP.GNFS.ZS - Exports of goods and services (% of GDP)
        GC.DOD.TOTL.GD.ZS - Central government debt (% of GDP)

    Args:
        country_code: ISO 3-letter code (ARG, USA, BRA, CHN, DEU, etc.)
        indicator: World Bank indicator code
        date_range: Format "YYYY:YYYY"
    """
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    params = {"format": "json", "date": date_range, "per_page": 200}
    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            # World Bank API returns [metadata, data]
            if not isinstance(data, list) or len(data) < 2:
                return {"error": "Unexpected World Bank response format"}

            observations = [
                {"year": int(d["date"]), "value": d["value"]}
                for d in data[1]
                if d.get("value") is not None
            ]
            observations.sort(key=lambda x: x["year"])

            if not observations:
                return {"error": f"No data for {country_code}/{indicator}"}

            values = [o["value"] for o in observations]
            return {
                "country": country_code,
                "indicator": indicator,
                "indicator_name": data[1][0].get("indicator", {}).get("value", ""),
                "count": len(observations),
                "first_value": values[0],
                "last_value": values[-1],
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": sum(values) / len(values),
                "data": observations,
            }
        except httpx.HTTPError as e:
            return {"error": f"World Bank API error: {str(e)}"}


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    # Run as HTTP server for remote access (Railway, Render, etc.)
    # Change to mcp.run() for stdio/local Claude Desktop
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
