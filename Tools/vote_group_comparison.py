import csv
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Any, Dict, List, Optional, Tuple
from scipy import stats
from functools import wraps
import matplotlib.pyplot as plt


@dataclass
class candidate:
    party_code: str
    votes: int
    storkreds: str
    name: str = ""
    additional_values: dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return self.name

    def copy(self):
        return candidate(
            party_code=self.party_code,
            votes=self.votes,
            storkreds=self.storkreds,
            name=self.name,
            additional_values=self.additional_values.copy()
        )


def filter_candidate(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if not self.__filter(result):
            raise ValueError(f"Candidate '{result.name}' is filtered out")
        return result
    return wrapper


def add_additional_values(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        result.additional_values = self.additional_values
        return result
    return wrapper


def handle_multiple_xml_paths(func):
    @wraps(func)
    def wrapper(self, xml_paths, *args, **kwargs):
        if isinstance(xml_paths, list):
            for xml_path in xml_paths:
                result = func(self, xml_path, *args, **kwargs)
                if result:
                    return result
            return ""
        else:
            return func(self, xml_paths, *args, **kwargs)
    return wrapper


class Filter:
    def __init__(self, name: str, filter_func: Callable):
        self.name = name
        self.filter_func = filter_func
    
    def __call__(self, candidate):
        return self.filter_func(candidate)

class CandidateGrouping:
    def __init__(self, xml_reader_instance=None, additional_values: Optional[Dict[str, Callable]] = None, global_filter: Filter = Filter("standart_filter",lambda c: c.votes <= 1000), filters=None):
        """
        Initialize with an XML reader and additional values
        Args:
            xml_reader_instance: An XML reader object that provides candidate data
            additional_values: Dictionary of {name: value_func} where value_func
                             takes a candidate and returns computed value
            global_filter: Filter function for candidates (default: votes <= 1000)
            filters: List of Filter objects to initialize with
        """
        if xml_reader_instance is None:
            xml_reader_instance = xml_reader(filter=global_filter, additional_values=additional_values)
        else: 
            for val_names in additional_values.keys():
                xml_reader_instance.add_adtional_value(val_names,additional_values[val_names])
        self.xml_reader = xml_reader_instance
        self.filters = filters or []
        self.additional_values = additional_values or {}

    def add_filter(self, Filter):
        """
        Add a boolean filter function with optional name
        Args:
            filter_func: A function that takes a candidate and returns bool
            name: Optional name for this filter group (default: filter_func.__name__)
        """
        self.filters.append(Filter)

    def get_candidates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get candidates split into groups based on which filters they pass
        Returns:
            Dictionary with filter names as keys and lists of candidates as values
            Each candidate includes original data plus computed additional values
        """
        # Initialize result dictionary with empty lists for each filter
        result = {f.name: [] for f in self.filters}
  # Candidates that don't pass any filter

        for candidate in self.xml_reader:
            # Check which filters this candidate passes
            passed_filters = []
            for filter_obj in self.filters:
                if filter_obj(candidate):
                    passed_filters.append(filter_obj.name)

            # Add to appropriate groups
            if passed_filters:
                for filter_name in passed_filters:
                    result[filter_name].append({'candidate': candidate})

  

        return result

    def plot(self, y_axis: str = "log_votes", use_log: bool = False, colors: Optional[Dict[str, str]] = None):
        """
        Plot candidates based on the specified y-axis variable
        Args:
            y_axis: Variable to plot on y-axis (can be 'votes', 'log_votes', or any additional value key)
            use_log: Whether to use logarithmic scale for the y-axis
            colors: Dictionary mapping party codes to colors (default: Danish party colors)
        """
        # Default Danish party colors (from Wikipedia)
        danish_party_colors = {
            'A': '#AF0D0D',  # Socialdemokraterne
            'V': '#01438E',  # Venstre
            'C': '#729B0D',  # Konservative
            'B': '#7A1898',  # Radikale Venstre
            'F': '#D91E18',  # Socialistisk Folkeparti
            'O': '#FCD03B',  # Dansk Folkeparti
            'Ø': '#F7660D',  # Enhedslisten
            'I': '#3FB2BE',  # Liberal Alliance
            'Å': '#00FF00',  # Alternativet
            'M': '#B48CD2',  # Moderaterne
            'Æ': "#6285aa",
            'H': "#11044D"
            
        }
        
        default_colors = colors or danish_party_colors
        
        results = self.get_candidates()
        
        plt.figure(figsize=(10, 6))
        
        # Create legend handles for each party
        legend_handles = []
        party_colors = {}
        
        for filter_name, candidates in results.items():
             if not candidates:
                 continue
             
             x_values = []
             y_values = []
             candidate_colors = []
             
             for candidate_data in candidates:
                 cand = candidate_data['candidate']
                 x_values.append(filter_name)
                 
                 if y_axis == "votes":
                     y_value = cand.votes
                 elif y_axis == "log_votes":
                     y_value = math.log(cand.votes) if cand.votes > 0 else 0
                 elif y_axis in cand.additional_values.keys():
                     y_value = cand.additional_values[y_axis]
                 else:
                     raise ValueError(f"Unknown y_axis variable: {y_axis}")
                 
                 y_values.append(y_value)
                 
                 # Get color based on party code
                 party_color = default_colors.get(cand.party_code, '#808080')  # Default to gray
                 candidate_colors.append(party_color)
                 
                 # Track party colors for legend
                 if cand.party_code not in party_colors:
                     party_colors[cand.party_code] = party_color
             
             plt.scatter(x_values, y_values, alpha=0.6, c=candidate_colors)
        
         # Add legend entries for each party
        for party_code, color in party_colors.items():
             legend_handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=8, label=f"{party_code}"))
         
        if use_log:
             plt.yscale('log')
          
        plt.xlabel('Filter Group')
        plt.ylabel(y_axis)
        plt.title(f'Candidate {y_axis} by Filter Group')
        plt.legend(handles=legend_handles)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    def test_filter_vote_difference(self, filter_name: str) -> Dict[str, Any]:
        """
        Test if people from the given filter group get more votes than other groups
        Args:
            filter_name: Name of the filter to test against others
        Returns:
            Dictionary with p-values for comparisons between the specified filter group and all other groups
        """
        results = self.get_candidates()
        
        if filter_name not in results or not results[filter_name]:
            raise ValueError(f"Filter '{filter_name}' not found or has no candidates")
        
        # Get votes for the specified filter group
        filter_group_votes = [cand['candidate'].votes for cand in results[filter_name]]
        
        p_values = {}
        
        # Compare with each other group
        for other_group_name, other_candidates in results.items():
            if other_group_name == filter_name or not other_candidates:
                continue
            
            other_group_votes = [cand['candidate'].votes for cand in other_candidates]
            
            # Perform t-test
            try:
                t_statistic, p_value = stats.ttest_ind(
                    filter_group_votes,
                    other_group_votes,
                    equal_var=False
                )
                p_values[other_group_name] = {
                    'p_value': p_value,
                    't_statistic': t_statistic,
                    'filter_mean': sum(filter_group_votes) / len(filter_group_votes) if filter_group_votes else 0,
                    'other_mean': sum(other_group_votes) / len(other_group_votes) if other_group_votes else 0,
                    'filter_count': len(filter_group_votes),
                    'other_count': len(other_group_votes)
                }
            except (ValueError, ZeroDivisionError):
                # Handle cases where t-test cannot be performed
                p_values[other_group_name] = {
                    'p_value': None,
                    't_statistic': None,
                    'filter_mean': sum(filter_group_votes) / len(filter_group_votes) if filter_group_votes else 0,
                    'other_mean': sum(other_group_votes) / len(other_group_votes) if other_group_votes else 0,
                    'filter_count': len(filter_group_votes),
                    'other_count': len(other_group_votes),
                    'error': 'Insufficient data for t-test'
                }
        
        return p_values


class xml_reader():
    def __init__(self, filter=lambda x: True, additional_values=None):
        self.__voting_place_reults = {}
        self.__all_candidate_names_cache = None
        self.__candidate_cache = {}
        self.__filter = filter
        self.additional_values = additional_values or {}

    def add_adtional_value(self,key,func):
        self.additional_values[key]=func

    def __iter__(self):
        for name in self.get_all_candidate_names():
            yield self.get_candidate(name)
   
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
            print(self.__all_candidate_names_cache)
            return self.__all_candidate_names_cache
        
        # Dictionary to accumulate votes and store candidate data
        candidate_data = {}
        base_path = Path("Data/dst_xml_downloads/Afstemningsomraader")
        
        for voting_place_dir in base_path.iterdir():
            if voting_place_dir.is_dir():
                xml_paths = self.__voting_place_to_xml(voting_place_dir.name)
                for xml_path in xml_paths:
                    self.__process_xml_file_for_candidates(xml_path, candidate_data)
        
        # Create all candidate objects and cache them
        filtered_names = []
        for normalized_name, data in candidate_data.items():
            
                # Create candidate object
                candidate_instance = candidate(
                    party_code=data['party_code'],
                    votes=data['votes'],
                    storkreds=data['storkreds'],
                    name=normalized_name
                )
                
                # Apply filter and cache if it passes
                temp_candidate=candidate_instance.copy()
                temp_candidate.additional_values=self.additional_values
                if self.__filter(temp_candidate):
                    self.__candidate_cache[normalized_name] = candidate_instance
                    filtered_names.append(normalized_name)
            
                # Skip candidates that can't be created or don't pass filter
                
        
        self.__all_candidate_names_cache = filtered_names
        return self.__all_candidate_names_cache
    
    def __process_xml_file_for_candidates(self, xml_path, candidate_data):
        """Process an XML file to extract and accumulate candidate data"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Skipping invalid XML: {xml_path} ({e})")
            return
        
        # First pass: extract party codes and storkreds from Parti elements
        party_info = {}
        for elem in root.iter():
            if self.__local_name(elem.tag) == "Parti":
                party_code = elem.attrib.get("Bogstav", "")
                for person_elem in elem:
                    if self.__local_name(person_elem.tag) == "Person":
                        name = extract_candidate_name(person_elem)
                        if name:
                            normalized_name = self.__normalize_name(name)
                            party_info[normalized_name] = party_code
            
            elif self.__local_name(elem.tag) == "Sted":
                sted_type = elem.attrib.get("Type", "")
                sted_text = elem.text or ""
                storkreds = f"{sted_type}: {sted_text}" if sted_type else sted_text
                for child in elem.iter():
                    if self.__local_name(child.tag) == "Person":
                        name = extract_candidate_name(child)
                        if name:
                            normalized_name = self.__normalize_name(name)
                            if normalized_name not in party_info:
                                party_info[normalized_name] = ""
        
        # Second pass: extract votes and create candidate data
        for elem in root.iter():
            if self.__local_name(elem.tag) == "Person":
                name = extract_candidate_name(elem)
                if name:
                    normalized_name = self.__normalize_name(name)
                    votes = extract_person_votes(elem)
                    
                    # Initialize candidate data if not exists
                    if normalized_name not in candidate_data:
                        candidate_data[normalized_name] = {
                            'votes': 0,
                            'party_code': party_info.get(normalized_name, ""),
                            'storkreds': ""
                        }
                    
                    # Accumulate votes
                    candidate_data[normalized_name]['votes'] += votes
                    
                    # Set party code if available
                    if not candidate_data[normalized_name]['party_code'] and normalized_name in party_info:
                        candidate_data[normalized_name]['party_code'] = party_info[normalized_name]
            
            elif self.__local_name(elem.tag) == "Parti":
                if "Bogstav" not in elem.attrib:
                    parti_name = elem.attrib.get("navn", "")
                    if parti_name:
                        normalized_parti_name = self.__normalize_name(parti_name)
                        votes = int(elem.attrib.get("PersonligeStemmer", "0"))
                        if normalized_parti_name not in candidate_data:
                            candidate_data[normalized_parti_name] = {
                                'votes': 0,
                                'party_code': "",
                                'storkreds': ""
                            }
                        candidate_data[normalized_parti_name]['votes'] += votes
    #TODO apply filter
    @add_additional_values
    def get_candidate(self, candidate_name):
        normalized_name = self.__normalize_name(candidate_name)
        if normalized_name in self.__candidate_cache:
            return self.__candidate_cache[normalized_name]
        
        votes = self.get_candidate_votes(candidate_name)
        party_code = self.__get_candidate_party_code(normalized_name)
        storkreds = self.__get_candidate_storkreds(normalized_name)
        candidate_instance = candidate(party_code=party_code, votes=votes, storkreds=storkreds, name=normalized_name)
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

    @handle_multiple_xml_paths
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

    @handle_multiple_xml_paths
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


class CSVAnswerReader:
    def __init__(self, csv_path: Path = Path("Data/Output_renset.csv")):
        self.csv_path = csv_path
        self.csv_data = self._load_csv_data()

    def _load_csv_data(self) -> List[Dict[str, str]]:
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def get_answers_for_candidate(self, candidate: candidate) -> Dict[str, int]:
        full_name = f"{candidate.name}"
        for row in self.csv_data:
            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()
            row_full_name = f"{first_name} {last_name}"
            if normalize_name(row_full_name) == normalize_name(full_name):
                return {f"Q{i}": int(row.get(f"Q{i}", 0)) for i in range(1, 26)}
        return {}

    def __call__(self, f_1: Callable[[Dict[str, int]], Any]) -> Callable[[candidate], Any]:
        def f_2(candidate: candidate) -> Any:
            answers = self.get_answers_for_candidate(candidate)
            return f_1(answers)
        return f_2


def normalize_name(name: str) -> str:
    name = name.strip()
    name = name.replace(".", "")
    name = name.replace(",", "")
    name = re.sub(r"\s+", " ", name)
    return name.casefold()



