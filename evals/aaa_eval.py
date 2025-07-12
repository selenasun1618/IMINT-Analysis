
import base64
from pathlib import Path
from openai import OpenAI
client = OpenAI()

instructions = """
You are an expert nuclear analyst responsible for informing the U.S. government about the status of nuclear power plants.
You are looking for anti-aircraft artillery (AAA) sites, which are indicators of nuclear power plants nearby.
You are to decide whether the given image contains an AAA site or not.
"""

# Convert image to base64
def image_to_base64(path):
    """Return the Base-64 string of an image file."""
    data = Path(path).read_bytes()
    return base64.b64encode(data).decode('ascii')  # str, not bytes

# Create eval
eval_obj = client.evals.create(
    name="AAA Eval",
    data_source_config={
        "type": "custom",
        "item_schema": {
            "type": "object",
            "properties": {
                "aaa_present": {"type": "string"},
            },
            "required": ["aaa_present"],
        },
        "include_sample_schema": True
    },
    testing_criteria=[
        {
            "name": "AAA classification grader",
            "type": "string_check",
            "labels": ["yes", "no"],
            "model": "gpt-4o-2024-08-06",
            "input": "{{ sample.output_text }}",
            "operation": "eq",
            "reference": "{{ item.correct_label }}"
        }
    ],
)

print(eval_obj)