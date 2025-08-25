import os
import json
from openai import OpenAI

client = OpenAI(api_key="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")

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image and AAA presence."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/"
    local_dir = "../IMINT-Images/"
    # Match actual repo directories
    double_fences_local_folder = "double_fences_training/"
    Non_double_fences_local_folder = "Non_double_fences_training/"

    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:  # Overwrite on each run
        # Process double fences images
        double_fences_path = os.path.join(local_dir, double_fences_local_folder)
        for img_name in os.listdir(double_fences_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Classify whether the following satellite image contains any anti-aircraft artillery (AAA). Respond only with \"yes\" or \"no\"."
                        },
                        {
                             "role": "user",
                             "content": [
                                 {
                                    "type": "image_url",
                                    "image_url": { "url": f"{github_url}{double_fences_local_folder}{img_name}?raw=true" }
                                }
                             ]
                        },
                        { "role": "assistant", "content": "yes" }
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process Non-double fences images
        non_double_fences_path = os.path.join(local_dir, Non_double_fences_local_folder)
        for img_name in os.listdir(non_double_fences_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Classify whether the following satellite image contains any anti-aircraft artillery (AAA). Respond only with \"yes\" or \"no\"."
                        },
                        {
                             "role": "user",
                             "content": [
                                 {
                                    "type": "image_url",
                                    "image_url": { "url": f"{github_url}{Non_double_fences_local_folder}{img_name}?raw=true" }
                                }
                             ]
                        },
                        { "role": "assistant", "content": "no" }
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

    print(f"✅ JSONL file created at '{jsonl_path}' with {total_written} entries.")

if __name__ == "__main__":
    finetune_data = "/Users/selenasun/Projects/IMINT-Analysis/fine-tuning/double_fences_training.jsonl"
    create_jsonl_file(finetune_data)


"""
{
  "object": "file",
  "id": "file-Ti7v8wCqkAw4u1n7CyFShA",
  "purpose": "fine-tune",
  "filename": "double_fences_training.jsonl",
  "bytes": 73768,
  "created_at": 1755859301,
  "expires_at": null,
  "status": "processed",
  "status_details": null
}
"""

"""
curl https://api.openai.com/v1/fine_tuning/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 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" \
  -d '{
    "training_file": "file-Ti7v8wCqkAw4u1n7CyFShA",
    "model": "gpt-4o-2024-08-06"
  }'
"""

"""
{
  "object": "fine_tuning.job",
  "id": "ftjob-VGrx5k0CDQwVvFXDxL1VrVCx",
  "model": "gpt-4o-2024-08-06",
  "created_at": 1755859896,
  "finished_at": null,
  "fine_tuned_model": null,
  "organization_id": "org-Siu2CQQYJYdlsuMSyrbni0Es",
  "result_files": [],
  "status": "validating_files",
  "validation_file": null,
  "training_file": "file-Ti7v8wCqkAw4u1n7CyFShA",
  "hyperparameters": {
    "n_epochs": "auto",
    "batch_size": "auto",
    "learning_rate_multiplier": "auto"
  },
  "trained_tokens": null,
  "error": {},
  "user_provided_suffix": null,
  "seed": 43064642,
  "estimated_finish": null,
  "integrations": [],
  "metadata": null,
  "usage_metrics": null,
  "shared_with_openai": false,
  "eval_id": null,
  "method": {
    "type": "supervised",
    "supervised": {
      "hyperparameters": {
        "batch_size": "auto",
        "learning_rate_multiplier": "auto",
        "n_epochs": "auto"
      }
    }
  }
}
"""