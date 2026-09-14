#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit and poll an offline batch job")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--max-new-tokens", type=int, default=32)
    args = parser.parse_args()

    prompts = [
        "Explain FastAPI in one sentence.",
        "Explain CUDA in one sentence.",
        "Explain model batching in one sentence.",
        "Explain throughput in one sentence.",
    ]
    with httpx.Client(base_url=args.url, timeout=180.0) as client:
        response = client.post(
            "/batch",
            json={"prompts": prompts, "max_new_tokens": args.max_new_tokens},
        )
        response.raise_for_status()
        accepted = response.json()
        print(f"accepted HTTP 202: job_id={accepted['job_id']}")

        while True:
            job = client.get(accepted["status_url"]).json()
            print(f"status={job['status']}")
            if job["status"] in {"completed", "failed"}:
                break
            time.sleep(0.2)

    if job["status"] == "failed":
        raise SystemExit(job["error"])
    for index, result in enumerate(job["results"], start=1):
        print(f"[{index}] {result}")
    print(f"batch_size={job['prompt_count']} inference_ms={job['inference_ms']}")


if __name__ == "__main__":
    main()
