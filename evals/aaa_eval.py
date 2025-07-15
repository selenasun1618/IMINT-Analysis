import base64
import json
import mimetypes
from pathlib import Path
from openai import OpenAI
client = OpenAI(api_key="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")


def create_jsonl_file():
    """Create a JSONL file with the image and AAA presence."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/google_earth_images/"
    file_path = Path("evals/aaa_eval.jsonl").resolve()

def upload_files(jsonl_path):
    file = client.files.create(
        file=open(jsonl_path, "rb"),
        purpose="evals"
    )
    return file

def create_eval():
    # Create eval
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
                "input": "{{ sample.output_text }}",
                "operation": "eq",
                "reference": "{{ item.aaa_present }}"
            }
        ],
    )
    return eval_obj


def run_eval(eval_id, file_id):
    """Run the eval with the given ID and file path."""

    developer_prompt = """
    You are an expert nuclear analyst responsible for informing the U.S. government about the status of nuclear power plants.
    You are looking for anti-aircraft artillery (AAA) sites, which are indicators of nuclear power plants nearby.
    You are to decide whether the given image contains an AAA site or not.
    """

    user_prompt = """
    Would you guess this iamge contains an anti-aircraft artillery (AAA) site?
    If yes, answer "yes". If no, answer "no". ONLY stick to "yes" or "no" as your answer. Here is the image:
    {{ item.image_url }}
    """
    # TODO - strutured output?

    eval_run = client.evals.runs.create(
        eval_id=eval_id,
        name="AAA Eval Run",
        data_source={
            "type": "completions",
            "model": "gpt-4o-2024-08-06", # Vision fine-tuning (https://platform.openai.com/docs/guides/vision-fine-tuning)
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
    # Upload the image file
    img_name = "google_earth_images/AAA_0.5km_images/AAA_39.43296_125.93912_0.5km.png"
    jsonl_path = Path("evals/aaa_eval.jsonl").resolve()
    print(f"Creating JSONL file at: {jsonl_path}")

    # # Try uploading the image beforehand
    # img_file = upload_image(img_name)
    # content = client.files.content(img_file.id)

    record = {
        "item": {
            "aaa_present": "no",
            "image_name": img_name,
            "image_url": "https://github.com/selenasun1618/IMINT-Images/blob/main/google_earth_images/AAA_0.5km_images/AAA_(e)_37.96253_126.64923_0.5km.png?raw=true",
        }
    }
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")

    file = upload_files(jsonl_path=jsonl_path)
    print(f"File uploaded: {file.id}")

    # Create the eval
    # eval_obj = create_eval()
    # print(f"Eval created: {eval_obj.id}")
    eval_obj_id = "eval_68750ce75e208191b4a2623a46b8809a"

    # Run the eval
    eval_run = run_eval(eval_id=eval_obj_id, file_id=file.id)
    print(f"Eval run started: {eval_run.id}")

    run = client.evals.runs.retrieve(eval_id=eval_obj_id, run_id=eval_run.id)
    print(f"Eval run status: {run.status}")

if __name__ == "__main__":
    main()
    # jsonl_path = Path("aaa_eval.jsonl").resolve()
    # print(f"Creating JSONL file at: {jsonl_path}")
    # file = upload_files(jsonl_path=jsonl_path)
    # print(f"File uploaded: {file.id}")