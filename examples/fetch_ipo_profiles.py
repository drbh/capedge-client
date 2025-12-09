import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from capedge_client import CapEdgeClient

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")


@dataclass
class CompanyProfile:
    """Company profile data."""
    cik: int
    ticker: Optional[str]
    name: str
    description: str
    exchange: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    country: Optional[str]
    address: Optional[str]
    website: Optional[str]
    market_cap: Optional[float]
    price: Optional[float]
    pe_ratio: Optional[float]
    week_52_high: Optional[float]
    week_52_low: Optional[float]
    shares_outstanding: Optional[int]


def get_latest_ipos(client: CapEdgeClient, limit: int = 10) -> list:
    """Fetch latest IPO filings."""
    data = client._request("ipos/latest", params={"page": 1})
    filings = [
        {
            "cik": item.get("filer", {}).get("cik"),
            "name": item.get("filer", {}).get("name", ""),
            "form_type": item.get("type", ""),
            "is_follow_on": item.get("isFollowOn", False),
            "date": item.get("date", ""),
        }
        for item in data.get("data", [])
        if not item.get("isFollowOn", False)  # Only IPOs, not follow-ons
    ]
    return filings[:limit]


def get_company_ticker(client: CapEdgeClient, cik: int, name: str) -> Optional[str]:
    """Get ticker symbol by searching for company name."""
    try:
        # Use direct request with timeout instead of client method
        resp = client.session.get(
            "https://capedge.com/v1/api/search/company",
            params={"q": name},
            timeout=10
        )
        if resp.ok:
            data = resp.json()
            for item in data.get("data", []):
                # Match by CIK to ensure we get the right company
                if str(item.get("value")) == str(cik) and item.get("tradingSymbol"):
                    return item["tradingSymbol"]
                # Fallback: return first result with a ticker
                if item.get("tradingSymbol"):
                    return item["tradingSymbol"]
    except Exception:
        pass
    return None


def get_company_profile(client: CapEdgeClient, cik: int, ticker: str) -> Optional[CompanyProfile]:
    """Fetch company profile from realtime data endpoint."""
    try:
        url = f"https://capedge.com/company/{cik}/{ticker}/data/realtime"
        resp = client.session.get(url, timeout=10)
        if not resp.ok:
            return None

        data = resp.json()
        quote = data.get("quote", {}).get("data", {})
        stats = data.get("stats", {}).get("data", {})

        # Skip if no meaningful data
        if not stats.get("Name") and not stats.get("Description"):
            return None

        return CompanyProfile(
            cik=cik,
            ticker=ticker,
            name=stats.get("Name", ""),
            description=stats.get("Description", ""),
            exchange=stats.get("Exchange"),
            sector=stats.get("Sector"),
            industry=stats.get("Industry"),
            country=stats.get("Country"),
            address=stats.get("Address"),
            website=stats.get("OfficialSite"),
            market_cap=quote.get("marketCap"),
            price=quote.get("latestPrice"),
            pe_ratio=quote.get("peRatio"),
            week_52_high=stats.get("week52High"),
            week_52_low=stats.get("week52Low"),
            shares_outstanding=stats.get("sharesOutstanding"),
        )
    except Exception:
        return None


def format_market_cap(value: Optional[float]) -> str:
    """Format market cap as readable string."""
    if value is None:
        return "-"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def format_price(value: Optional[float]) -> str:
    """Format price."""
    if value is None:
        return "-"
    return f"${value:.2f}"


def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    # Set default timeout for all requests
    client.session.request = lambda method, url, **kwargs: client.session.__class__.request(
        client.session, method, url, timeout=kwargs.pop('timeout', 10), **kwargs
    )

    print("Fetching Recent IPO Company Profiles")
    print("=" * 80)
    print()

    # Get latest IPOs (not follow-ons)
    print("Fetching latest IPO filings...")
    ipos = get_latest_ipos(client, limit=20)
    print(f"Found {len(ipos)} recent IPO filings")
    print()

    profiles = []

    for ipo in ipos[:15]:  # Limit to 15 to avoid too many requests
        name = ipo["name"]
        cik = ipo["cik"]

        print(f"Looking up: {name[:50]}...", end=" ", flush=True)

        # Get ticker - use short name for better search results
        short_name = name.split(",")[0].split(" Inc")[0].split(" Corp")[0].strip()
        ticker = get_company_ticker(client, cik, short_name)
        if not ticker:
            # Try full name
            ticker = get_company_ticker(client, cik, name)
        if not ticker:
            print("(no ticker)")
            continue

        # Get profile
        profile = get_company_profile(client, cik, ticker)
        if profile:
            profiles.append(profile)
            print(f"OK ({ticker})")
        else:
            print(f"(no data for {ticker})")

    print()
    print("=" * 80)
    print("IPO COMPANY PROFILES")
    print("=" * 80)

    for p in profiles:
        print()
        print(f"{p.name}")
        print(f"  Ticker: {p.ticker} | Exchange: {p.exchange or '-'}")
        print(f"  Sector: {p.sector or '-'}")
        print(f"  Industry: {p.industry or '-'}")
        print()
        if p.description:
            desc = p.description[:200] + "..." if len(p.description) > 200 else p.description
            print(f"  {desc}")
            print()
        print(f"  Price: {format_price(p.price)}")
        print(f"  Market Cap: {format_market_cap(p.market_cap)}")
        print(f"  P/E Ratio: {p.pe_ratio if p.pe_ratio else '-'}")
        print(f"  52-Week Range: {format_price(p.week_52_low)} - {format_price(p.week_52_high)}")
        if p.website:
            print(f"  Website: {p.website}")
        if p.address:
            print(f"  Address: {p.address}")
        print("-" * 80)


if __name__ == "__main__":
    main()
