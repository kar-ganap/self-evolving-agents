"""
Start OpenAI Fine-Tuning Job (Milestone 1.15)

Uploads training data and starts fine-tuning with early stopping.

Usage:
    python -m src.level1.run.start_finetuning
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import openai
from openai import OpenAI
import time

load_dotenv(override=True)


def validate_training_file(file_path: Path) -> bool:
    """Validate training file exists and has correct format"""
    if not file_path.exists():
        print(f"❌ Training file not found: {file_path}")
        return False

    # Check file size
    file_size = file_path.stat().st_size
    print(f"📏 File size: {file_size / 1024 / 1024:.2f} MB")

    # Count examples
    with open(file_path, 'r') as f:
        num_examples = sum(1 for _ in f)

    print(f"📊 Number of examples: {num_examples}")

    if num_examples < 10:
        print(f"⚠️  Warning: Only {num_examples} examples (recommended: 50+)")

    return True


def upload_training_file(client: OpenAI, file_path: Path) -> str:
    """Upload training file to OpenAI"""
    print(f"\n📤 Uploading training file...")

    with open(file_path, 'rb') as f:
        response = client.files.create(
            file=f,
            purpose='fine-tune'
        )

    file_id = response.id
    print(f"✅ Uploaded successfully!")
    print(f"   File ID: {file_id}")

    return file_id


def start_finetuning_job(
    client: OpenAI,
    training_file_id: str,
    validation_file_id: str = None,
    model: str = "gpt-4o-2024-08-06",
    suffix: str = "kartik-patterns"
) -> str:
    """Start fine-tuning job with validation file and early stopping"""
    print(f"\n🚀 Starting fine-tuning job...")
    print(f"   Base model: {model}")
    print(f"   Model suffix: {suffix}")
    if validation_file_id:
        print(f"   Validation file: {validation_file_id}")
        print(f"   Early stopping: Enabled")

    # Create fine-tuning job parameters
    params = {
        "training_file": training_file_id,
        "model": model,
        "suffix": suffix,
        "hyperparameters": {
            "n_epochs": "auto",  # Auto with early stopping
        }
    }

    # Add validation file if provided
    if validation_file_id:
        params["validation_file"] = validation_file_id

    # Create fine-tuning job
    response = client.fine_tuning.jobs.create(**params)

    job_id = response.id
    print(f"✅ Fine-tuning job created!")
    print(f"   Job ID: {job_id}")
    print(f"   Status: {response.status}")

    return job_id


def monitor_job(client: OpenAI, job_id: str, poll_interval: int = 60):
    """Monitor fine-tuning job progress"""
    print(f"\n👀 Monitoring job {job_id}...")
    print(f"   Polling every {poll_interval} seconds")
    print(f"   Press Ctrl+C to stop monitoring (job will continue)")
    print()

    try:
        while True:
            # Get job status
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status

            # Print status update
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] Status: {status}", end="")

            # Print additional info if available
            if hasattr(job, 'trained_tokens') and job.trained_tokens:
                print(f" | Tokens trained: {job.trained_tokens:,}", end="")

            if hasattr(job, 'error') and job.error:
                print(f" | Error: {job.error}", end="")

            print()  # New line

            # Check if job is complete
            if status in ['succeeded', 'failed', 'cancelled']:
                print()
                if status == 'succeeded':
                    print(f"🎉 Fine-tuning completed successfully!")
                    print(f"   Fine-tuned model: {job.fine_tuned_model}")

                    # Save model info
                    model_info = {
                        'job_id': job_id,
                        'fine_tuned_model': job.fine_tuned_model,
                        'base_model': job.model,
                        'status': status,
                        'created_at': job.created_at,
                        'finished_at': job.finished_at,
                        'trained_tokens': job.trained_tokens if hasattr(job, 'trained_tokens') else None
                    }

                    output_file = Path(__file__).parent.parent.parent.parent / "data/finetuned_model_info.json"
                    with open(output_file, 'w') as f:
                        json.dump(model_info, f, indent=2)

                    print(f"   Model info saved to: {output_file}")

                elif status == 'failed':
                    print(f"❌ Fine-tuning failed!")
                    if hasattr(job, 'error') and job.error:
                        print(f"   Error: {job.error}")
                else:
                    print(f"⚠️  Job was cancelled")

                break

            # Wait before next poll
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print(f"\n⏸️  Monitoring stopped. Job {job_id} is still running.")
        print(f"   Check status with: openai api fine_tuning.jobs.retrieve -i {job_id}")


def main():
    """Main execution"""
    print("🚀 OpenAI Fine-Tuning Job Launcher")
    print("=" * 60)

    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Make sure .env file contains OPENAI_API_KEY")
        return

    print(f"✅ API key loaded: {api_key[:15]}...")

    # Initialize client
    client = OpenAI(api_key=api_key)

    # Paths
    project_root = Path(__file__).parent.parent.parent.parent
    training_file = project_root / "data/finetuning/train.jsonl"
    validation_file = project_root / "data/finetuning/validation.jsonl"

    # Validate training file
    print(f"\n📂 Training file: {training_file}")
    if not validate_training_file(training_file):
        return

    # Validate validation file
    print(f"\n📂 Validation file: {validation_file}")
    if not validate_training_file(validation_file):
        return

    # Upload training file
    training_file_id = upload_training_file(client, training_file)

    # Upload validation file
    print(f"\n📤 Uploading validation file...")
    with open(validation_file, 'rb') as f:
        response = client.files.create(
            file=f,
            purpose='fine-tune'
        )
    validation_file_id = response.id
    print(f"✅ Uploaded successfully!")
    print(f"   File ID: {validation_file_id}")

    # Start fine-tuning with validation
    job_id = start_finetuning_job(
        client,
        training_file_id,
        validation_file_id=validation_file_id,
        model="gpt-4o-2024-08-06",
        suffix="kartik-patterns"
    )

    # Save job ID
    job_info_file = project_root / "data/finetuning_job_id.txt"
    with open(job_info_file, 'w') as f:
        f.write(job_id)
    print(f"\n💾 Job ID saved to: {job_info_file}")

    # Monitor job
    print("\n" + "=" * 60)
    monitor_job(client, job_id, poll_interval=30)


if __name__ == '__main__':
    main()
