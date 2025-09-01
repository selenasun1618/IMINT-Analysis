#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from json_to_csv import json_to_csv_pandas
from pathlib import Path

def main():
    # Input JSONL file path
    jsonl_file = "/Users/selenasun/Projects/IMINT-Analysis/evals/eval_results/eval_items_OutputDataItemStatusParam.ALL_2025-09-01_01-52-03.jsonl"
    
    # Output CSV file in the same directory
    jsonl_path = Path(jsonl_file)
    csv_file = jsonl_path.parent / f"{jsonl_path.stem}.csv"
    
    print(f"Converting {jsonl_file}")
    print(f"Output: {csv_file}")
    
    # Convert using the existing function
    json_to_csv_pandas(str(jsonl_file), str(csv_file), flatten=True)

if __name__ == "__main__":
    main()
