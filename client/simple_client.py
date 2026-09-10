#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-request client for /generate")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--endpoint", default="/generate")
    parser.add_argument("--prompt", default="Explain GPU batching in simple terms")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    payload = {"prompt": args.prompt, "max_new_tokens": args.max_new_tokens}
    started = time.perf_counter()
    response = httpx.post(f"{args.url}{args.endpoint}", json=payload, timeout=120.0)
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"status={response.status_code} client_latency_ms={elapsed_ms:.1f}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)


if __name__ == "__main__":
    main()
