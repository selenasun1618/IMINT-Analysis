import os
import json
import pandas as pd
from openai import OpenAI
from pathlib import Path

client = OpenAI(api_key="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")

def load_reasoning_traces():
    """Load reasoning traces from Chinese_facilities.csv"""
    csv_path = "../coordinates/Chinese_facilities.csv"
    df = pd.read_csv(csv_path)
    
    # Create a mapping from facility name to reasoning trace
    reasoning_map = {}
    for _, row in df.iterrows():
        if pd.notna(row['Reasoning Trace']):
            # Extract facility name and create a simplified key
            facility_name = row['Name'].replace('/', '_').replace('-', '_')
            reasoning_map[facility_name] = row['Reasoning Trace']
    
    return reasoning_map

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image, double fence presence, and explanations."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_train_combined/"
    local_dir = "../IMINT-Images/Double-Fences/"
    double_fences_local_folder = "yes_df_train/"
    no_double_fences_local_folder = "no_df_train/"

    # Load reasoning traces from CSV
    reasoning_map = load_reasoning_traces()
    
    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:
        # Process double fences images
        df_path = os.path.join(local_dir, double_fences_local_folder)
        for img_name in os.listdir(df_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Try to match image name to facility for explanation
                explanation = "conspicuous checkpoint where double fencing seen as two dark, straight, parallel lines breaks"
                
                # Try to find matching reasoning trace
                img_base = img_name.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')
                for facility_key, reasoning in reasoning_map.items():
                    if any(part in img_base for part in facility_key.split('_')):
                        explanation = reasoning
                        break
                
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Classify whether the following satellite image contains double fences and provide an explanation. Respond with JSON: {\"double_fences_present\": \"yes\" or \"no\", \"explanation\": \"your reasoning\"}."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"{github_url}{img_name}?raw=true"
                                    }
                                }
                            ]
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({
                                "double_fences_present": "yes",
                                "explanation": explanation
                            })
                        }
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process no double fences images
        no_df_path = os.path.join(local_dir, no_double_fences_local_folder)
        for img_name in os.listdir(no_df_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                explanation = "urban area with roads and buildings but no visible double fencing structures or parallel lines characteristic of security perimeters"
                
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Classify whether the following satellite image contains double fences and provide an explanation. Respond with JSON: {\"double_fences_present\": \"yes\" or \"no\", \"explanation\": \"your reasoning\"}."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"{github_url}{img_name}?raw=true"
                                    }
                                }
                            ]
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({
                                "double_fences_present": "no",
                                "explanation": explanation
                            })
                        }
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

    print(f"✅ JSONL file created at '{jsonl_path}' with {total_written} entries.")

def main():
    jsonl_path = Path("double_fences_training_with_explanations.jsonl").resolve()
    print(f"Creating JSONL file at: {jsonl_path}")
    create_jsonl_file(jsonl_path)

if __name__ == "__main__":
    main()
