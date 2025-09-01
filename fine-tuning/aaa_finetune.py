import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
client = OpenAI(api_key="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")

def create_jsonl_file(jsonl_path):
    """Create a JSONL file with the image and AAA presence."""
    github_url = "https://github.com/selenasun1618/IMINT-Images/blob/main/AAA/aaa_train_combined/"
    local_dir = "../IMINT-Images/AAA/"
    AAA_local_folder = "yes_aaa_train/"
    Non_AAA_local_folder = "no_aaa_train/"

    total_written = 0

    with open(jsonl_path, "w", encoding="utf-8") as f:  # Overwrite on each run
        # Process AAA images
        aaa_path = os.path.join(local_dir, AAA_local_folder)
        for img_name in os.listdir(aaa_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Classify whether the following satellite image contains any anti-aircraft artillery (AAA). Respond only with \"yes\" or \"no\"."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": { "url": f"{github_url}{img_name}?raw=true" }
                                }
                            ]
                        },
                        { "role": "assistant", "content": "yes" }
                    ]
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_written += 1

        # Process Non-AAA images
        non_aaa_path = os.path.join(local_dir, Non_AAA_local_folder)
        for img_name in os.listdir(non_aaa_path):
            if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                record = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Classify whether the following satellite image contains any anti-aircraft artillery (AAA). Respond only with \"yes\" or \"no\"."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": { "url": f"{github_url}{img_name}?raw=true" }
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
    finetune_data = "/Users/selenasun/Projects/IMINT-Analysis/fine-tuning/aaa_training.jsonl"
    create_jsonl_file(finetune_data)
    
"""
curl https://api.openai.com/v1/files \
  -H "Authorization: Bearer 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" \
  -F purpose="fine-tune" \
  -F file="@./fine-tuning/aaa_training.jsonl"

response:
{
  "object": "file",
  "id": "file-3Woghj6Sa1hHQWZHSE8Ui3",
  "purpose": "fine-tune",
  "filename": "aaa_training.jsonl",
  "bytes": 422909,
  "created_at": 1756699925,
  "expires_at": null,
  "status": "processed",
  "status_details": null
}

fine-tuning API call:

curl https://api.openai.com/v1/fine_tuning/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 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" \
  -d '{
    "training_file": "file-3Woghj6Sa1hHQWZHSE8Ui3",
    "model": "gpt-4o-2024-08-06"
    }'

response:
{
  "object": "fine_tuning.job",
  "id": "ftjob-u5Lb1Kow09InyRJeQ86epCgv",
  "model": "gpt-4o-2024-08-06",
  "created_at": 1756701508,
  "finished_at": null,
  "fine_tuned_model": null,
  "organization_id": "org-Siu2CQQYJYdlsuMSyrbni0Es",
  "result_files": [],
  "status": "validating_files",
  "validation_file": null,
  "training_file": "file-3Woghj6Sa1hHQWZHSE8Ui3",
  "hyperparameters": {
    "n_epochs": "auto",
    "batch_size": "auto",
    "learning_rate_multiplier": "auto"
  },
  "trained_tokens": null,
  "error": {},
  "user_provided_suffix": null,
  "seed": 103776184,
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