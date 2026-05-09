import sys
sys.path.insert(0, 'Tools')

from vote_group_comparison import xml_reader, CandidateGrouping

def test_katrine_kjaer_robsue_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Katrine Robsøe")
    assert votes == 6406, f"Expected Katrine Robsøe to have 6406 votes, but got {votes}"
    print("Test passed: Katrine Robsøe has 6406 votes")

def test_mercedes_czank_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Mercedes Czank")
    assert votes == 156, f"Expected Mercedes Czank to have 156 votes, but got {votes}"
    print("Test passed: Mercedes Czank has 156 votes")

def test_soren_skjold_andersen_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Søren Skjold Andersen")
    assert votes == 158, f"Expected Søren Skjold Andersen to have 158 votes, but got {votes}"
    print("Test passed: Søren Skjold Andersen has 158 votes")

def test_stephanie_lose_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Stephanie Lose")
    assert votes == 31008, f"Expected Stephanie Lose to have 31008 votes, but got {votes}"
    print("Test passed: Stephanie Lose has 31008 votes")

def test_bjorn_kristoffersen_brandenborg_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Bjørn Brandenborg")
    assert votes == 12098, f"Expected Bjørn Brandenborg to have 12098 votes, but got {votes}"
    print("Test passed: Bjørn Brandenborg has 12098 votes")

def test_morten_messerschmidt_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Morten Messerschmidt")
    assert votes == 50819, f"Expected Morten Messerschmidt to have 50819 votes, but got {votes}"
    print("Test passed: Morten Messerschmidt has 50819 votes")

def test_jacob_krzyrosiak_mark_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Jacob Mark")
    assert votes == 12139, f"Expected Jacob Mark to have 12139 votes, but got {votes}"
    print("Test passed: Jacob Mark has 12139 votes")

def test_mattias_tesfaye_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Mattias Tesfaye")
    assert votes == 11898, f"Expected Mattias Tesfaye to have 11898 votes, but got {votes}"
    print("Test passed: Mattias Tesfaye has 11898 votes")

def test_pelle_dragsted_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Pelle Dragsted")
    assert votes == 30707, f"Expected Pelle Dragsted to have 30707 votes, but got {votes}"
    print("Test passed: Pelle Dragsted has 30707 votes")

def test_mette_frederiksen_votes():
    reader = xml_reader()
    votes = reader.get_candidate_votes("Mette Frederiksen")
    assert votes == 41721, f"Expected Mette Frederiksen to have 41721 votes, but got {votes}"
    print("Test passed: Mette Frederiksen has 41721 votes")


def test_a_vs_aa_vote_difference():
    """Test if A candidates get more votes than Å candidates with p-value < 0.05"""
    reader = xml_reader()
    grouper = CandidateGrouping(xml_reader_instance=reader)
    
    # Add filters for party A and Å
    grouper.add_filter(lambda c: c.party_code == 'A', name='A')
    grouper.add_filter(lambda c: c.party_code == 'Å', name='Å')
    
    # Test the vote difference
    results = grouper.test_filter_vote_difference('A')
    
    # Check if Å is in the results and has a p-value < 0.05
    assert 'Å' in results, "Å group not found in results"
    assert results['Å']['p_value'] is not None, "P-value for Å comparison is None"
    assert results['Å']['p_value'] < 0.05, f"P-value {results['Å']['p_value']} is not < 0.05"
    print(f"Test passed: A candidates get more votes than Å candidates (p-value: {results['Å']['p_value']:.6f})")


def test_a_vs_a_same_party():
    """Test that A candidates compared with A candidates have p-value of 1"""
    reader = xml_reader()
    grouper = CandidateGrouping(xml_reader_instance=reader)
    
    # Add the same filter for party A with two different names
    grouper.add_filter(lambda c: c.party_code == 'A', name='A_group1')
    grouper.add_filter(lambda c: c.party_code == 'A', name='A_group2')
    
    # Test the vote difference between the two identical A groups
    results = grouper.test_filter_vote_difference('A_group1')
    
    # Check if A_group2 is in the results
    assert 'A_group2' in results, "A_group2 not found in results"
    assert results['A_group2']['p_value'] is not None, "P-value for A_group2 comparison is None"
    assert results['A_group2']['p_value'] == 1, f"P-value {results['A_group2']['p_value']} should be close to 1 for identical groups"
    print(f"Test passed: A candidates vs A candidates have high p-value: {results['A_group2']['p_value']:.6f}")

def test_a_vs_a_same_party_under1000():
    """Test that A candidates compared with A candidates have p-value of 1"""
    grouper = CandidateGrouping()
    
    # Add the same filter for party A with two different names
    grouper.add_filter(lambda c: c.party_code == 'A', name='A_group1')
    grouper.add_filter(lambda c: c.party_code == 'A', name='A_group2')
    
    # Test the vote difference between the two identical A groups
    results = grouper.test_filter_vote_difference('A_group1')
    
    # Check if A_group2 is in the results
    assert 'A_group2' in results, "A_group2 not found in results"
    assert results['A_group2']['p_value'] is not None, "P-value for A_group2 comparison is None"
    assert results['A_group2']['p_value'] == 1, f"P-value {results['A_group2']['p_value']} should be close to 1 for identical groups"
    print(f"Test passed: A candidates vs A candidates have high p-value: {results['A_group2']['p_value']:.6f}")

def test_a_vs_aa_vote_difference_under_1000():
    """Test if A candidates get more votes than Å candidates with p-value < 0.05"""
    grouper = CandidateGrouping()
    
    # Add filters for party A and Å
    grouper.add_filter(lambda c: c.party_code == 'A', name='A')
    grouper.add_filter(lambda c: c.party_code == 'Å', name='Å')
    
    # Test the vote difference
    results = grouper.test_filter_vote_difference('A')
    
    # Check if Å is in the results and has a p-value < 0.05
    assert 'Å' in results, "Å group not found in results"
    assert results['Å']['p_value'] is not None, "P-value for Å comparison is None"
    assert results['Å']['p_value'] < 0.05, f"P-value {results['Å']['p_value']} is not < 0.05"
    print(f"Test passed: A candidates get more votes than Å candidates (p-value: {results['Å']['p_value']:.6f})")    

if __name__ == "__main__":
    
    test_katrine_kjaer_robsue_votes()
    test_mercedes_czank_votes()
    test_soren_skjold_andersen_votes()
    test_stephanie_lose_votes()
    test_bjorn_kristoffersen_brandenborg_votes()
    test_morten_messerschmidt_votes()
    test_jacob_krzyrosiak_mark_votes()
    test_mattias_tesfaye_votes()
    test_pelle_dragsted_votes()
    test_mette_frederiksen_votes()
    test_a_vs_aa_vote_difference()
    test_a_vs_a_same_party()
    test_a_vs_a_same_party_under1000()
    test_a_vs_aa_vote_difference_under_1000()