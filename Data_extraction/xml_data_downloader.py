import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


URL = "https://www.dst.dk/valg/Valg2546527/xml/fintal.xml"
OUTPUT_DIR = Path("dst_xml_downloads")


def safe_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name


def download_xml(url: str) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, timeout=60, headers=headers)
    response.raise_for_status()
    return response.content


def parse_xml(xml_bytes: bytes) -> ET.Element:
    if xml_bytes.startswith(b"\xef\xbb\xbf"):
        xml_bytes = xml_bytes[3:]

    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        preview = xml_bytes[:500].decode("utf-8", errors="replace")
        raise ET.ParseError(
            f"{exc}. The downloaded content does not look like valid XML.\n"
            f"First 500 characters of response:\n{preview}"
        ) from exc


def write_bytes(data: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def get_attr(element: ET.Element, name: str) -> str:
    return element.attrib.get(name, "").strip()


def get_text(element: ET.Element) -> str:
    return (element.text or "").strip()


def download_and_save(url: str, output_path: Path) -> ET.Element:
    xml_bytes = download_xml(url)
    write_bytes(xml_bytes, output_path)
    return parse_xml(xml_bytes)


def process_group(root: ET.Element, group_name: str, child_tag: str, base_folder: Path) -> None:
    group_container = root.find(group_name)
    if group_container is None:
        print(f"No <{group_name}> section found.")
        return

    group_folder = base_folder / group_name
    group_folder.mkdir(parents=True, exist_ok=True)

    for item in group_container.findall(child_tag):
        name = get_text(item) or f"UNKNOWN_{child_tag.upper()}"
        item_id = get_attr(item, f"{child_tag.lower()}_id")
        file_url = get_attr(item, "filnavn")

        if not file_url:
            print(f"Skipping {name}: missing 'filnavn' attribute")
            continue

        absolute_url = urljoin(URL, file_url)

        item_folder = group_folder / safe_name(name)
        item_folder.mkdir(parents=True, exist_ok=True)

        file_name = Path(urlparse(absolute_url).path).name or "data.xml"

        # Include the ID in the saved filename so each storkreds is clearly traceable.
        if item_id:
            file_name = f"{file_name.stem if hasattr(file_name, 'stem') else Path(file_name).stem}_{item_id}.xml"
            output_path = item_folder / file_name
        else:
            output_path = item_folder / file_name

        print(f"Downloading {name} (id={item_id or 'unknown'}) -> {absolute_url}")
        print(f"Saving to: {output_path}")

        try:
            download_and_save(absolute_url, output_path)
        except requests.RequestException as exc:
            print(f"Failed to download {name} from {absolute_url}: {exc}")
        except ET.ParseError as exc:
            print(f"Downloaded invalid XML for {name} from {absolute_url}: {exc}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save the main index file
    main_xml_path = OUTPUT_DIR / "fintal.xml"
    root = download_and_save(URL, main_xml_path)

    # Save by the structure described in fintal.xml
    process_group(root, "Landsdele", "Landsdel", OUTPUT_DIR)
    process_group(root, "Storkredse", "Storkreds", OUTPUT_DIR)
    process_group(root, "Opstillingskredse", "Opstillingskreds", OUTPUT_DIR)
    process_group(root, "Afstemningsomraader", "Afstemningsomraade", OUTPUT_DIR)

    print(f"Done. Files saved under: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
