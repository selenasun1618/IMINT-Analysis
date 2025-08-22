import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image and AAA presence."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/"
    local_dir = "../IMINT-Images/"
    double_fences_local_folder = "double_fences_eval_images/"
    Non_double_fences_local_folder = "Non_double_fences_eval_images/"

    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:  # Overwrite on each run
        # Process double fences images
        double_fences_path = os.path.join(local_dir, double_fences_local_folder)
        for img_name in os.listdir(double_fences_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "double_fences_present": "yes",
                        "image_name": img_name,
                        "image_url": f"{github_url}{double_fences_local_folder}{img_name}?raw=true",
                    }
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process Non-double fences images
        non_double_fences_path = os.path.join(local_dir, Non_double_fences_local_folder)
        for img_name in os.listdir(non_double_fences_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "item": {
                        "double_fences_present": "no",
                        "image_name": img_name,
                        "image_url": f"{github_url}{Non_double_fences_local_folder}{img_name}?raw=true",
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


def run_eval(eval_id, file_id, model="gpt-4o-2024-08-06"):
    """Run the eval with the given ID and file path."""

    developer_prompt = """
    You are an expert nuclear analyst responsible for informing the U.S. government about the status of nuclear power plants.
    You are looking for double fences around buildings, which is an indicator that it's a nuclear site.
    You are to decide whether the given image contains double fences or not.
    """

    user_prompt = """
    Would you guess this iamge contains double fences?
    If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer. Here is the image:
    {{ item.image_url }}
    """
    # TODO - strutured output?

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
    jsonl_path = Path(f"evals/double_fences_eval.jsonl").resolve()
    print(f"Creating JSONL file at: {jsonl_path}")
    create_jsonl_file(jsonl_path)

    # 2. Upload the JSONL file to OpenAI
    jsonl_path = Path(f"evals/double_fences_eval.jsonl").resolve()
    file = upload_files(jsonl_path=jsonl_path)
    print(f"Jsonl file uploaded: {file.id}")

    # 3. Create the eval
    eval_obj = create_eval()
    print(f"Eval created: {eval_obj.id}")
    # eval_obj_id = # TODO

    # 4. Run the eval
    # model = "ft:gpt-4o-2024-08-06:vannevar-labs::Buk6Uyac"
    # model = "gpt-4o-2024-08-06"
    # eval_run = run_eval(eval_id=eval_obj_id, file_id=file.id, model=model)
    # print(f"Eval run started: {eval_run.id}")

    # run = client.evals.runs.retrieve(eval_id=eval_obj_id, run_id=eval_run.id)
    # print(f"Eval run status: {run.status}")

if __name__ == "__main__":
    main()