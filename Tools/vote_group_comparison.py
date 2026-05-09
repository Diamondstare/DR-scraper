import csv
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any, TypeVar
from scipy import stats
from functools import wraps

from dataclasses import field

@dataclass
class candidate:
    party_code: str
    votes: int
    storkreds: str
    name: str = ""
    adtional_values: dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return self.name


def filter_candidate(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if not self.__filter(result):
            raise ValueError(f"Candidate '{result.name}' is filtered out")
        return result
    return wrapper


class xml_reader():
    def __init__(self,filter=lambda x:True):
        self.__voting_place_reults = {}
        self.__all_candidate_names_cache = None
        self.__candidate_cache = {}
        self.__filter=filter
        
    def get_candidate_votes(self, candidate):
        total_votes = 0
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader")
        
        for voting_place_dir in base_path.iterdir():
            if voting_place_dir.is_dir():
                votes_by_name = self.__read_voting_place(voting_place_dir.name)
                normalized_candidate = self.__normalize_name(candidate)
                total_votes += votes_by_name.get(normalized_candidate, 0)
        
        return total_votes

    def get_all_candidate_names(self):
        if self.__all_candidate_names_cache is not None:
            return self.__all_candidate_names_cache
        
        all_names = set()
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader")
        
        for voting_place_dir in base_path.iterdir():
            if voting_place_dir.is_dir():
                votes_by_name = self.__read_voting_place(voting_place_dir.name)
                for name in votes_by_name.keys():
                    if self.__filter(name):
                        all_names.add(name)
        
        self.__all_candidate_names_cache = list(all_names)
        return self.__all_candidate_names_cache

    @filter_candidate
    def get_candidate(self, candidate_name):
        normalized_name = self.__normalize_name(candidate_name)
        if normalized_name in self.__candidate_cache:
            return self.__candidate_cache[normalized_name]
        
        votes = self.get_candidate_votes(candidate_name)
        party_code = self.__get_candidate_party_code(normalized_name)
        storkreds = self.__get_candidate_storkreds(normalized_name)
        candidate_instance = candidate(party_code=party_code, votes=votes, storkreds=storkreds,name=normalized_name)
        self.__candidate_cache[normalized_name] = candidate_instance
        return candidate_instance
    
    def __get_candidate_party_code(self, normalized_candidate_name):
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader")
        
        for voting_place_dir in base_path.iterdir():
            if voting_place_dir.is_dir():
                xml_path = self.__voting_place_to_xml(voting_place_dir.name)
                party_code = self.__extract_candidate_party_code(xml_path, normalized_candidate_name)
                if party_code:
                    return party_code
        return ""
    
    def __get_candidate_storkreds(self, normalized_candidate_name):
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader")
        
        for voting_place_dir in base_path.iterdir():
            if voting_place_dir.is_dir():
                xml_path = self.__voting_place_to_xml(voting_place_dir.name)
                storkreds = self.__extract_candidate_storkreds(xml_path, normalized_candidate_name)
                if storkreds:
                    return storkreds
        return ""
    
    def __read_voting_place(self, voting_place):
        if voting_place in self.__voting_place_reults:
            return self.__voting_place_reults[voting_place]
        else:
            votes_by_name: dict[str, int] = {}
            xml_paths = self.__voting_place_to_xml(voting_place)
            for xml_path in xml_paths:
                for name, votes in self.__extract_points_from_xml(xml_path):
                    key = self.__normalize_name(name)
                    votes_by_name[key] = votes_by_name.get(key, 0) + votes
            
            self.__voting_place_reults[voting_place] = votes_by_name
        
        return votes_by_name
   
    def __voting_place_to_xml(self, voting_place):
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader") / voting_place
        xml_files = list(base_path.glob("*.xml"))
        return xml_files
    
    def __extract_points_from_xml(self,xml_path: Path) -> list[tuple[str, int]]:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Skipping invalid XML: {xml_path} ({e})")
            return []

        points: list[tuple[str, int]] = []

        for elem in root.iter():
            if self.__local_name(elem.tag) == "Person":
                name = extract_candidate_name(elem)
                votes = extract_person_votes(elem)

                if name:
                    points.append((name, votes))
            
            elif self.__local_name(elem.tag) == "Parti":
                if "Bogstav" not in elem.attrib:
                    name = elem.attrib.get("navn", "")
                    votes = int(elem.attrib.get("PersonligeStemmer", "0"))
                    
                    if name:
                        points.append((name, votes))

        return points

    def __extract_candidate_party_code(self, xml_path: Path, normalized_candidate_name: str) -> str:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Skipping invalid XML: {xml_path} ({e})")
            return ""

        for parti_elem in root.iter():
            if self.__local_name(parti_elem.tag) != "Parti":
                continue
            
            party_code = parti_elem.attrib.get("Bogstav", "")
            
            # Check if this is a party with candidates
            if party_code:
                for person_elem in parti_elem.iter():
                    if self.__local_name(person_elem.tag) != "Person":
                        continue
                    
                    name = extract_candidate_name(person_elem)
                    if name:
                        normalized_name = self.__normalize_name(name)
                        if normalized_name == normalized_candidate_name:
                            return party_code
            
            # Check if this is an independent candidate (no Bogstav attribute)
            else:
                parti_name = parti_elem.attrib.get("navn", "")
                if parti_name:
                    normalized_parti_name = self.__normalize_name(parti_name)
                    if normalized_parti_name == normalized_candidate_name:
                        return ""
        
        return ""

    def __extract_candidate_storkreds(self, xml_path: Path, normalized_candidate_name: str) -> str:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Skipping invalid XML: {xml_path} ({e})")
            return ""

        for sted_elem in root.iter():
            if self.__local_name(sted_elem.tag) == "Sted":
                return sted_elem.attrib.get("Type", "") + ": " + sted_elem.text or ""
        
        return ""
    
    def __normalize_name(self,name: str) -> str:
        name = name.strip()
        name = name.replace(".", "")
        name = re.sub(r"\s+", " ", name)
        return name.casefold()
    
    def __local_name(self,tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag
T = TypeVar('T')


@dataclass
class Point:
    x: int
    y: float
    label: str
    party_code: str


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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




def build_points(
    csv_rows: list[dict[str, str]],
    votes_by_name: dict[str, int],
    group_splitter: Callable[[dict[str, str]], bool],
) -> list[Point]:
    points: list[Point] = []

    for row in csv_rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        answers_text = (row.get("answers") or "").strip()
        party_code = (row.get("party_code") or "").strip()

        if not first_name and not last_name:
            continue

        question3 = extract_question3_answer(answers_text)
        if question3 is None:
            continue

        full_name = normalize_name(f"{first_name} {last_name}")
        votes = votes_by_name.get(full_name)

        if votes is None:
            continue

        x = question3
        y = votes
        label = f"{first_name} {last_name}"

        group = group_splitter(row)

        points.append(Point(x=x, y=y, label=label, party_code=party_code))

    return points


def extract_question3_answer(answers_text: str):
    answers = answers_text.split()
    if len(answers) < 3:
        return None

    try:
        return int(answers[1])
    except ValueError:
        return None


def filter_candidates_by_votes(
    csv_rows: list[dict[str, str]],
    votes_by_name: dict[str, int],
    max_votes: int = 1000,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Split candidates into two groups based on vote count.
    Group 1: Candidates with votes <= max_votes
    Group 2: Candidates with votes > max_votes
    """
    group1: list[dict[str, str]] = []
    group2: list[dict[str, str]] = []

    for row in csv_rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        if not first_name and not last_name:
            continue

        full_name = normalize_name(f"{first_name} {last_name}")
        votes = votes_by_name.get(full_name, 0)

        if votes <= max_votes:
            group1.append(row)
        else:
            group2.append(row)

    return group1, group2


def split_by_question3_answer(
    csv_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Split candidates into two groups based on their answer to question 3.
    Group 1: Candidates who answered 1 or 2
    Group 2: Candidates who answered 4 or 5
    """
    group1: list[dict[str, str]] = []
    group2: list[dict[str, str]] = []

    for row in csv_rows:
        answers_text = (row.get("answers") or "").strip()
        question3 = extract_question3_answer(answers_text)

        if question3 is None:
            continue

        if question3 in [1, 2]:
            group1.append(row)
        elif question3 in [4, 5]:
            group2.append(row)

    return group1, group2


def split_by_party(
    csv_rows: list[dict[str, str]],
    votes_by_name: dict[str, int],
    target_parties: list[str] = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Split candidates into two groups based on party affiliation.
    Group 1: Candidates from the target parties (A, V, O by default)
    Group 2: Candidates from other parties
    Only considers candidates with <= 1000 total votes.
    """
    if target_parties is None:
        target_parties = ["A", "V", "O", "F"]

    group1: list[dict[str, str]] = []
    group2: list[dict[str, str]] = []

    for row in csv_rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        if not first_name and not last_name:
            continue

        full_name = normalize_name(f"{first_name} {last_name}")
        votes = votes_by_name.get(full_name, 0)

        if votes > 1000:
            continue

        party_code = (row.get("party_code") or "").strip()

        if party_code in target_parties:
            group1.append(row)
        else:
            group2.append(row)

    return group1, group2


def split_by_answer_frequency(
    csv_rows: list[dict[str, str]],
    votes_by_name: dict[str, int],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """
    Split candidates into two groups based on the frequency of their answers to question 3.
    Group 1: Candidates with more than 5 answers of 1 or 5
    Group 2: Candidates with 5 or fewer answers of 1 or 5
    Only considers candidates with <= 1000 total votes.
    """
    group1: list[dict[str, str]] = []
    group2: list[dict[str, str]] = []

    for row in csv_rows:
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        if not first_name and not last_name:
            continue

        full_name = normalize_name(f"{first_name} {last_name}")
        votes = votes_by_name.get(full_name, 0)

        if votes > 1000:
            continue

        answers_text = (row.get("answers") or "").strip()
        answers = answers_text.split()

        if len(answers) < 3:
            continue

        try:
            question3 = int(answers[1])
        except ValueError:
            continue

        count_1_or_5 = sum(1 for ans in answers if ans in ["1", "5"])

        if count_1_or_5 > 5:
            group1.append(row)
        else:
            group2.append(row)

    return group1, group2


def compare_groups_statistically(
    group1_points: list[Point],
    group2_points: list[Point],
) -> dict[str, Any]:
    """
    Compare two groups of points statistically.
    Returns a dictionary with comparison results.
    """
    results = {
        "group1_size": len(group1_points),
        "group2_size": len(group2_points),
    }

    if not group1_points or not group2_points:
        return results

    group1_ys = [p.y for p in group1_points]
    group2_ys = [p.y for p in group2_points]

    mean1 = sum(group1_ys) / len(group1_ys)
    mean2 = sum(group2_ys) / len(group2_ys)

    results["mean_group1"] = mean1
    results["mean_group2"] = mean2
    results["mean_difference"] = mean1 - mean2

    # Calculate standard deviations
    std1 = math.sqrt(sum((y - mean1) ** 2 for y in group1_ys) / len(group1_ys)) if group1_ys else 0
    std2 = math.sqrt(sum((y - mean2) ** 2 for y in group2_ys) / len(group2_ys)) if group2_ys else 0

    results["std_group1"] = std1
    results["std_group2"] = std2

    # Calculate t-statistic and p-value
    n1, n2 = len(group1_ys), len(group2_ys)
    if n1 + n2 < 2:
        t_statistic = 0
        p_value = 1.0
    else:
        pooled_std = math.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2))
        t_statistic = (mean1 - mean2) / (pooled_std * math.sqrt(1 / n1 + 1 / n2)) if pooled_std != 0 else 0
        
        # Calculate two-tailed p-value
        p_value = stats.t.sf(abs(t_statistic), df=n1 + n2 - 2) * 2

    results["t_statistic"] = t_statistic
    results["p_value"] = p_value

    return results

    group1_ys = [p.y for p in group1_points]
    group2_ys = [p.y for p in group2_points]

    mean1 = sum(group1_ys) / len(group1_ys) if group1_ys else 0
    mean2 = sum(group2_ys) / len(group2_ys) if group2_ys else 0

    results["mean_group1"] = mean1
    results["mean_group2"] = mean2
    results["mean_difference"] = mean1 - mean2

    # Calculate standard deviations
    std1 = math.sqrt(sum((y - mean1) ** 2 for y in group1_ys) / len(group1_ys)) if group1_ys else 0
    std2 = math.sqrt(sum((y - mean2) ** 2 for y in group2_ys) / len(group2_ys)) if group2_ys else 0

    results["std_group1"] = std1
    results["std_group2"] = std2

    # Calculate t-statistic (simplified)
    n1, n2 = len(group1_ys), len(group2_ys)
    if n1 + n2 < 2:
        t_statistic = 0
    else:
        pooled_std = math.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2))
        t_statistic = (mean1 - mean2) / (pooled_std * math.sqrt(1 / n1 + 1 / n2)) if pooled_std != 0 else 0

    results["t_statistic"] = t_statistic

    return results


def create_group_comparison_report(
    group1_points: list[Point],
    group2_points: list[Point],
    group1_name: str = "Group 1",
    group2_name: str = "Group 2",
) -> str:
    """
    Create a human-readable report comparing two groups.
    """
    stats = compare_groups_statistically(group1_points, group2_points)

    report_lines = []
    report_lines.append(f"Group Comparison Report")
    report_lines.append(f"{group1_name}: {stats['group1_size']} candidates")
    report_lines.append(f"{group2_name}: {stats['group2_size']} candidates")
    report_lines.append("")
    report_lines.append("Statistics:")
    report_lines.append(f"  Mean {group1_name}: {stats['mean_group1']:.4f}")
    report_lines.append(f"  Mean {group2_name}: {stats['mean_group2']:.4f}")
    report_lines.append(f"  Difference: {stats['mean_difference']:.4f}")
    report_lines.append("")
    report_lines.append("Standard Deviations:")
    report_lines.append(f"  {group1_name}: {stats['std_group1']:.4f}")
    report_lines.append(f"  {group2_name}: {stats['std_group2']:.4f}")
    report_lines.append("")
    report_lines.append(f"T-statistic: {stats['t_statistic']:.4f}")
    report_lines.append(f"P-value: {stats['p_value']:.4f}")

    if stats['p_value'] < 0.05:
        if stats['t_statistic'] > 0:
            report_lines.append(f"Conclusion: {group1_name} has significantly higher average votes (p < 0.05)")
        elif stats['t_statistic'] < 0:
            report_lines.append(f"Conclusion: {group2_name} has significantly higher average votes (p < 0.05)")
    else:
        report_lines.append("Conclusion: No significant difference (p >= 0.05)")

    return "\n".join(report_lines)
