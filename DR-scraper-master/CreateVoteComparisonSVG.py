import csv
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


CSV_PATH = Path("output.csv")
AFSTEMNINGSOMRAADER_DIR = Path("dst_xml_downloads") / "Afstemningsomraader"
OUTPUT_SVG = Path("party_question_diff_vs_log_votes.svg")


PARTY_COLORS = {
    "A": "red",
    "F": "pink",
    "V": "blue",
    "I": "teal",
    "O": "gold",
    "M": "darkviolet",
    "C": "green",
    "Ø": "darkred",
    "B": "plum",
    "Æ": "lightblue",
    "Å": "lightgreen",
    "H": "black",
    "": "brown",
}


@dataclass
class Point:
    x: float
    y: float
    label: str
    party_code: str


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def normalize_name(name: str) -> str:
    name = name.strip()
    name = name.replace(".", "")
    name = re.sub(r"\s+", " ", name)
    return name.casefold()


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extract_answers(answers_text: str) -> list[int | None]:
    """
    Parse all answers.
    Values 0 or invalid values are treated as missing.
    """
    answers: list[int | None] = []
    for item in answers_text.split():
        try:
            value = int(item)
        except ValueError:
            answers.append(None)
            continue

        if value == 0:
            answers.append(None)
        else:
            answers.append(value)

    return answers


def extract_person_votes(elem: ET.Element) -> int:
    text = (elem.attrib.get("PersonligeStemmer", "") or "").strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def extract_candidate_name(elem: ET.Element) -> str:
    return (elem.attrib.get("Navn", "") or "").strip()


def extract_points_from_xml(xml_path: Path) -> list[tuple[str, int]]:
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Skipping invalid XML: {xml_path} ({e})")
        return []

    points: list[tuple[str, int]] = []

    for elem in root.iter():
        if local_name(elem.tag) != "Person":
            continue

        name = extract_candidate_name(elem)
        votes = extract_person_votes(elem)

        if name:
            points.append((name, votes))

    return points


def read_xml_votes(folder: Path) -> dict[str, int]:
    votes_by_name: dict[str, int] = {}

    for xml_file in folder.rglob("*.xml"):
        for name, votes in extract_points_from_xml(xml_file):
            key = normalize_name(name)
            votes_by_name[key] = votes_by_name.get(key, 0) + votes

    return votes_by_name


def build_points(csv_rows: list[dict[str, str]], votes_by_name: dict[str, int]) -> list[Point]:
    """
    Build points using the party's average answer for each question.
    x = sum over questions of (candidate_answer - party_avg_answer)^2
    y = log10(votes + 1)
    """
    candidates: list[dict[str, object]] = []
    party_question_sums: dict[str, list[float]] = defaultdict(list)
    party_question_counts: dict[str, list[int]] = defaultdict(list)

    # First pass: collect all valid answers and party totals per question
    for row in csv_rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        party_code = (row.get("party_code") or "").strip()
        answers_text = (row.get("answers") or "").strip()

        if not first_name and not last_name:
            continue

        answers = extract_answers(answers_text)
        if not answers:
            continue

        full_name = normalize_name(f"{first_name} {last_name}")
        votes = votes_by_name.get(full_name)
        if votes is None:
            continue

        candidates.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "party_code": party_code,
                "answers": answers,
                "votes": votes,
            }
        )

        # Make sure the per-question arrays are long enough
        while len(party_question_sums[party_code]) < len(answers):
            party_question_sums[party_code].append(0.0)
            party_question_counts[party_code].append(0)

        for i, answer in enumerate(answers):
            if answer is None:
                continue
            party_question_sums[party_code][i] += answer
            party_question_counts[party_code][i] += 1

    # Compute party average per question
    party_question_avgs: dict[str, list[float | None]] = {}
    for party_code, sums in party_question_sums.items():
        counts = party_question_counts[party_code]
        avgs: list[float | None] = []
        for total, count in zip(sums, counts):
            if count == 0:
                avgs.append(None)
            else:
                avgs.append(total / count)
        party_question_avgs[party_code] = avgs

    # Second pass: compute squared difference from party average answers
    points: list[Point] = []
    for candidate in candidates:
        party_code = str(candidate["party_code"])
        answers = candidate["answers"]
        votes = int(candidate["votes"])

        avgs = party_question_avgs.get(party_code)
        if not avgs:
            continue

        squared_diff = 0.0
        for i, answer in enumerate(answers):
            if answer is None:
                continue
            if i >= len(avgs):
                continue
            party_avg = avgs[i]
            if party_avg is None:
                continue
            squared_diff += (answer - party_avg) ** 2

        label = f'{candidate["first_name"]} {candidate["last_name"]}'
        y = math.log10(votes + 1)
        points.append(Point(x=squared_diff, y=y, label=label, party_code=party_code))

    return points


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def color_for_party(party_code: str) -> str:
    return PARTY_COLORS.get((party_code or "").strip(), "brown")


def create_svg(points: list[Point], output_path: Path) -> None:
    width = 1100
    height = 800
    margin_left = 90
    margin_right = 30
    margin_top = 40
    margin_bottom = 90

    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    if not points:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="50%" y="50%" text-anchor="middle" font-size="24">No points to plot</text>
</svg>
"""
        output_path.write_text(svg, encoding="utf-8")
        return

    max_x = max(p.x for p in points)
    max_y = max(p.y for p in points)

    def x_to_px(x: float) -> float:
        if max_x == 0:
            return margin_left + plot_width / 2
        return margin_left + (x / max_x) * plot_width

    def y_to_px(y: float) -> float:
        if max_y == 0:
            return margin_top + plot_height / 2
        return margin_top + plot_height - (y / max_y) * plot_height

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
    lines.append('<rect width="100%" height="100%" fill="white"/>')

    lines.append(
        f'<text x="{width / 2}" y="24" text-anchor="middle" font-size="20" font-family="Arial">'
        f'Party question-average difference vs log10(votes + 1)'
        f"</text>"
    )

    x0 = margin_left
    y0 = margin_top
    y1 = margin_top + plot_height
    x2 = margin_left + plot_width
    y2 = margin_top + plot_height

    lines.append(f'<line x1="{x0}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2"/>')
    lines.append(f'<line x1="{x0}" y1="{y1}" x2="{x0}" y2="{y0}" stroke="black" stroke-width="2"/>')

    lines.append(
        f'<text x="{margin_left + plot_width / 2}" y="{height - 30}" text-anchor="middle" '
        f'font-size="16" font-family="Arial">Squared difference from party average answers</text>'
    )
    lines.append(
        f'<text x="24" y="{margin_top + plot_height / 2}" text-anchor="middle" '
        f'font-size="16" font-family="Arial" transform="rotate(-90 24 {margin_top + plot_height / 2})">'
        f'log10(votes + 1)</text>'
    )

    tick_count = 5
    for i in range(tick_count + 1):
        value = (max_x / tick_count) * i if tick_count else 0
        px = x_to_px(value)
        lines.append(f'<line x1="{px}" y1="{y2}" x2="{px}" y2="{y2 + 6}" stroke="black"/>')
        lines.append(
            f'<text x="{px}" y="{y2 + 22}" text-anchor="middle" font-size="12" font-family="Arial">{value:.2f}</text>'
        )

    for i in range(tick_count + 1):
        value = (max_y / tick_count) * i if tick_count else 0
        py = y_to_px(value)
        lines.append(f'<line x1="{x0 - 6}" y1="{py}" x2="{x0}" y2="{py}" stroke="black"/>')
        lines.append(
            f'<text x="{x0 - 10}" y="{py + 4}" text-anchor="end" font-size="12" font-family="Arial">{value:.1f}</text>'
        )

    for point in points:
        px = x_to_px(point.x)
        py = y_to_px(point.y)
        fill = color_for_party(point.party_code)
        title = svg_escape(f"{point.label} ({point.party_code or 'none'}): x={point.x:.3f}, y={point.y:.2f}")
        lines.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="{fill}" opacity="0.85"/>')
        lines.append(f"<title>{title}</title>")

    lines.append(
        f'<text x="{margin_left}" y="{margin_top - 10}" font-size="12" font-family="Arial" fill="#333">'
        f"{len(points)} candidates plotted"
        f"</text>"
    )

    lines.append("</svg>")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH.resolve()}")

    if not AFSTEMNINGSOMRAADER_DIR.exists():
        raise FileNotFoundError(
            f"Afstemningsomraader folder not found: {AFSTEMNINGSOMRAADER_DIR.resolve()}"
        )

    csv_rows = read_csv_rows(CSV_PATH)
    votes_by_name = read_xml_votes(AFSTEMNINGSOMRAADER_DIR)
    points = build_points(csv_rows, votes_by_name)

    print(f"CSV rows loaded: {len(csv_rows)}")
    print(f"Candidates with XML vote data: {len(votes_by_name)}")
    print(f"Points plotted: {len(points)}")

    create_svg(points, OUTPUT_SVG)
    print(f"Saved graph to: {OUTPUT_SVG.resolve()}")


if __name__ == "__main__":
    main()
