import base64
import json
import mimetypes
from pathlib import Path
from openai import OpenAI
client = OpenAI(api_key="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")

# Convert image to base64
def image_to_data_url(path):
    """Return the Base-64 string of an image file."""
    mime, _ = mimetypes.guess_type(path)
    data = Path(path).read_bytes()
    
    b64 = base64.b64encode(data).decode('ascii')
    data_url = f"data:{mime};base64,{b64}"
    return data_url

def get_data_urls(images_dir):
    """Get all image URLs in the directory."""
    img_extensions = [".png", ".jpg", ".jpeg"]
    data_urls = []
    
    for img_path in images_dir.iterdir():
        if img_path.suffix.lower() in img_extensions and img_path.is_file():
            data_urls.append(image_to_data_url(img_path))
    
    return data_urls

def create_jsonl_file(): # TODO
    """Create a JSONL file with the image and AAA presence."""

    base64_image_urls = get_data_urls(images_dir="0.5km_1000x1000_satellite")

    data = {
        "item": {
            "image": image_to_data_url("AAA_37.82494_126.61849_0.5km_1000x1000.png"),
            "aaa_present": "Hardware"  # Example value TODO
        }
    }
    
    jsonl_path = Path("aaa_eval.jsonl")
    with jsonl_path.open("w") as f:
        f.write(f"{data}\n")
    
    print(f"JSONL file created: {jsonl_path}")
    return jsonl_path

# Upload files
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
                    "image": {"type": "string"}, # Base64 encoded image URL
                },
                "required": ["image", "aaa_present", "image_name"],
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
                        "content": "{{ item.image }}"
                    }
                ]
            }
        }
    )

    return eval_run

def main():
    # Upload the image file
    img_name = "AAA_37.82494_126.61849_0.5km_1000x1000.png"
    img_url = image_to_data_url(img_name)
    jsonl_path = Path("aaa_eval.jsonl").resolve()

    record = {
        "item": {
            "aaa_present": "yes",
            "image_name": img_name,
            "image": img_url,
        }
    }
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")

    file = upload_files(jsonl_path=jsonl_path)
    print(f"File uploaded: {file.id}")

    # Create the eval
    eval_obj = create_eval()
    print(f"\nEval created: {eval_obj.id}")

    # Run the eval
    eval_run = run_eval(eval_id=eval_obj.id, file_id=file.id)
    print(f"\nEval run started: {eval_run.id}")

    run = client.evals.runs.retrieve(eval_id=eval_obj.id, run_id=eval_run.id)
    print(f"\nEval run status: {run.status}")

if __name__ == "__main__":
    main()