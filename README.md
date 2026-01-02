# doj-epstein-pdf-scraper

Grabs the .PDF URLs from the DOJ Epstein disclosures and stores them in a `.txt` document for use.

## Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Usage

Run the scraper with the default DOJ dataset 8 base URL:

```bash
python scrape_pdfs.py
```

Key options:

- `--dataset 1` through `--dataset 8` to target a specific DOJ dataset page.
- `--base-url <url>` to scrape any paginated listing URL (overrides `--dataset`).
- `--max-pages <num>` and `--delay <seconds>` to tune pagination and pacing.
- `--output <path>` to change the output file (default: `pdf_links.txt`).
- `--headless` to run Chromium without a visible browser window.

The script will write the collected PDF links (one per line) to the specified output file.
