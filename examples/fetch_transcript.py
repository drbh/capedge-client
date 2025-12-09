import os
from dotenv import load_dotenv
from capedge_client import CapEdgeClient
from bs4 import BeautifulSoup
import html

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")

# ticker = "SKYT"
# company_name = "SkyWater"

ticker = "RKLB"
company_name = "Rocket Lab"

def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    # Find company CIK
    print(f"Searching for {ticker}...")
    target_cik = client.find_company_cik(ticker)

    if not target_cik:
        print(f"Could not find {ticker}. Trying full name...")
        target_cik = client.find_company_cik(company_name)

    if not target_cik:
        print(f"Error: Could not find CIK for {ticker} or {company_name}")
        return

    print(f"Found {ticker} with CIK: {target_cik}")
    print()

    # Get transcripts for target CIK
    print(f"Fetching {ticker} transcripts...")
    result = client.get_company_transcripts(target_cik)

    if result["total"] == 0:
        print(f"No transcripts found for {ticker}")
        return

    print(f"Total transcripts available: {result['total']}")
    print()

    # Get the latest transcript
    latest = result["data"][0]
    print("Latest transcript:")
    print(f"  Title: {latest.title}")
    print(f"  Date: {latest.date[:10]}")
    print(f"  Quarter: Q{latest.quarter} {latest.year}")
    print(f"  Transcript URL: {latest.transcript_url}")
    print()

    # Fetch the transcript page and parse the HTML
    print("Fetching transcript content...")
    response = client.session.get(latest.transcript_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    print("\n" + "=" * 60)
    print("TRANSCRIPT CONTENT")
    print("=" * 60)

    # Find the Call transcript section
    # The transcript is in a grid layout with speaker names (h3) and their text (div with p tags)
    transcript_grid = soup.find("div", class_="r6o-annotatable")

    if transcript_grid:
        grid_div = transcript_grid.find("div", class_="grid")
        if grid_div:
            children = list(grid_div.children)
            i = 0
            while i < len(children):
                child = children[i]
                if child.name == "h3":
                    # Speaker name
                    speaker = child.get_text(strip=True)
                    print(f"\n[{speaker}]")
                    i += 1
                    # Next element should be the content div
                    if i < len(children):
                        content_div = children[i]
                        if content_div.name == "div":
                            paragraphs = content_div.find_all("p")
                            for p in paragraphs:
                                text = html.unescape(p.get_text())
                                print(text)
                                print()
                        i += 1
                else:
                    i += 1
    else:
        print("Could not find transcript content in the page")


if __name__ == "__main__":
    main()
