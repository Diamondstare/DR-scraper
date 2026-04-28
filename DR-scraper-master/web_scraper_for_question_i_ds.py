import csv
import re
import sys
from dataclasses import dataclass
from typing import List, Optional

from playwright.sync_api import sync_playwright


BASE_URL = "https://www.dr.dk/nyheder/politik/folketingsvalg/din-stemmeseddel/kandidater/{}"

# Matches lines like:
# QuestionID\,1270
# QuestionID,1270
QUESTION_ID_RE = re.compile(r"QuestionID\\?,\s*(\d+)", re.IGNORECASE)


@dataclass
class Row:
    page_number: int
    question_id: str
    next_field: str


def fetch_page_text(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )

        page.goto(url, wait_until="networkidle", timeout=60000)
        text = page.content()
        browser.close()
        return text


def extract_question_ids_with_following_field(text: str) -> List[tuple[str, str]]:
    """
    Returns a list of (question_id, next_field_value) pairs.

    We look at the text line-by-line and, for each QuestionID line,
    take the next non-empty line as the "field after" it.
    """
    lines = [line.strip() for line in text.splitlines()]
    results: List[tuple[str, str]] = []

    for i, line in enumerate(lines):
        match = QUESTION_ID_RE.search(line)
        if not match:
            continue

        question_id = match.group(1)
        next_field = ""

        for j in range(i + 1, len(lines)):
            candidate = lines[j].strip()
            if candidate:
                next_field = candidate
                break

        results.append((question_id, next_field))

    return results


def scrape_all_pages(start: int, end: int) -> List[Row]:
    rows: List[Row] = []

    for page_number in range(start, end + 1):
        url = BASE_URL.format(page_number)
        print(f"Scraping {url} ...")

        try:
            text = fetch_page_text(url)
            pairs = extract_question_ids_with_following_field(text)

            for question_id, next_field in pairs:
                rows.append(Row(page_number, question_id, next_field))

        except Exception as e:
            print(f"Failed on {page_number}: {e}")

    return rows


def save_to_csv(rows: List[Row], output_file: str) -> None:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page_number", "question_id", "next_field"])
        for row in rows:
            writer.writerow([row.page_number, row.question_id, row.next_field])


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <output.csv>")
        sys.exit(1)

    output_file = sys.argv[1]

    rows = scrape_all_pages(2, 984)
    save_to_csv(rows, output_file)

    print(f"Found {len(rows)} QuestionID row(s).")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
