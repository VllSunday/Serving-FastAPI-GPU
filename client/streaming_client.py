#!/usr/bin/env python3
from __future__ import annotations

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Streaming client for /generate/stream")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--prompt", default="Hello, how are you")
    parser.add_argument("--max-new-tokens", type=int, default=32)
    args = parser.parse_args()

    with httpx.stream(
        "POST",
        f"{args.url}/generate/stream",
        json={"prompt": args.prompt, "max_new_tokens": args.max_new_tokens},
        timeout=180.0,
    ) as response:
        response.raise_for_status()
        print("--- stream ---")
        for chunk in response.iter_text():
            if chunk:
                print(chunk, end="", flush=True)
        print("\n--- done ---")


if __name__ == "__main__":
    main()
