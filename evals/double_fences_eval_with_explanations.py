import os
import json
from openai import OpenAI
from df_prompts_with_explanations import *
from pathlib import Path

client = OpenAI(api_key="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")

def create_jsonl_file(jsonl_path, dataset):
    """Create a JSONL file with the image, double fence presence, and expected explanations."""
    github_url = f"https://github.com/selenasun1618/IMINT-Images/blob/main/Double-Fences/df_{dataset}_combined/"
    local_dir = "../IMINT-Images/Double-Fences/"
    double_fences_local_folder = f"yes_df_{dataset}/"
    Non_double_fences_local_folder = f"no_df_{dataset}/"

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
                },
                "required": ["image_url", "double_fences_present", "image_name"],
            },
            "include_sample_schema": True
        },
        testing_criteria=[
            {
                "name": "Double Fences classification grader",
                "type": "string_check",
                "input": "{{ sample.output_json.double_fences_present }}",
                "operation": "eq",
                "reference": "{{ item.double_fences_present }}"
            }
        ],
    )
    return eval_obj


def run_eval(name,eval_id, file_id, user_prompt=PROMPT, model="gpt-4o-2024-08-06"):
    """Run the eval with the given ID and file path."""

    developer_prompt = """
    DO NOT RESPOND IN MARKDOWN!!!!! It is CRITICAL for national security purposes that you respond a JSON object only.
    """

    eval_run = client.evals.runs.create(
        eval_id=eval_id,
        name=name,
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

    # dataset = "test" # "test" or "val"
    # # 1. Create JSONL file

    # jsonl_path = Path(f"evals/double_fences_eval_with_explanations_{dataset}.jsonl").resolve()
    # print(f"Creating JSONL file at: {jsonl_path}")
    # create_jsonl_file(jsonl_path, dataset)
    # file = upload_files(jsonl_path=jsonl_path)
    # print(f"Jsonl file uploaded: {file.id}")

    # # # 2. Create the eval
    # eval_obj = create_eval()
    # print(f"Eval created: {eval_obj.id}")

    """
    Validation:
    Jsonl file uploaded: file-6kTU3fCzxDqr8X1B9ARFTZ

    Test:
    Jsonl file uploaded: file-JvorUASYQkp4oaeH814A24

    Eval created: eval_68b514bf138481919d532144091bebf7
    """
    # 3. Run the eval
    file_id = "file-6kTU3fCzxDqr8X1B9ARFTZ"
    eval_obj_id = "eval_68b514bf138481919d532144091bebf7"
    model = "gpt-4o-2024-08-06"
    eval_run = run_eval(name="Double Fences - No Guidance", eval_id=eval_obj_id, file_id=file_id, user_prompt=PROMPT_WITH_GUIDANCE, model=model)
    print(f"Eval run started: {eval_run.id}")

    run = client.evals.runs.retrieve(eval_id=eval_obj_id, run_id=eval_run.id)
    print(f"Eval run status: {run.status}")

if __name__ == "__main__":
    main()