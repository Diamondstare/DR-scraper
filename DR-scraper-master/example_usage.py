from pathlib import Path
from vote_group_comparison import (
    read_csv_rows,
    read_xml_votes,
    build_points,
    create_group_comparison_report,
    filter_candidates_by_votes,
    split_by_question3_answer,
    split_by_answer_frequency,
    split_by_party,
)

# Example usage
CSV_PATH = Path("DR-scraper-master\output.csv")
AFSTEMNINGSOMRAADER_DIR = Path("dst_xml_downloads") / "Afstemningsomraader"

# Main execution
def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH.resolve()}")

    if not AFSTEMNINGSOMRAADER_DIR.exists():
        raise FileNotFoundError(
            f"Afstemningsomraader folder not found: {AFSTEMNINGSOMRAADER_DIR.resolve()}"
        )

    csv_rows = read_csv_rows(CSV_PATH)
    votes_by_name = read_xml_votes(AFSTEMNINGSOMRAADER_DIR)

    # Split candidates by vote count (<=1000 vs >1000)
    candidates_under_1000, candidates_over_1000 = filter_candidates_by_votes(csv_rows, votes_by_name, max_votes=1500)

    print(f"Candidates with <= 1000 votes: {len(candidates_under_1000)}")
    print(f"Candidates with > 1000 votes: {len(candidates_over_1000)}")

    # Split candidates by question 3 answer (1,2 vs 4,5)
    group_q3_1_2, group_q3_4_5 = split_by_question3_answer(candidates_under_1000)

    print(f"\nCandidates who answered 1 or 2 on question 3: {len(group_q3_1_2)}")
    print(f"Candidates who answered 4 or 5 on question 3: {len(group_q3_4_5)}")

    # Split candidates by answer frequency (more than 5 answers of 1 or 5 vs 5 or fewer)
    group_freq_high, group_freq_low = split_by_answer_frequency(candidates_under_1000, votes_by_name)

    print(f"\nCandidates with more than 5 answers of 1 or 5: {len(group_freq_high)}")
    print(f"Candidates with 5 or fewer answers of 1 or 5: {len(group_freq_low)}")

    # Build points for both groups
    group1_points = build_points(group_q3_1_2, votes_by_name, lambda row: True)
    group2_points = build_points(group_q3_4_5, votes_by_name, lambda row: False)

    # Compare groups statistically
    report = create_group_comparison_report(
        group1_points,
        group2_points,
        group1_name="Answer 1 or 2 on Q3",
        group2_name="Answer 4 or 5 on Q3"
    )

    print("\n" + report)

    # Build points for answer frequency groups
    group_freq_high_points = build_points(group_freq_high, votes_by_name, lambda row: True)
    group_freq_low_points = build_points(group_freq_low, votes_by_name, lambda row: False)

    # Compare answer frequency groups statistically
    freq_report = create_group_comparison_report(
        group_freq_high_points,
        group_freq_low_points,
        group1_name="More than 5 answers of 1 or 5",
        group2_name="5 or fewer answers of 1 or 5"
    )

    print("\n" + freq_report)

    # Split candidates by party (A, V, O vs other parties)
    group_party_avo, group_other_parties = split_by_party(candidates_under_1000, votes_by_name)

    print(f"\nCandidates from parties A, V, O, F: {len(group_party_avo)}")
    print(f"Candidates from other parties: {len(group_other_parties)}")

    # Build points for party groups
    group_party_avo_points = build_points(group_party_avo, votes_by_name, lambda row: True)
    group_other_parties_points = build_points(group_other_parties, votes_by_name, lambda row: False)

    # Compare party groups statistically
    party_report = create_group_comparison_report(
        group_party_avo_points,
        group_other_parties_points,
        group1_name="Parties A, V, O, F",
        group2_name="Other parties"
    )

    print("\n" + party_report)


if __name__ == "__main__":
    main()