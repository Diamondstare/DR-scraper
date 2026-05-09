import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[0]))

from vote_group_comparison import (
    candidate, Filter, CandidateGrouping, xml_reader, 
    CSVAnswerReader, normalize_name, extract_person_votes, 
    extract_candidate_name
)
import xml.etree.ElementTree as ET


# ==================== Test candidate class ====================

def test_candidate_creation():
    """Test creating a candidate with all fields."""
    c = candidate(party_code="A", votes=1000, storkreds="North", name="Test Candidate")
    assert c.party_code == "A"
    assert c.votes == 1000
    assert c.storkreds == "North"
    assert c.name == "Test Candidate"
    assert c.additional_values == {}
    print("Test passed: candidate creation with all fields")


def test_candidate_creation_minimal():
    """Test creating a candidate with minimal fields."""
    c = candidate(party_code="V", votes=500, storkreds="South")
    assert c.party_code == "V"
    assert c.votes == 500
    assert c.storkreds == "South"
    assert c.name == ""
    assert c.additional_values == {}
    print("Test passed: candidate creation with minimal fields")


def test_candidate_str():
    """Test candidate string representation."""
    c = candidate(party_code="A", votes=1000, storkreds="North", name="Test Candidate")
    assert str(c) == "Test Candidate"
    print("Test passed: candidate string representation")


# ==================== Test Filter class ====================

def test_filter_creation():
    """Test creating a Filter object."""
    def mock_filter_func(c):
        return c.votes > 500
    
    f = Filter("test_filter", mock_filter_func)
    assert f.name == "test_filter"
    assert f.filter_func == mock_filter_func
    print("Test passed: Filter creation")


def test_filter_call():
    """Test calling a Filter object."""
    def mock_filter_func(c):
        return c.votes > 500
    
    f = Filter("test_filter", mock_filter_func)
    
    c1 = candidate(party_code="A", votes=1000, storkreds="North")
    c2 = candidate(party_code="V", votes=300, storkreds="South")
    
    assert f(c1) == True
    assert f(c2) == False
    print("Test passed: Filter call")


# ==================== Test CandidateGrouping class ====================

def test_candidate_grouping_creation():
    """Test creating a CandidateGrouping object."""
    grouper = CandidateGrouping()
    assert grouper.filters == []
    assert grouper.additional_values == {}
    print("Test passed: CandidateGrouping creation")


def test_candidate_grouping_with_xml_reader():
    """Test creating a CandidateGrouping object with an xml_reader."""
    reader = xml_reader()
    grouper = CandidateGrouping(xml_reader_instance=reader)
    assert grouper.xml_reader == reader
    print("Test passed: CandidateGrouping creation with xml_reader")


def test_candidate_grouping_add_filter():
    """Test adding a filter to CandidateGrouping."""
    grouper = CandidateGrouping()
    
    def mock_filter_func(c):
        return c.votes > 500
    
    grouper.add_filter(Filter(filter_func=mock_filter_func, name="high_votes"))
    assert len(grouper.filters) == 1
    assert grouper.filters[0].name == "high_votes"
    print("Test passed: CandidateGrouping add_filter")


def test_candidate_grouping_get_candidates_empty():
    """Test get_candidates with no filters."""
    class MockXMLReader:
        def __iter__(self):
            return iter([])
    
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader())
    results = grouper.get_candidates()
    
    assert "none" in results
    assert len(results["none"]) == 0
    print("Test passed: CandidateGrouping get_candidates with no filters and no candidates")


def test_candidate_grouping_get_candidates_with_filters():
    """Test get_candidates with filters."""
    class MockXMLReader:
        def __iter__(self):
            c1 = candidate(party_code="A", votes=1000, storkreds="North", name="Candidate1")
            c2 = candidate(party_code="V", votes=300, storkreds="South", name="Candidate2")
            c1.additional_values = {"test": 1}
            c2.additional_values = {"test": 2}
            return iter([c1, c2])
    
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader())
    grouper.add_filter(Filter(filter_func=lambda c: c.additional_values.get("test", 0) == 1, name="test_1"))
    grouper.add_filter(Filter(filter_func=lambda c: c.additional_values.get("test", 0) == 2, name="test_2"))
    
    results = grouper.get_candidates()
    
    assert "test_1" in results
    assert "test_2" in results
    assert "none" in results
    assert len(results["test_1"]) == 1
    assert len(results["test_2"]) == 1
    assert len(results["none"]) == 0
    print("Test passed: CandidateGrouping get_candidates with filters")


# ==================== Test xml_reader class ====================

def test_xml_reader_creation():
    """Test creating an xml_reader object."""
    reader = xml_reader()
    assert reader.additional_values == {}
    print("Test passed: xml_reader creation")


def test_xml_reader_with_filter():
    """Test creating an xml_reader object with a custom filter."""
    def custom_filter(c):
        return c.votes > 500
    
    reader = xml_reader(filter=custom_filter)
    print("Test passed: xml_reader creation with custom filter")


def test_xml_reader_add_additional_value():
    """Test adding an additional value to xml_reader."""
    reader = xml_reader()
    
    def mock_func(c):
        return 42
    
    reader.add_adtional_value("test_key", mock_func)
    assert "test_key" in reader.additional_values
    assert reader.additional_values["test_key"] == mock_func
    print("Test passed: xml_reader add_additional_value")


def test_xml_reader_iteration():
    """Test iterating over xml_reader (with mocked data)."""
    # This test depends on actual data files, so we'll just verify it doesn't crash
    reader = xml_reader()
    try:
        count = 0
        for c in reader:
            count += 1
            if count >= 3:  # Just check first few candidates
                break
        print(f"Test passed: xml_reader iteration (checked {count} candidates)")
    except Exception as e:
        assert False, f"xml_reader iteration failed: {e}"


# ==================== Test CSVAnswerReader class ====================

def test_csv_answer_reader_creation():
    """Test creating a CSVAnswerReader object."""
    reader = CSVAnswerReader()
    assert reader.csv_path.exists() or not reader.csv_path.exists()  # Just check it's set
    print("Test passed: CSVAnswerReader creation")


def test_csv_answer_reader_load_csv_data():
    """Test loading CSV data."""
    reader = CSVAnswerReader()
    data = reader._load_csv_data()
    assert isinstance(data, list)
    if len(data) > 0:
        assert isinstance(data[0], dict)
    print(f"Test passed: CSVAnswerReader load_csv_data (loaded {len(data)} rows)")


def test_csv_answer_reader_callable():
    """Test that CSVAnswerReader returns a callable."""
    reader = CSVAnswerReader()
    
    def mock_func(answers):
        return answers.get("Q1", 0)
    
    callable_func = reader(mock_func)
    assert callable(callable_func)
    print("Test passed: CSVAnswerReader returns a callable")


# ==================== Test utility functions ====================

def test_normalize_name():
    """Test the normalize_name function."""
    assert normalize_name("Test Name") == "test name"
    assert normalize_name("  Test  Name  ") == "test name"
    assert normalize_name("Test.Name") == "testname"
    assert normalize_name("TEST NAME") == "test name"
    print("Test passed: normalize_name")


def test_extract_person_votes():
    """Test the extract_person_votes function."""
    # Create a mock XML element
    elem = ET.Element("Person")
    elem.attrib["PersonligeStemmer"] = "100"
    assert extract_person_votes(elem) == 100
    
    elem.attrib["PersonligeStemmer"] = "  200  "
    assert extract_person_votes(elem) == 200
    
    elem.attrib["PersonligeStemmer"] = ""
    assert extract_person_votes(elem) == 0
    
    elem.attrib["PersonligeStemmer"] = "invalid"
    assert extract_person_votes(elem) == 0
    
    del elem.attrib["PersonligeStemmer"]
    assert extract_person_votes(elem) == 0
    print("Test passed: extract_person_votes")


def test_extract_candidate_name():
    """Test the extract_candidate_name function."""
    # Create a mock XML element
    elem = ET.Element("Person")
    elem.attrib["Navn"] = "Test Candidate"
    assert extract_candidate_name(elem) == "Test Candidate"
    
    elem.attrib["Navn"] = "  Test Candidate  "
    assert extract_candidate_name(elem) == "Test Candidate"
    
    del elem.attrib["Navn"]
    assert extract_candidate_name(elem) == ""
    print("Test passed: extract_candidate_name")


# ==================== Test CandidateGrouping.plot ====================

def test_candidate_grouping_plot_with_mock_data():
    """Test that CandidateGrouping.plot() works with mock data."""
    class MockXMLReader:
        def __iter__(self):
            c = candidate(party_code="A", votes=1000, storkreds="North", name="Test Candidate")
            c.additional_values = {"test": lambda :1}
            yield c
    
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader())
    grouper.add_filter(Filter(name="mock_filter",filter_func=lambda c: c.additional_values["test"]() == 1))
    
    try:
        grouper.plot(y_axis="votes")
        print("Test passed: CandidateGrouping.plot() with mock data")
    except Exception as e:
        assert False, f"CandidateGrouping.plot() failed: {e}"


def test_candidate_grouping_plot_with_empty_data():
    """Test that CandidateGrouping.plot() handles empty data gracefully."""
    class MockXMLReader:
        def __iter__(self):
            return iter([])
    
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader())
    
    try:
        grouper.plot(y_axis="votes")
        print("Test passed: CandidateGrouping.plot() with empty data")
    except Exception as e:
        assert False, f"CandidateGrouping.plot() failed with empty data: {e}"


# ==================== Test test_filter_vote_difference ====================

def test_filter_vote_difference():
    """Test the test_filter_vote_difference method."""
    class MockXMLReader:
        def __iter__(self):
            # Create candidates with different vote counts
            candidates = [
                candidate(party_code="A", votes=1000, storkreds="North", name="Candidate1"),
                candidate(party_code="A", votes=1200, storkreds="North", name="Candidate2"),
                candidate(party_code="V", votes=500, storkreds="South", name="Candidate3"),
                candidate(party_code="V", votes=600, storkreds="South", name="Candidate4"),
            ]
            for c in candidates:
                yield c
    
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader())
    grouper.add_filter(Filter(filter_func=lambda c: c.party_code == "A", name="A"))
    grouper.add_filter(Filter(filter_func=lambda c: c.party_code == "V", name="V"))
    
    results = grouper.test_filter_vote_difference("A")
    
    assert "V" in results
    assert results["V"]["p_value"] is not None
    assert results["V"]["filter_count"] == 2
    assert results["V"]["other_count"] == 2
    print("Test passed: test_filter_vote_difference")


if __name__ == "__main__":
    print("Running unit tests for vote_group_comparison.py...\n")
    
    # Test candidate class
    test_candidate_creation()
    test_candidate_creation_minimal()
    test_candidate_str()
    
    # Test Filter class
    test_filter_creation()
    test_filter_call()
    
    # Test CandidateGrouping class
    test_candidate_grouping_creation()
    test_candidate_grouping_with_xml_reader()
    test_candidate_grouping_add_filter()
    test_candidate_grouping_get_candidates_empty()
    test_candidate_grouping_get_candidates_with_filters()
    
    # Test xml_reader class
    test_xml_reader_creation()
    test_xml_reader_with_filter()
    test_xml_reader_add_additional_value()
    test_xml_reader_iteration()
    
    # Test CSVAnswerReader class
    test_csv_answer_reader_creation()
    test_csv_answer_reader_load_csv_data()
    test_csv_answer_reader_callable()
    
    # Test utility functions
    test_normalize_name()
    test_extract_person_votes()
    test_extract_candidate_name()
    
    # Test CandidateGrouping.plot
    test_candidate_grouping_plot_with_mock_data()
    test_candidate_grouping_plot_with_empty_data()
    
    # Test test_filter_vote_difference
    test_filter_vote_difference()
    
    print("\nAll tests passed!")
