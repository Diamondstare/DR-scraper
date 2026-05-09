import csv
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any, Dict, List, Optional, Tuple
from scipy import stats
import matplotlib.pyplot as plt
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root)) 
from  Tools.vote_group_comparison import xml_reader, CandidateGrouping,CSVAnswerReader


class CandidateGroupAnalyzer_fetures:
    answer_to_n_values=[1,2,4,5]
    def answer_to_n(n):
        def func(answers):
            return(answers[f"Q{n}"])
        return  func
    extreme_votes_posible_values=[i for i in range(26)]
    def extreme_votes():
        def func(answers):  
            total=0
            for i in range(1,25):
                if answers[f"Q{i}"]==1 or answers[f"Q{i}"]==5:
                    total+=1
            return total
        return func
    
def make_filter_functions(name, posible_values):
    from Tools.vote_group_comparison import Filter
    filter_list=[]
    for posible_value in posible_values:
        def filter_func(c,val=posible_value):
            try:
                return c.additional_values[name](c) ==val
            except:
                return False
        filter_list.append(Filter(f'{posible_value}', filter_func))
    return filter_list 
class CandidateGroupAnalyzer:
    def __init__(self, global_filter: Callable = lambda c: c.votes <= 1000):
        self.global_filter = global_filter
        self.xml_reader = xml_reader(filter=global_filter)
        self.csv_answer_reader = CSVAnswerReader()
    def plot(self,feturex):
         if  feturex in [(f"Q{i}") for i in range(1,26)]:
             feture_func=self.csv_answer_reader(CandidateGroupAnalyzer_fetures.answer_to_n(int(feturex[1])))
             posible_values=CandidateGroupAnalyzer_fetures.answer_to_n_values
             additional_values={feturex:feture_func}
         if feturex=="extreme":
             feture_func=self.csv_answer_reader(CandidateGroupAnalyzer_fetures.extreme_votes())
             posible_values=CandidateGroupAnalyzer_fetures.extreme_votes_posible_values
             additional_values={feturex:feture_func}

         gruoping=CandidateGrouping(self.xml_reader, additional_values=additional_values, filters=make_filter_functions(feturex, posible_values))
         gruoping.plot()
_=CandidateGroupAnalyzer()
_.plot("Q2")
_.plot("extreme")