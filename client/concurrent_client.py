#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((q / 100) * (len(ordered) - 1)))))
    return ordered[index]


async def one_request(
    client: httpx.AsyncClient,
    url: str,
    prompt: str,
    max_new_tokens: int,
    semaphore: asyncio.Semaphore,
) -> tuple[bool, float]:
    async with semaphore:
        started = time.perf_counter()
        try:
            response = await client.post(
                url,
                json={"prompt": prompt, "max_new_tokens": max_new_tokens},
            )
            ok = response.status_code == 200
        except Exception:
            ok = False
        latency_ms = (time.perf_counter() - started) * 1000
        return ok, latency_ms


async def run_benchmark(
    base_url: str,
    endpoint: str,
    requests: int,
    concurrency: int,
    prompt: str,
    max_new_tokens: int,
) -> None:
    url = f"{base_url}{endpoint}"
    semaphore = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(180.0)
    started = time.perf_counter()

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            one_request(client, url, f"{prompt} #{index}", max_new_tokens, semaphore)
            for index in range(requests)
        ]
        results = await asyncio.gather(*tasks)

    total_s = time.perf_counter() - started
    successes = [latency for ok, latency in results if ok]
    failures = len(results) - len(successes)
    avg = statistics.mean(successes) if successes else 0.0
    throughput = len(successes) / total_s if total_s > 0 else 0.0

    print(f"requests           {requests}")
    print(f"concurrency        {concurrency}")
    print(f"endpoint           {endpoint}")
    print(f"successful         {len(successes)}")
    print(f"failed             {failures}")
    print(f"total time         {total_s:.3f}s")
    print(f"average latency    {avg:.1f}ms")
    print(f"p50                {percentile(successes, 50):.1f}ms")
    print(f"p95                {percentile(successes, 95):.1f}ms")
    print(f"throughput         {throughput:.2f} req/s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Concurrent benchmark client")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--endpoint",
        default="/generate/dynamic",
        help="Use /generate to compare against dynamic batching",
    )
    parser.add_argument("--requests", type=int, default=32)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--prompt", default="Explain GPU serving")
    parser.add_argument("--max-new-tokens", type=int, default=32)
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run 1,2,4,8,16,32 concurrent requests",
    )
    args = parser.parse_args()

    if args.sweep:
        for concurrency in (1, 2, 4, 8, 16, 32):
            print("=" * 48)
            asyncio.run(
                run_benchmark(
                    args.url,
                    args.endpoint,
                    requests=concurrency,
                    concurrency=concurrency,
                    prompt=args.prompt,
                    max_new_tokens=args.max_new_tokens,
                )
            )
        return

    asyncio.run(
        run_benchmark(
            args.url,
            args.endpoint,
            args.requests,
            args.concurrency,
            args.prompt,
            args.max_new_tokens,
        )
    )


if __name__ == "__main__":
    main()
