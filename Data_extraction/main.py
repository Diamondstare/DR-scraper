import csv
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright


BASE_URL = "https://www.dr.dk/nyheder/politik/folketingsvalg/din-stemmeseddel/kandidater/{}"


@dataclass
class Row:
    page_number: int
    line_up_name: str
    first_name: str
    last_name: str
    party_code: str
    answers: List[str]


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


def unescape_text(text: str) -> str:
    # Turn {\"QuestionID\":1294,...} into {"QuestionID":1294,...}
    return text.replace(r"\/", "/").replace(r"\"", '"')


def extract_json_objects_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Find escaped JSON objects, unescape them, then parse.
    """
    results: List[Dict[str, Any]] = []

    pattern = re.compile(r"\{\\?.*?\}", re.DOTALL)

    for match in pattern.finditer(text):
        chunk = unescape_text(match.group(0))
        try:
            obj = json.loads(chunk)
            if isinstance(obj, dict):
                results.append(obj)
        except Exception:
            pass

    return results


def extract_lineup_name(text: str) -> Optional[str]:
    for obj in extract_json_objects_from_text(text):
        if obj.get("groupType") == "Bigconstituency":
            name = obj.get("lineUpName")
            if name:
                return str(name)
    return None


def extract_answers(text: str) -> List[str]:
    answers: List[str] = []

    for obj in extract_json_objects_from_text(text):
        if "QuestionID" in obj and "Answer" in obj:
            answers.append(str(obj["Answer"]))

    return answers


def extract_person_info(text: str) -> Dict[str, str]:
    text = unescape_text(text)

    candidate_match = re.search(
        r'"candidate"\s*:\s*\{(?P<body>.*?)\}\s*,\s*"candidateAnswers"',
        text,
        re.DOTALL,
    )

    if not candidate_match:
        return {"first_name": "", "last_name": "", "party_code": ""}

    candidate_body = candidate_match.group("body")

    first_match = re.search(r'"Firstname"\s*:\s*"([^"]*)"', candidate_body)
    last_match = re.search(r'"LastName"\s*:\s*"([^"]*)"', candidate_body)
    party_code_match = re.search(r'"CurrentPartyCode"\s*:\s*"([^"]*)"', candidate_body)

    return {
        "first_name": first_match.group(1).strip() if first_match else "",
        "last_name": last_match.group(1).strip() if last_match else "",
        "party_code": party_code_match.group(1).strip() if party_code_match else "",
    }


def scrape_all_pages(start: int, end: int) -> List[Row]:
    rows: List[Row] = []

    for page_number in range(start, end + 1):
        url = BASE_URL.format(page_number)
        print(f"Scraping {url} ...")

        try:
            text = fetch_page_text(url)
            line_up_name = extract_lineup_name(text) or "UNKNOWN"
            person_info = extract_person_info(text)
            answers = extract_answers(text)

            rows.append(
                Row(
                    page_number=page_number,
                    line_up_name=line_up_name,
                    first_name=person_info["first_name"],
                    last_name=person_info["last_name"],
                    party_code=person_info["party_code"],
                    answers=answers,
                )
            )

        except Exception as e:
            print(f"Failed on {page_number}: {e}")

    return rows


def save_to_csv(rows: List[Row], output_file: str) -> None:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["page_number", "line_up_name", "first_name", "last_name", "party_code", "answers"])
        for row in rows:
            writer.writerow([
                row.page_number,
                row.line_up_name,
                row.first_name,
                row.last_name,
                row.party_code,
                " ".join(row.answers),
            ])


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <output.csv>")
        sys.exit(1)

    output_file = sys.argv[1]

    rows = scrape_all_pages(2, 984)
    save_to_csv(rows, output_file)

    print(f"Found {len(rows)} row(s).")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
