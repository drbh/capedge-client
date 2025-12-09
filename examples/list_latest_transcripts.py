import os
from dotenv import load_dotenv
from capedge_client import CapEdgeClient

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")


def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    print("Latest Earnings Call Transcripts")
    print("=" * 60)
    print()

    result = client.get_transcripts(page=1)
    print(f"Total available: {result['total']}")
    print()

    for t in result["data"][:20]:
        print(f"{t.ticker:6} | {t.date[:10]} | Q{t.quarter} {t.year} | {t.company_name}")


if __name__ == "__main__":
    main()
