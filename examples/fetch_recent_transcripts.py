import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html

from capedge_client import CapEdgeClient

load_dotenv()

COOKIES = os.getenv("CAPEDGE_COOKIES")
if not COOKIES:
    raise ValueError("CAPEDGE_COOKIES not found in environment. Please set it in .env file.")

OUTPUT_DIR = Path("transcripts")


def parse_transcript_html(html_content: str) -> str:
    """Parse transcript HTML and return formatted text."""
    soup = BeautifulSoup(html_content, "html.parser")
    lines = []

    transcript_grid = soup.find("div", class_="r6o-annotatable")
    if not transcript_grid:
        return ""

    grid_div = transcript_grid.find("div", class_="grid")
    if not grid_div:
        return ""

    children = list(grid_div.children)
    i = 0
    while i < len(children):
        child = children[i]
        if child.name == "h3":
            speaker = child.get_text(strip=True)
            lines.append(f"\n[{speaker}]\n")
            i += 1
            if i < len(children):
                content_div = children[i]
                if content_div.name == "div":
                    paragraphs = content_div.find_all("p")
                    for p in paragraphs:
                        text = html.unescape(p.get_text())
                        lines.append(text)
                i += 1
        else:
            i += 1

    return "\n".join(lines)


def main():
    client = CapEdgeClient.from_cookie_string(COOKIES)

    OUTPUT_DIR.mkdir(exist_ok=True)

    cutoff = datetime.now() - timedelta(hours=24)
    print(f"Fetching transcripts from the last 24 hours (since {cutoff.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    print()

    result = client.get_transcripts(page=1)
    recent = []

    for t in result["data"]:
        transcript_date = datetime.fromisoformat(t.date.replace("Z", "+00:00"))
        if transcript_date.replace(tzinfo=None) >= cutoff:
            recent.append(t)

    if not recent:
        print("No transcripts found in the last 24 hours.")
        return

    print(f"Found {len(recent)} transcripts in the last 24 hours:")
    print()

    for t in recent:
        print(f"  {t.ticker:6} | {t.date[:10]} | Q{t.quarter} {t.year} | {t.company_name}")

    print()
    print("Fetching and saving transcripts...")
    print()

    for t in recent:
        filename = f"{t.ticker}_{t.year}_Q{t.quarter}.txt"
        filepath = OUTPUT_DIR / filename

        print(f"  Fetching {t.ticker} Q{t.quarter} {t.year}...", end=" ", flush=True)

        try:
            response = client.session.get(t.transcript_url)
            response.raise_for_status()

            transcript_text = parse_transcript_html(response.text)

            if not transcript_text:
                print("SKIP (no content)")
                continue

            header = f"""{t.company_name} ({t.ticker})
{t.title}
Date: {t.date[:10]}
Quarter: Q{t.quarter} {t.year}
{'=' * 60}
"""
            with open(filepath, "w") as f:
                f.write(header)
                f.write(transcript_text)

            print(f"OK -> {filepath}")

        except Exception as e:
            print(f"ERROR ({e})")

    print()
    print(f"Done. Transcripts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
