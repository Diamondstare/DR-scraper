import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable


CSV_PATH = Path("output.csv")
AFSTEMNINGSOMRAADER_DIR = Path("dst_xml_downloads") / "Afstemningsomraader"


def normalize_name(name: str) -> str:
    """
    Normalize names so that minor formatting differences don't create false mismatches.
    Examples:
      - extra spaces
      - dots in initials
      - repeated whitespace
    """
    name = name.strip()
    name = name.replace(".", "")
    name = re.sub(r"\s+", " ", name)
    return name.casefold()


def read_csv_candidates(csv_path: Path) -> set[str]:
    candidates: set[str] = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()

            # Skip empty/invalid rows
            if not first_name and not last_name:
                continue

            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                candidates.add(normalize_name(full_name))

    return candidates


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def extract_person_names_from_xml(xml_path: Path) -> set[str]:
    names: set[str] = set()

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Skipping invalid XML: {xml_path} ({e})")
        return names

    for elem in root.iter():
        if local_name(elem.tag) != "Person":
            continue

        name = elem.attrib.get("Navn", "").strip()
        if name:
            names.add(normalize_name(name))

    return names


def read_afstemningsomraader_candidates(folder: Path) -> set[str]:
    candidates: set[str] = set()

    for xml_file in folder.rglob("*.xml"):
        candidates.update(extract_person_names_from_xml(xml_file))

    return candidates


def pretty_set(values: Iterable[str]) -> list[str]:
    return sorted(values)


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH.resolve()}")

    if not AFSTEMNINGSOMRAADER_DIR.exists():
        raise FileNotFoundError(
            f"Afstemningsomraader folder not found: {AFSTEMNINGSOMRAADER_DIR.resolve()}"
        )

    csv_candidates = read_csv_candidates(CSV_PATH)
    xml_candidates = read_afstemningsomraader_candidates(AFSTEMNINGSOMRAADER_DIR)

    only_in_csv = csv_candidates - xml_candidates
    only_in_xml = xml_candidates - csv_candidates
    in_both = csv_candidates & xml_candidates

    print(f"CSV candidates: {len(csv_candidates)}")
    print(f"XML candidates: {len(xml_candidates)}")
    print(f"In both: {len(in_both)}")
    print(f"Only in CSV: {len(only_in_csv)}")
    print(f"Only in XML: {len(only_in_xml)}")

    print("\n=== Candidates only in output.csv ===")
    for name in pretty_set(only_in_csv):
        print(name)

    print("\n=== Candidates only in Afstemningsomraader XML ===")
    for name in pretty_set(only_in_xml):
        print(name)

    print("\nDone.")


if __name__ == "__main__":
    main()
