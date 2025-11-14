"""
Monitor Fine-Tuning Job Progress

Checks status of a running fine-tuning job using .env API key.

Usage:
    python -m src.level1.run.monitor_finetuning
"""

import os
import time
from pathlib import Path
from openai import OpenAI


def load_env_api_key():
    """Load API key directly from .env file"""
    env_file = Path(__file__).parent.parent.parent.parent / ".env"

    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                api_key = line.split('=', 1)[1].split('#')[0].strip()
                return api_key

    raise ValueError("OPENAI_API_KEY not found in .env")


def monitor_job(job_id: str, poll_interval: int = 60):
    """Monitor fine-tuning job progress"""
    api_key = load_env_api_key()
    client = OpenAI(api_key=api_key)

    print(f"🔍 Monitoring job: {job_id}")
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

            if hasattr(job, 'error') and job.error and job.error.message:
                print(f" | Error: {job.error.message}", end="")

            print()  # New line

            # Check if job is complete
            if status in ['succeeded', 'failed', 'cancelled']:
                print()
                if status == 'succeeded':
                    print(f"🎉 Fine-tuning completed successfully!")
                    print(f"   Fine-tuned model: {job.fine_tuned_model}")

                    # Save model info
                    import json
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
        print(f"   Resume monitoring: python -m src.level1.run.monitor_finetuning")


def main():
    """Main execution"""
    # Load job ID
    project_root = Path(__file__).parent.parent.parent.parent
    job_id_file = project_root / "data/finetuning_job_id.txt"

    if not job_id_file.exists():
        print("❌ Job ID file not found")
        print(f"   Expected: {job_id_file}")
        return

    job_id = job_id_file.read_text().strip()
    monitor_job(job_id, poll_interval=60)


if __name__ == '__main__':
    main()
