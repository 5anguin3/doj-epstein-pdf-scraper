"""Scrape PDF links from a paginated DOJ disclosure page.

This script mirrors the original scraping logic but makes the target URL
configurable so you can swap between different data sets (1-8) or provide any
custom URL. Results are written to a text file with one URL per line.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterable

from playwright.sync_api import sync_playwright

DEFAULT_BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-8-files"
DEFAULT_OUTPUT = Path("pdf_links.txt")
DEFAULT_MAX_PAGES = 400
DEFAULT_DELAY_SECONDS = 1.5
DEFAULT_PROFILE = "pw_profile"  # folder created next to script to store cookies/session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dataset",
        type=int,
        choices=range(1, 9),
        help=(
            "Dataset number (1-8) from justice.gov. When provided, the base URL "
            "is set to the matching data-set-N-files page."
        ),
    )
    group.add_argument(
        "--base-url",
        type=str,
        default=None,
        help=(
            "Fully-qualified URL to scrape (overrides the dataset option). "
            "Must be the paginated listing page without the ?page= suffix."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the collected PDF links (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum number of pages to scan (default: {DEFAULT_MAX_PAGES}).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=f"Seconds to sleep between page requests (default: {DEFAULT_DELAY_SECONDS}).",
    )
    parser.add_argument(
        "--profile-dir",
        type=str,
        default=DEFAULT_PROFILE,
        help=(
            "Persistent Chromium profile directory for cookies/sessions (default: "
            f"{DEFAULT_PROFILE})."
        ),
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chromium in headless mode (default: visible browser).",
    )
    return parser.parse_args()


def resolve_base_url(args: argparse.Namespace) -> str:
    if args.base_url:
        return args.base_url.rstrip("/")
    if args.dataset:
        return (
            "https://www.justice.gov/epstein/doj-disclosures/"
            f"data-set-{args.dataset}-files"
        )
    return DEFAULT_BASE_URL


def collect_pdf_links(
    base_url: str,
    max_pages: int,
    delay_seconds: float,
    profile_dir: str,
    headless: bool,
) -> Iterable[str]:
    all_links: set[str] = set()
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for i in range(max_pages):
            url = f"{base_url}?page={i}"
            print(f"Scraping page {i} from {url} ...")

            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_selector('a[href*=".pdf"]', timeout=30000)
            except Exception:
                Path(f"blocked_page_{i}.html").write_text(
                    page.content(), encoding="utf-8"
                )
                print(
                    f"No PDF links detected on page {i}. "
                    f"Saved blocked_page_{i}.html and stopping."
                )
                break

            hrefs = page.eval_on_selector_all(
                'a[href*=".pdf"]',
                "els => els.map(e => e.href)",
            )

            if not hrefs:
                Path(f"blocked_page_{i}.html").write_text(
                    page.content(), encoding="utf-8"
                )
                print(
                    f"No PDF links extracted on page {i}. "
                    f"Saved blocked_page_{i}.html and stopping."
                )
                break

            all_links.update(hrefs)
            time.sleep(delay_seconds)

        context.close()
    return all_links


def main() -> None:
    args = parse_args()
    base_url = resolve_base_url(args)
    print(f"Using base URL: {base_url}")

    pdf_links = collect_pdf_links(
        base_url=base_url,
        max_pages=args.max_pages,
        delay_seconds=args.delay,
        profile_dir=args.profile_dir,
        headless=args.headless,
    )

    args.output.write_text("\n".join(sorted(pdf_links)), encoding="utf-8")
    print(f"\nSaved {len(pdf_links)} PDF links to {args.output}")


if __name__ == "__main__":
    main()
