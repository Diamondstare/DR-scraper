import csv
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List


ALLOWED_RANDOM_ANSWERS = [1, 2, 4, 5]
ALLOWED_RANDOM_WEIGHTS = [0, 5, 5, 0]
TRIALS = 10000000
BOTTOM_N = 6
TOP_RESULTS = 10
PROGRESS_EVERY = 1000


@dataclass
class Row:
    page_number: int
    line_up_name: str
    answers: List[int]


def load_rows_from_csv(output_file: str) -> List[Row]:
    rows: List[Row] = []

    with open(output_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_up_name = (row.get("line_up_name") or "").strip()
            answers_text = (row.get("answers") or "").strip()

            answers: List[int] = []
            for item in answers_text.split():
                try:
                    answers.append(int(item))
                except ValueError:
                    pass

            rows.append(
                Row(
                    page_number=int(row["page_number"]),
                    line_up_name=line_up_name,
                    answers=answers,
                )
            )

    return rows


def weighted_random_answer() -> int:
    return random.choices(ALLOWED_RANDOM_ANSWERS, weights=ALLOWED_RANDOM_WEIGHTS, k=1)[0]


def save_scatter_svg(points: list[tuple[int, float, str]], output_file: str) -> None:
    width = 1000
    height = 700
    margin_left = 90
    margin_right = 40
    margin_top = 40
    margin_bottom = 80

    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    if not points:
        return

    min_x = min(x for x, _, _ in points)
    max_x = max(x for x, _, _ in points)
    min_y = min(y for _, y, _ in points)
    max_y = max(y for _, y, _ in points)

    if min_x == max_x:
        max_x += 1
    if min_y == max_y:
        max_y += 1

    def sx(x: int) -> float:
        return margin_left + (x - min_x) / (max_x - min_x) * plot_width

    def sy(y: float) -> float:
        return margin_top + (max_y - y) / (max_y - min_y) * plot_height

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="black"/>',
        f'<text x="{width / 2}" y="25" text-anchor="middle" font-size="18">Count vs Average Bottom-6 Score</text>',
        f'<text x="{width / 2}" y="{height - 20}" text-anchor="middle" font-size="14">Count in bottom {BOTTOM_N}</text>',
        f'<text x="25" y="{height / 2}" text-anchor="middle" font-size="14" transform="rotate(-90 25 {height / 2})">Average bottom-{BOTTOM_N} score</text>',
    ]

    for x, y, label in points:
        px = sx(x)
        py = sy(y)
        lines.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="#2b6cb0" opacity="0.75"/>')
        lines.append(
            f'<title>{label}: count={x}, avg_score={y:.2f}</title>'
        )

    tick_count = 5
    for i in range(tick_count + 1):
        t = i / tick_count
        x_val = min_x + t * (max_x - min_x)
        x_pos = margin_left + t * plot_width
        lines.append(f'<line x1="{x_pos:.2f}" y1="{margin_top + plot_height}" x2="{x_pos:.2f}" y2="{margin_top + plot_height + 6}" stroke="black"/>')
        lines.append(f'<text x="{x_pos:.2f}" y="{margin_top + plot_height + 22}" text-anchor="middle" font-size="12">{x_val:.0f}</text>')

        y_val = min_y + t * (max_y - min_y)
        y_pos = margin_top + plot_height - t * plot_height
        lines.append(f'<line x1="{margin_left - 6}" y1="{y_pos:.2f}" x2="{margin_left}" y2="{y_pos:.2f}" stroke="black"/>')
        lines.append(f'<text x="{margin_left - 10}" y="{y_pos + 4:.2f}" text-anchor="end" font-size="12">{y_val:.2f}</text>')

    lines.append("</svg>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def compare_against_random_choices(output_file: str) -> None:
    rows = load_rows_from_csv(output_file)
    valid_rows = [
        row
        for row in rows
        if row.line_up_name != "UNKNOWN" and row.answers and 0 not in row.answers
    ]

    if not valid_rows:
        print("No valid Bigconstituency rows found.")
        return

    rows_by_constituency = defaultdict(list)
    for row in valid_rows:
        rows_by_constituency[row.line_up_name].append(row)

    constituency_bottom_6_counts: dict[str, Counter] = {
        constituency: Counter() for constituency in rows_by_constituency
    }
    constituency_bottom_6_score_sums: dict[str, Counter] = {
        constituency: Counter() for constituency in rows_by_constituency
    }
    constituency_pick_counts = Counter()

    constituencies = list(rows_by_constituency.keys())

    for trial in range(1, TRIALS + 1):
        if trial == 1 or trial % PROGRESS_EVERY == 0 or trial == TRIALS:
            percent = (trial / TRIALS) * 100
            print(f"Progress: {trial}/{TRIALS} ({percent:.1f}%)")

        constituency = random.choice(constituencies)
        constituency_pick_counts[constituency] += 1
        constituency_rows = rows_by_constituency[constituency]

        if len(constituency_rows) < BOTTOM_N:
            continue

        max_length = max(len(row.answers) for row in constituency_rows)
        random_answers = [weighted_random_answer() for _ in range(max_length)]

        trial_scores = []
        for row in constituency_rows:
            score = sum(
                abs(candidate - random_answer)
                for candidate, random_answer in zip(row.answers, random_answers)
            )
            trial_scores.append((score, row))

        trial_scores.sort(key=lambda item: item[0])

        for score, row in trial_scores[-BOTTOM_N:]:
            constituency_bottom_6_counts[constituency][row.page_number] += 1
            constituency_bottom_6_score_sums[constituency][row.page_number] += score

    print(f"Ran {TRIALS} trials.")
    print("\nBigconstituency pick counts:")
    for constituency, count in constituency_pick_counts.most_common():
        print(f"  {constituency}: {count}")

    plot_points: list[tuple[int, float, str]] = []

    print(f"\nAll candidates per Bigconstituency by bottom-{BOTTOM_N} appearances:")
    for constituency, counts in constituency_bottom_6_counts.items():
        print(f"\n{constituency}")
        for page_number, count in counts.most_common():
            avg_score = 1 - constituency_bottom_6_score_sums[constituency][page_number] / (count * 25 * 5)
            print(f"  candidate/page {page_number}: {count} | avg_score_in_bottom_{BOTTOM_N}={avg_score:.2f}")

            log_count = math.log10(count)
            plot_points.append((log_count, avg_score, f"{constituency} / {page_number}"))

    save_scatter_svg(plot_points, "count_vs_avg_score.svg")
    print("\nSaved plot to: count_vs_avg_score.svg")


def main() -> None:
    compare_against_random_choices("output.csv")


if __name__ == "__main__":
    main()
