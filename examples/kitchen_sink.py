import os
from dotenv import load_dotenv
from capedge_client import CapEdgeClient

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")


def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    # Search for companies
    print("Searching for 'Tesla'...")
    companies = client.search_company("Tesla")
    for c in companies[:3]:
        print(f"  {c.name} ({c.ticker}) - CIK: {c.cik}")
    print()

    # Get latest transcripts
    print("Latest earnings transcripts:")
    result = client.get_transcripts(page=1)
    print(f"  Total available: {result['total']}")
    for t in result["data"][:5]:
        print(f"  - {t.ticker}: {t.title}")
    print()

    # Get transcripts for a specific company (Apple)
    print("Apple (AAPL) transcripts:")
    apple_cik = client.find_company_cik("AAPL")
    if apple_cik:
        result = client.get_company_transcripts(apple_cik)
        print(f"  Total: {result['total']}")
        for t in result["data"][:5]:
            print(f"  - {t.title} ({t.date[:10]})")


if __name__ == "__main__":
    main()
