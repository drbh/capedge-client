"""
CapEdge API Client

A Python client for the CapEdge API (https://capedge.com/v1/api/)
for accessing SEC filings, earnings transcripts, and company data.

Note: This API requires authentication via session cookies from capedge.com.
"""

import requests
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class Transcript:
    """Earnings call transcript metadata."""
    id: str
    company_name: str
    cik: int
    ticker: str
    year: int
    quarter: int
    title: str
    date: str
    transcript_url: str
    exchange: Optional[str] = None
    market_cap: Optional[int] = None


@dataclass
class Company:
    """Company search result."""
    cik: str
    name: str
    ticker: Optional[str] = None


class CapEdgeClient:
    """
    Client for the CapEdge API.

    CapEdge provides access to SEC filings and earnings transcripts.

    Usage:
        # Initialize with cookies from a browser session
        cookies = {
            "__Host-authjs.csrf-token": "...",
            "__Secure-authjs.callback-url": "...",
            "sessionId": "...",
            "__Secure-authjs.session-token": "..."
        }
        client = CapEdgeClient(cookies)

        # Or use a cookie string
        client = CapEdgeClient.from_cookie_string("cookie1=value1; cookie2=value2")

        # Search for companies
        companies = client.search_company("Apple")

        # Get transcripts
        transcripts = client.get_transcripts(page=1)

        # Get transcripts for a specific company
        apple_transcripts = client.get_transcripts(page=1, company_id=320193)
    """

    BASE_URL = "https://capedge.com/v1/api/"

    def __init__(self, cookies: Dict[str, str]):
        """
        Initialize the CapEdge client.

        Args:
            cookies: Dictionary of session cookies from capedge.com
        """
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        })

    @classmethod
    def from_cookie_string(cls, cookie_string: str) -> "CapEdgeClient":
        """
        Create a client from a cookie string (as copied from browser DevTools).

        Args:
            cookie_string: Cookie header value (e.g., "name1=value1; name2=value2")

        Returns:
            CapEdgeClient instance
        """
        cookies = {}
        for item in cookie_string.split("; "):
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key] = value
        return cls(cookies)

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make a request to the API.

        Args:
            endpoint: API endpoint (relative to BASE_URL)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            requests.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        url = urljoin(self.BASE_URL, endpoint)
        response = self.session.get(url, params=params)
        response.raise_for_status()

        # Check if we got HTML instead of JSON (session expired)
        if response.text.startswith("<!DOCTYPE html>") or response.text.startswith("<html"):
            raise ValueError(
                "Session expired or invalid. Please update your cookies. "
                "Response was HTML instead of JSON."
            )

        return response.json()

    # === Company Search ===

    def search_company(self, query: str) -> List[Company]:
        """
        Search for companies by name or ticker.

        Args:
            query: Search query (company name or ticker symbol)

        Returns:
            List of matching companies

        Example:
            >>> companies = client.search_company("Apple")
            >>> for c in companies:
            ...     print(f"{c.name} ({c.ticker}) - CIK: {c.cik}")
        """
        data = self._request("search/company", params={"q": query})
        return [
            Company(
                cik=item["value"],
                name=item["label"],
                ticker=item.get("tradingSymbol")
            )
            for item in data.get("data", [])
        ]

    # === Transcripts ===

    def get_transcripts(
        self,
        page: int = 1,
        company_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get earnings call transcripts.

        Args:
            page: Page number (1-indexed)
            company_id: Optional CIK to filter by company

        Returns:
            Dictionary with 'total' count and 'data' list of transcripts

        Example:
            >>> result = client.get_transcripts(page=1)
            >>> print(f"Total: {result['total']}")
            >>> for t in result['data']:
            ...     print(f"{t.ticker} Q{t.quarter} {t.year}")
        """
        params = {"page": page}
        if company_id:
            params["companyId"] = company_id

        data = self._request("transcripts", params=params)

        transcripts = []
        for item in data.get("data", []):
            transcripts.append(Transcript(
                id=item["id"],
                company_name=item["company"]["name"],
                cik=item["company"]["cik"],
                ticker=item.get("ticker", ""),
                year=item["year"],
                quarter=item["quarter"],
                title=item["title"],
                date=item["date"],
                transcript_url=item["transcriptUrl"],
                exchange=item.get("exchange"),
                market_cap=item.get("marketCap")
            ))

        return {
            "total": data.get("total", 0),
            "data": transcripts
        }

    def get_company_transcripts(self, cik: int, page: int = 1) -> Dict[str, Any]:
        """
        Get all transcripts for a specific company.

        Args:
            cik: Company CIK number
            page: Page number (1-indexed)

        Returns:
            Dictionary with 'total' count and 'data' list of transcripts

        Example:
            >>> # Get Apple transcripts (CIK: 320193)
            >>> result = client.get_company_transcripts(320193)
        """
        return self.get_transcripts(page=page, company_id=cik)

    # === Convenience Methods ===

    def get_latest_transcripts(self, limit: int = 10) -> List[Transcript]:
        """
        Get the most recent earnings call transcripts.

        Args:
            limit: Maximum number of transcripts to return

        Returns:
            List of recent transcripts
        """
        result = self.get_transcripts(page=1)
        return result["data"][:limit]

    def find_company_cik(self, name_or_ticker: str) -> Optional[int]:
        """
        Find a company's CIK by name or ticker.

        Args:
            name_or_ticker: Company name or ticker symbol

        Returns:
            CIK number if found, None otherwise

        Example:
            >>> cik = client.find_company_cik("AAPL")
            >>> print(cik)  # 320193
        """
        companies = self.search_company(name_or_ticker)
        if companies:
            return int(companies[0].cik)
        return None


# === Example Usage ===

if __name__ == "__main__":
    # Example cookie string (replace with your own from browser DevTools)
    COOKIE_STRING = """__Host-authjs.csrf-token=YOUR_TOKEN; __Secure-authjs.callback-url=https%3A%2F%2Fcapedge.com; sessionId=YOUR_SESSION_ID; __Secure-authjs.session-token=YOUR_SESSION_TOKEN"""

    # Create client
    client = CapEdgeClient.from_cookie_string(COOKIE_STRING)

    print("=== CapEdge API Client Demo ===\n")

    # Search for companies
    print("1. Searching for 'Apple'...")
    try:
        companies = client.search_company("Apple")
        for company in companies[:3]:
            print(f"   - {company.name} ({company.ticker}) - CIK: {company.cik}")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Get latest transcripts
    print("2. Getting latest transcripts...")
    try:
        result = client.get_transcripts(page=1)
        print(f"   Total transcripts available: {result['total']}")
        for t in result['data'][:5]:
            print(f"   - {t.ticker}: {t.title} ({t.date[:10]})")
    except Exception as e:
        print(f"   Error: {e}")

    print()

    # Get company-specific transcripts
    print("3. Getting Apple (CIK: 320193) transcripts...")
    try:
        result = client.get_company_transcripts(320193)
        print(f"   Total Apple transcripts: {result['total']}")
        for t in result['data'][:3]:
            print(f"   - {t.title} ({t.date[:10]})")
    except Exception as e:
        print(f"   Error: {e}")
