import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from Tools.vote_group_comparison import xml_reader, CandidateGrouping, CSVAnswerReader, candidate, Filter
from Data_analysis.x_m_l_votes_aggregator import make_filter_functions, CandidateGroupAnalyzer_fetures


def test_make_filter_functions_captures_values_correctly():
    """Test that make_filter_functions creates filters with unique captured values."""
    name = "Q3"
    posible_values = [1, 2, 4, 5]
    filters = make_filter_functions(name, posible_values)
    
    # Check that we have the correct number of filters
    assert len(filters) == len(posible_values), f"Expected {len(posible_values)} filters, got {len(filters)}"
    
    # Check that each filter has the correct name
    for i, val in enumerate(posible_values):
        assert filters[i].name == f"filter_{val}", f"Expected filter name 'filter_{val}', got '{filters[i].name}'"
    
    print("Test passed: make_filter_functions creates correct filter names")


def test_make_filter_functions_lambda_captures_correctly():
    """Test that each lambda in the filters captures its own value."""
    name = "Q3"
    posible_values = [1, 2, 4, 5]
    filters = make_filter_functions(name, posible_values)
    
    # Create mock candidates with different Q3 values
    class MockCandidate:
        def __init__(self, q3_value):
            self.additional_values = {"Q3": q3_value}
    
    # Test each filter
    for i, val in enumerate(posible_values):
        mock_candidate = MockCandidate(q3_value=lambda x:val)
        assert filters[i](mock_candidate), f"Filter for value {val} failed for candidate with Q3={val}"
        
        # Test that the filter fails for other values
        for other_val in posible_values:
            if other_val != val:
                mock_candidate_other = MockCandidate(q3_value=lambda x:other_val)
                assert not filters[i](mock_candidate_other), f"Filter for value {val} incorrectly passed for candidate with Q3={other_val}"
    
    print("Test passed: make_filter_functions lambdas capture values correctly")


def test_csv_answer_reader_returns_callable():
    """Test that CSVAnswerReader returns a callable that works with candidates."""
    reader = CSVAnswerReader()
    
    # Test with a simple function that extracts Q3
    def extract_q3(answers):
        return answers.get("Q3", 0)
    
    callable_func = reader(extract_q3)
    
    # Create a mock candidate
    mock_candidate = candidate(party_code="A", votes=100, storkreds="test")
    
    # Mock the get_answers_for_candidate method to return a known value
    original_get_answers = reader.get_answers_for_candidate
    reader.get_answers_for_candidate = lambda c: {"Q3": 4}
    
    try:
        result = callable_func(mock_candidate)
        assert result == 4, f"Expected callable to return 4, got {result}"
        print("Test passed: CSVAnswerReader returns a working callable")
    finally:
        reader.get_answers_for_candidate = original_get_answers


def test_candidate_grouping_with_filters():
    """Test that CandidateGrouping correctly groups candidates based on filters."""
    # Create a mock xml_reader that yields candidates with additional_values
    class MockXMLReader:
        def __init__(self):
            self.additional_values = {}
        
        def __iter__(self):
            # Yield mock candidates with Q3 values
            candidates = [
                candidate(party_code="A", votes=100, storkreds="test", name="Candidate1"),
                candidate(party_code="A", votes=200, storkreds="test", name="Candidate2"),
                candidate(party_code="A", votes=300, storkreds="test", name="Candidate3"),
            ]
            # Manually set additional_values for each candidate
            for c in candidates:
                c.additional_values = {"Q3": lambda x:1 if c.name == "Candidate1" else 2 if c.name == "Candidate2" else 4}
                yield c
    
    # Create filters for Q3 values
    filters = make_filter_functions("Q3", [1, 2, 4])
    
    # Create CandidateGrouping with the mock reader and filters
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader(), filters=filters)
    
    # Get the grouped candidates
    results = grouper.get_candidates()
    
    # Check that candidates are grouped correctly
    assert "filter_1" in results, "filter_1 group not found"
    assert "filter_2" in results, "filter_2 group not found"
    assert "filter_4" in results, "filter_4 group not found"
    
    assert len(results["filter_1"]) == 1, f"Expected 1 candidate in filter_1, got {len(results['filter_1'])}"
    assert len(results["filter_2"]) == 1, f"Expected 1 candidate in filter_2, got {len(results['filter_2'])}"
    assert len(results["filter_4"]) == 1, f"Expected 1 candidate in filter_4, got {len(results['filter_4'])}"
    
    print("Test passed: CandidateGrouping correctly groups candidates with filters")


def test_candidate_grouping_plot_does_not_crash():
    """Test that CandidateGrouping.plot() does not crash with valid data."""
    # Create a mock xml_reader that yields candidates with additional_values
    class MockXMLReader:
        def __init__(self):
            self.additional_values = {}
        
        def __iter__(self):
            # Yield a single candidate to avoid empty plot
            c = candidate(party_code="A", votes=100, storkreds="test", name="TestCandidate")
            c.additional_values = {"Q3":lambda x: 1}
            yield c
    
    # Create filters for Q3 values
    filters = make_filter_functions("Q3", [1, 2, 4])
    
    # Create CandidateGrouping with the mock reader and filters
    grouper = CandidateGrouping(xml_reader_instance=MockXMLReader(), filters=filters)
    
    # This should not crash (though it may show an empty plot if no data matches)
    try:
        grouper.plot(y_axis="votes")
        print("Test passed: CandidateGrouping.plot() does not crash")
    except Exception as e:
        assert False, f"CandidateGrouping.plot() raised an exception: {e}"


def test_additional_values_propagation():
    """Test that additional_values are correctly propagated to candidates."""
    reader = xml_reader()
    
    # Define a simple function to extract Q3
    def extract_q3(answers):
        return answers.get("Q3", 0)
    
    # Create a CSVAnswerReader and get the callable
    csv_reader = CSVAnswerReader()
    q3_func = csv_reader(extract_q3)
    
    # Set additional_values on the reader
    reader.additional_values = {"Q3": q3_func}
    
    # Mock the get_answers_for_candidate method to return a known value
    original_get_answers = csv_reader.get_answers_for_candidate
    csv_reader.get_answers_for_candidate = lambda c: {"Q3": 3}
    
    try:
        # Get a candidate (this will use the @add_additional_values decorator)
        c = reader.get_candidate("Test Candidate")
        
        # Check that additional_values are set
        assert hasattr(c, "additional_values"), "Candidate does not have additional_values"
        assert "Q3" in c.additional_values, "Q3 not found in candidate's additional_values"
        
        # Check that the Q3 function is callable and returns the expected value
        q3_value = c.additional_values["Q3"](c)
        assert q3_value == 3, f"Expected Q3 value to be 3, got {q3_value}"
        
        print("Test passed: additional_values are correctly propagated to candidates")
    finally:
        csv_reader.get_answers_for_candidate = original_get_answers


if __name__ == "__main__":
    print("Running unit tests for x_m_l_votes_aggregator and related functions...\n")
    
    test_make_filter_functions_captures_values_correctly()
    test_make_filter_functions_lambda_captures_correctly()
    test_csv_answer_reader_returns_callable()
    test_candidate_grouping_with_filters()
    test_candidate_grouping_plot_does_not_crash()
    test_additional_values_propagation()
    
    print("\nAll tests passed!")
