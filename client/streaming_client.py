#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

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
        event = "message"
        for line in response.iter_lines():
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = json.loads(line.removeprefix("data:").strip())
                if event == "token":
                    print(data["delta"], end="", flush=True)
                elif event == "done":
                    print(
                        f"\n--- done: chunks={data['chunks']} "
                        f"latency_ms={data['latency_ms']} ---"
                    )


if __name__ == "__main__":
    main()
