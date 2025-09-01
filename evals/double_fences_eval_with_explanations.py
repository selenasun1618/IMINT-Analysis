import os
import json
from openai import OpenAI
from df_prompts_with_explanations import *
from pathlib import Path

client = OpenAI(api_key="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")

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image, double fence presence, and expected explanations."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_val_combined/"
    local_dir = "../IMINT-Images/Double-Fences/"
    double_fences_local_folder = "yes_df_val/"
    Non_double_fences_local_folder = "no_df_val/"

    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:
        # Process double fences images
        df_path = os.path.join(local_dir, double_fences_local_folder)
        for img_name in os.listdir(df_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "double_fences_present": "yes",
                        "image_name": img_name,
                        "image_url": f"{github_url}{img_name}?raw=true",
                        "expected_explanation": "should identify double fencing features like parallel lines, gates, checkpoints, or segmented shadows"
                    }
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process Non-double fences images
        non_df_path = os.path.join(local_dir, Non_double_fences_local_folder)
        for img_name in os.listdir(non_df_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "double_fences_present": "no",
                        "image_name": img_name,
                        "image_url": f"{github_url}{img_name}?raw=true",
                        "expected_explanation": "should explain absence of double fencing structures in urban/civilian areas"
                    }
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

    print(f"✅ JSONL file created at '{jsonl_path}' with {total_written} entries.")


def upload_files(jsonl_path):
    file = client.files.create(
        file=open(jsonl_path, "rb"),
        purpose="evals"
    )
    return file

def create_eval():
    eval_obj = client.evals.create(
        name="Double Fences Eval with Explanations",
        data_source_config={
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "double_fences_present": {"type": "string"},
                    "image_name": {"type": "string"},
                    "image_url": {"type": "string"},
                    "expected_explanation": {"type": "string"},
                },
                "required": ["image_url", "double_fences_present", "image_name"],
            },
            "include_sample_schema": True
        },
        testing_criteria=[
            {
                "name": "Double Fences classification grader",
                "type": "string_check",
                "input": "{{ sample.output_json.double_fences_present.strip().lower() }}",
                "operation": "eq",
                "reference": "{{ item.double_fences_present }}"
            }
        ],
    )
    return eval_obj


def run_eval(eval_id, file_id, user_prompt=ZERO_SHOT_PROMPT_WITH_EXPLANATIONS, model="gpt-4o-2024-08-06"):
    """Run the eval with the given ID and file path."""

    developer_prompt = """
    You are an expert satellite analyst responsible for informing the U.S. government about the status of nuclear power plants.
    You are looking for double fences around buildings, which is an indicator that it's a nuclear site.
    You are to decide whether the given image contains double fences or not and provide a detailed explanation.
    """

    eval_run = client.evals.runs.create(
        eval_id=eval_id,
        name="Double Fences Eval with Explanations Run",
        data_source={
            "type": "completions",
            "model": model,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "double_fences_with_explanation",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "double_fences_present": {"type": "string", "enum": ["yes", "no"]},
                            "explanation": {"type": "string"}
                        },
                        "required": ["double_fences_present", "explanation"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            "source": {"type": "file_id", "id": file_id},
            "input_messages": {
                "type": "template",
                "template": [
                    {
                        "role": "developer",
                        "content": developer_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            }
        }
    )

    return eval_run

def main():

    # 1. Create JSONL file
    jsonl_path = Path(f"evals/double_fences_eval_with_explanations.jsonl").resolve()
    print(f"Creating JSONL file at: {jsonl_path}")
    create_jsonl_file(jsonl_path)
    file = upload_files(jsonl_path=jsonl_path)
    print(f"Jsonl file uploaded: {file.id}")

    # 2. Create the eval
    eval_obj = create_eval()
    print(f"Eval created: {eval_obj.id}")

    # 3. Run the eval
    model = "gpt-4o-2024-08-06"
    eval_run = run_eval(eval_id=eval_obj.id, file_id=file.id, user_prompt=ZERO_SHOT_PROMPT_WITH_EXPLANATIONS, model=model)
    print(f"Eval run started: {eval_run.id}")

    run = client.evals.runs.retrieve(eval_id=eval_obj.id, run_id=eval_run.id)
    print(f"Eval run status: {run.status}")

if __name__ == "__main__":
    main()
