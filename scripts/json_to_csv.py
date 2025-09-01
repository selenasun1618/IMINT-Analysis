import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Union

def flatten_json(data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested JSON object into a single level dictionary.
    
    Args:
        data: JSON object to flatten
        parent_key: Parent key for nested objects
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(flatten_json(value, new_key, sep=sep).items())
            elif isinstance(value, list):
                # Handle arrays by creating indexed keys
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(flatten_json(item, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{sep}{i}", item))
            else:
                items.append((new_key, value))
    
    return dict(items)

def load_jsonl(file_path: str) -> List[Dict]:
    """Load JSONL file (one JSON object per line)."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def extract_eval_columns(data: List[Dict]) -> List[Dict]:
    """
    Extract specific columns for eval analysis and rename them.
    
    Args:
        data: List of flattened eval data
    
    Returns:
        List of dictionaries with extracted and renamed columns
    """
    extracted_data = []
    
    for item in data:
        # Extract model output JSON
        model_output_str = item.get('sample_outputs_0_content', '{}')
        try:
            model_output = json.loads(model_output_str)
        except json.JSONDecodeError:
            model_output = {}
        
        # Create new row with renamed columns
        row = {
            'human_label': item.get('item_double_fences_present', ''),
            'human_explanation': item.get('item_expected_explanation', ''),
            'image_name': item.get('item_image_name', ''),
            'image_url': item.get('item_image_url', ''),
            'model_label': model_output.get('double_fences_present', ''),
            'model_explanation': model_output.get('explanation', '')
        }
        
        extracted_data.append(row)
    
    return extracted_data

def json_to_csv_manual(json_file: str, csv_file: str, flatten: bool = True, extract_eval: bool = False):
    """
    Convert JSON to CSV using manual CSV writer (for simple data).
    
    Args:
        json_file: Path to input JSON file
        csv_file: Path to output CSV file
        flatten: Whether to flatten nested objects
        extract_eval: Whether to extract specific eval columns
    """
    # Determine if it's JSONL or regular JSON
    if json_file.endswith('.jsonl'):
        data = load_jsonl(json_file)
    else:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    # Flatten data if requested
    if flatten:
        data = [flatten_json(item) for item in data]
    
    # Extract specific eval columns if requested
    if extract_eval:
        data = extract_eval_columns(data)
        headers = ['human_label', 'human_explanation', 'image_name', 'image_url', 'model_label', 'model_explanation']
    else:
        # Get all unique keys for headers
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        headers = sorted(list(all_keys))
    
    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for item in data:
            if isinstance(item, dict):
                if extract_eval:
                    # Data is already processed
                    writer.writerow(item)
                else:
                    # Fill missing keys with empty strings and handle complex values
                    row = {}
                    for key in headers:
                        value = item.get(key, '')
                        # Convert complex types to strings
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        row[key] = value
                    writer.writerow(row)
    
    print(f"✅ Converted {json_file} to {csv_file}")
    print(f"   Rows: {len(data)}, Columns: {len(headers)}")

def convert_file(json_file_path: str, flatten: bool = True, extract_eval: bool = False):
    """
    Convert a JSON/JSONL file to CSV in the same directory.
    
    Args:
        json_file_path: Path to the JSON/JSONL file
        flatten: Whether to flatten nested objects
        extract_eval: Whether to extract specific eval columns
    """
    json_path = Path(json_file_path)
    
    # Create CSV filename in the same directory
    if extract_eval:
        csv_file = json_path.parent / f"{json_path.stem}_eval_analysis.csv"
    else:
        csv_file = json_path.parent / f"{json_path.stem}.csv"
    
    json_to_csv_manual(str(json_path), str(csv_file), flatten, extract_eval)
    return str(csv_file)

def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON/JSONL files to CSV format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python json_to_csv.py data.json
  python json_to_csv.py data.jsonl
  python json_to_csv.py data.json --no-flatten
  python json_to_csv.py eval_results.jsonl --extract-eval
  python json_to_csv.py data.json --output custom_output.csv
        """
    )
    
    parser.add_argument("json_file", help="Input JSON/JSONL file path")
    parser.add_argument("--output", "-o", help="Output CSV file path (optional, defaults to same folder as input)")
    parser.add_argument("--no-flatten", action="store_true", 
                       help="Don't flatten nested objects")
    parser.add_argument("--extract-eval", action="store_true", default=True,
                       help="Extract specific eval columns (human_label, model_label, etc.)")
    
    args = parser.parse_args()
    
    # Validate input file
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"❌ Error: JSON file '{args.json_file}' not found")
        return
    
    # Determine output file
    if args.output:
        csv_file = args.output
        # Create output directory if needed
        csv_path = Path(csv_file)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Use same directory as input file
        if args.extract_eval:
            csv_file = json_path.parent / f"{json_path.stem}_eval_analysis.csv"
        else:
            csv_file = json_path.parent / f"{json_path.stem}.csv"
    
    # Convert
    flatten = not args.no_flatten
    
    try:
        json_to_csv_manual(args.json_file, str(csv_file), flatten, args.extract_eval)
    except Exception as e:
        print(f"❌ Error converting JSON to CSV: {e}")

# Convenience function for programmatic use
def convert_json_to_csv(json_file_path: str, flatten: bool = True, extract_eval: bool = False) -> str:
    """
    Convert a JSON/JSONL file to CSV format in the same directory.
    
    Args:
        json_file_path: Path to the JSON/JSONL file
        flatten: Whether to flatten nested objects (default: True)
        extract_eval: Whether to extract specific eval columns (default: False)
    
    Returns:
        Path to the created CSV file
    """
    return convert_file(json_file_path, flatten, extract_eval)

if __name__ == "__main__":
    main()
