import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from capedge_client import CapEdgeClient

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")


@dataclass
class IPOFiling:
    """IPO/Follow-On registration filing."""
    id: str
    form_type: str
    filename: str
    date: str
    cik: int
    company_name: str
    is_follow_on: bool


def get_latest_ipos(client: CapEdgeClient, page: int = 1, limit: int = 100) -> Dict[str, Any]:
    """Fetch latest IPO filings from the API."""
    data = client._request("ipos/latest", params={"page": page, "limit": limit})

    filings = []
    for item in data.get("data", []):
        filings.append(IPOFiling(
            id=item.get("id", ""),
            form_type=item.get("type", ""),
            filename=item.get("filename", ""),
            date=item.get("date", ""),
            cik=item.get("filer", {}).get("cik"),
            company_name=item.get("filer", {}).get("name", ""),
            is_follow_on=item.get("isFollowOn", False),
        ))

    return {
        "total": data.get("total", 0),
        "data": filings,
    }


def format_date(iso_date: str) -> str:
    """Format ISO date to readable format."""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except:
        return iso_date[:10] if iso_date else "-"


def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    print("Latest IPO & Follow-On Filings")
    print("=" * 90)
    print()

    result = get_latest_ipos(client, page=1, limit=50)
    print(f"Total filings: {result['total']}")
    print()

    print(f"{'Form':<10} {'Type':<12} {'Date':<14} {'CIK':<12} {'Company'}")
    print("-" * 90)

    for filing in result["data"]:
        reg_type = "Follow-On" if filing.is_follow_on else "IPO"
        date = format_date(filing.date)
        company = filing.company_name[:38] if len(filing.company_name) > 38 else filing.company_name
        print(f"{filing.form_type:<10} {reg_type:<12} {date:<14} {filing.cik:<12} {company}")


if __name__ == "__main__":
    main()
