"""
Fine-tune GPT-4.1 on the tool acquisition decision dataset.

Usage:
    uv run python -m src.level2.run.finetune --upload    # Upload training file
    uv run python -m src.level2.run.finetune --create    # Create fine-tuning job
    uv run python -m src.level2.run.finetune --status    # Check job status
    uv run python -m src.level2.run.finetune --list      # List all jobs
"""

import argparse
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


def upload_training_file(client: OpenAI, file_path: Path) -> str:
    """Upload training file and return file ID."""
    print(f"Uploading {file_path}...")

    with open(file_path, 'rb') as f:
        response = client.files.create(
            file=f,
            purpose="fine-tune"
        )

    print(f"Uploaded: {response.id}")
    print(f"  Filename: {response.filename}")
    print(f"  Status: {response.status}")
    print(f"  Bytes: {response.bytes}")

    return response.id


def create_finetune_job(
    client: OpenAI,
    training_file_id: str,
    model: str = "gpt-4.1-2025-04-14",
    suffix: str = "tool-acquisition",
    n_epochs: int = 3,
    validation_file_id: str = None
) -> str:
    """Create a fine-tuning job and return job ID."""
    print(f"\nCreating fine-tuning job...")
    print(f"  Base model: {model}")
    print(f"  Training file: {training_file_id}")
    print(f"  Epochs: {n_epochs}")
    print(f"  Suffix: {suffix}")

    kwargs = {
        "training_file": training_file_id,
        "model": model,
        "suffix": suffix,
        "hyperparameters": {
            "n_epochs": n_epochs
        }
    }

    if validation_file_id:
        kwargs["validation_file"] = validation_file_id
        print(f"  Validation file: {validation_file_id}")

    response = client.fine_tuning.jobs.create(**kwargs)

    print(f"\nJob created: {response.id}")
    print(f"  Status: {response.status}")
    print(f"  Created at: {response.created_at}")

    return response.id


def check_job_status(client: OpenAI, job_id: str = None):
    """Check status of fine-tuning job(s)."""
    if job_id:
        job = client.fine_tuning.jobs.retrieve(job_id)
        print_job_details(job)
    else:
        # Get most recent job
        jobs = client.fine_tuning.jobs.list(limit=1)
        if jobs.data:
            print_job_details(jobs.data[0])
        else:
            print("No fine-tuning jobs found.")


def print_job_details(job):
    """Print detailed job information."""
    print(f"\nJob: {job.id}")
    print(f"  Status: {job.status}")
    print(f"  Model: {job.model}")
    print(f"  Created: {job.created_at}")

    if job.fine_tuned_model:
        print(f"  Fine-tuned model: {job.fine_tuned_model}")

    if job.finished_at:
        print(f"  Finished: {job.finished_at}")

    if job.error:
        print(f"  Error: {job.error}")

    if job.trained_tokens:
        print(f"  Trained tokens: {job.trained_tokens}")


def list_jobs(client: OpenAI, limit: int = 10):
    """List recent fine-tuning jobs."""
    jobs = client.fine_tuning.jobs.list(limit=limit)

    print(f"\nRecent fine-tuning jobs:")
    print("=" * 70)

    for job in jobs.data:
        model_name = job.fine_tuned_model or "(pending)"
        print(f"{job.id} | {job.status:12} | {job.model} -> {model_name}")


def wait_for_completion(client: OpenAI, job_id: str, poll_interval: int = 60):
    """Wait for job to complete, polling periodically."""
    print(f"\nWaiting for job {job_id} to complete...")

    while True:
        job = client.fine_tuning.jobs.retrieve(job_id)
        print(f"  [{time.strftime('%H:%M:%S')}] Status: {job.status}")

        if job.status in ["succeeded", "failed", "cancelled"]:
            print_job_details(job)
            return job

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune GPT-4.1 for tool acquisition")
    parser.add_argument("--upload", action="store_true", help="Upload training file")
    parser.add_argument("--create", action="store_true", help="Create fine-tuning job")
    parser.add_argument("--status", action="store_true", help="Check job status")
    parser.add_argument("--list", action="store_true", help="List all jobs")
    parser.add_argument("--wait", action="store_true", help="Wait for job completion")
    parser.add_argument("--job-id", type=str, help="Specific job ID")
    parser.add_argument("--file-id", type=str, help="Training file ID (for --create)")
    parser.add_argument("--val-file-id", type=str, help="Validation file ID (optional)")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--suffix", type=str, default="tool-acquisition-v2", help="Model suffix")

    args = parser.parse_args()

    # Load environment
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    data_dir = Path("data/finetuning")
    train_path = data_dir / "train_v2.jsonl"
    val_path = data_dir / "validation_v2.jsonl"

    if args.upload:
        # Upload both training and validation files
        train_id = upload_training_file(client, train_path)
        val_id = upload_training_file(client, val_path)
        print(f"\n{'='*50}")
        print(f"Training file ID: {train_id}")
        print(f"Validation file ID: {val_id}")
        print(f"\nTo create job, run:")
        print(f"  uv run python -m src.level2.run.finetune --create --file-id {train_id} --val-file-id {val_id}")

    elif args.create:
        if not args.file_id:
            print("Error: --file-id required for --create")
            return

        job_id = create_finetune_job(
            client,
            training_file_id=args.file_id,
            validation_file_id=args.val_file_id,
            n_epochs=args.epochs,
            suffix=args.suffix
        )

        print(f"\nTo check status:")
        print(f"  uv run python -m src.level2.run.finetune --status --job-id {job_id}")

        if args.wait:
            wait_for_completion(client, job_id)

    elif args.status:
        check_job_status(client, args.job_id)

    elif args.list:
        list_jobs(client)

    elif args.wait and args.job_id:
        wait_for_completion(client, args.job_id)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
