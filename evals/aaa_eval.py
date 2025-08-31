import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from aaa_prompts import *
client = OpenAI(api_key="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")

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image and AAA presence."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/"
    local_dir = "../IMINT-Images/AAA/"
    AAA_local_folder = "aaa_test/"
    Non_AAA_local_folder = "non_aaa_test/"

    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:  # Overwrite on each run
        # Process AAA images
        aaa_path = os.path.join(local_dir, AAA_local_folder)
        for img_name in os.listdir(aaa_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "aaa_present": "yes",
                        "image_name": img_name,
                        "image_url": f"{github_url}{AAA_local_folder}{img_name}?raw=true",
                    }
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process Non-AAA images
        non_aaa_path = os.path.join(local_dir, Non_AAA_local_folder)
        for img_name in os.listdir(non_aaa_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "aaa_present": "no",
                        "image_name": img_name,
                        "image_url": f"{github_url}{Non_AAA_local_folder}{img_name}?raw=true",
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
        name="AAA Eval",
        data_source_config={
            "type": "custom",
            "item_schema": {
                "type": "object",
                "properties": {
                    "aaa_present": {"type": "string"},
                    "image_name": {"type": "string"},
                    "image_url": {"type": "image_url"},
                },
                "required": ["image_url", "aaa_present", "image_name"],
            },
            "include_sample_schema": True
        },
        testing_criteria=[
            {
                "name": "AAA classification grader",
                "type": "string_check",
                "input": "{{ sample.output_text.strip().lower() }}",
                "operation": "eq",
                "reference": "{{ item.aaa_present }}"
            }
        ],
    )
    return eval_obj


def run_eval(eval_id, file_id, user_prompt=ZERO_SHOT_PROMPT, model="gpt-4o-2024-08-06"):
    """Run the eval with the given ID and file path."""

    developer_prompt = """
    You are an expert nuclear analyst responsible for informing the U.S. government about the status of nuclear power plants.
    You are looking for anti-aircraft artillery (AAA) sites, which are indicators of nuclear power plants nearby.
    You are to decide whether the given image contains an AAA site or not.
    """

    eval_run = client.evals.runs.create(
        eval_id=eval_id,
        name="AAA Eval Run",
        data_source={
            "type": "completions",
            "model": model,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "aaa_presence",
                    "schema": {
                        "type": "string",
                        "enum": ["yes", "no"]
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
    jsonl_path = Path(f"evals/aaa_eval_test.jsonl").resolve()
    print(f"Creating JSONL file at: {jsonl_path}")
    create_jsonl_file(jsonl_path)
    file = upload_files(jsonl_path=jsonl_path)
    print(f"Jsonl file uploaded: {file.id}")

    # 3. Create the eval
    eval_obj = create_eval()
    print(f"Eval created: {eval_obj.id}")

    """
    Validation:
    Jsonl file uploaded: file-3QWWDHt7bQ5AJxLZ6vZZCa
    Eval created: eval_68b407abf6d08191bc0a0e79fe975389

    Test:
    Jsonl file uploaded: file-X4tkn9ycbZBASGJc2fHokF
    Eval created: eval_68b408808b9c8191b2f70d59b545f719
    """

    eval_obj_id = "eval_68b407abf6d08191bc0a0e79fe975389"

    # 4. Run the eval
    # model = "ft:gpt-4o-2024-08-06:vannevar-labs::Buk6Uyac"
    # # model = "gpt-4o-2024-08-06"
    # eval_run = run_eval(eval_id=eval_obj_id, file_id=file.id, user_prompt=FEW_SHOT_PROMPT, model=model)
    # print(f"Eval run started: {eval_run.id}")

    # run = client.evals.runs.retrieve(eval_id=eval_obj_id, run_id=eval_run.id)
    # print(f"Eval run status: {run.status}")

if __name__ == "__main__":
    main()