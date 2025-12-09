# capedge-client

Python client for the CapEdge API. Access SEC filings and earnings call transcripts.

## Install

```bash
uv add git+https://github.com/drbh/capedge-client.git
```

## Setup

Create a `.env` file with your CapEdge session cookies:

```
CAPEDGE_COOKIES="your-cookie-string-here"
```

To get your cookies, log in to [capedge.com](https://capedge.com), open DevTools, and copy the cookie header from any API request.

## Usage

```python
from dotenv import load_dotenv
from capedge_client import CapEdgeClient
import os

load_dotenv()
client = CapEdgeClient.from_cookie_string(os.getenv("CAPEDGE_COOKIES"))

# search for a company
companies = client.search_company("Tesla")
print(companies[0].name, companies[0].ticker, companies[0].cik)

# get latest transcripts
result = client.get_transcripts(page=1)
for t in result["data"][:5]:
    print(f"{t.ticker}: {t.title}")

# get transcripts for a specific company
cik = client.find_company_cik("AAPL")
result = client.get_company_transcripts(cik)
for t in result["data"][:3]:
    print(f"{t.title} ({t.date[:10]})")
```

## Examples

See the `examples/` directory:

- `kitchen_sink.py` - general API usage
- `list_latest_transcripts.py` - list recent earnings calls
- `fetch_skyt_transcript.py` - fetch and parse a full earnings call transcript
- `fetch_recent_transcripts.py` - fetch all transcripts from the last 24 hours and save to files

```bash
uv run examples/kitchen_sink.py
uv run examples/list_latest_transcripts.py
uv run examples/fetch_skyt_transcript.py
uv run examples/fetch_recent_transcripts.py
```

## API

### CapEdgeClient

| Method | Description |
|--------|-------------|
| `search_company(query)` | Search companies by name or ticker |
| `get_transcripts(page, company_id)` | Get earnings call transcripts |
| `get_company_transcripts(cik, page)` | Get transcripts for a specific company |
| `get_latest_transcripts(limit)` | Get most recent transcripts |
| `find_company_cik(name_or_ticker)` | Find a company's CIK number |

### Data Classes

**Company**: `cik`, `name`, `ticker`

**Transcript**: `id`, `company_name`, `cik`, `ticker`, `year`, `quarter`, `title`, `date`, `transcript_url`, `exchange`, `market_cap`
