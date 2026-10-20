
import argparse
import math
import statistics
import time

import httpx


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[index]


def run_benchmark(base_url: str, job_count: int) -> None:
    job_ids = []
    submitted_at = {}
    latencies = {}

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        print(f"Submitting {job_count} jobs...")

        benchmark_start = time.perf_counter()

        for _ in range(job_count):
            payload = {
                "job_type": "send_email",
                "payload": {
                    "recipient": "benchmark@example.com",
                    "subject": "Benchmark job",
                },
                "max_retries": 0,
            }

            start = time.perf_counter()
            response = client.post("/jobs", json=payload)
            response.raise_for_status()

            job_id = response.json()["id"]
            job_ids.append(job_id)
            submitted_at[job_id] = start

        print("Waiting for all jobs to finish...")

        pending = set(job_ids)
        failed = set()

        while pending:
            for job_id in list(pending):
                response = client.get(f"/jobs/{job_id}")
                response.raise_for_status()
                job = response.json()

                if job["status"] == "completed":
                    latencies[job_id] = (
                        time.perf_counter() - submitted_at[job_id]
                    )
                    pending.remove(job_id)

                elif job["status"] == "failed":
                    failed.add(job_id)
                    pending.remove(job_id)

            if pending:
                time.sleep(0.25)

        elapsed = time.perf_counter() - benchmark_start

    completed_count = len(latencies)
    failed_count = len(failed)
    throughput = completed_count / elapsed if elapsed else 0

    print("\n--- Benchmark Results ---")
    print(f"Submitted:          {job_count}")
    print(f"Completed:          {completed_count}")
    print(f"Failed:             {failed_count}")
    print(f"Total elapsed:      {elapsed:.2f} seconds")
    print(f"Throughput:         {throughput:.2f} jobs/second")

    if latencies:
        values_ms = [value * 1000 for value in latencies.values()]
        print(f"Average latency:    {statistics.mean(values_ms):.2f} ms")
        print(f"P95 latency:        {percentile(values_ms, 0.95):.2f} ms")

    if failed_count:
        print("Warning: Some jobs failed; investigate before comparing runs.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=20)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
    )
    args = parser.parse_args()

    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    run_benchmark(args.url, args.jobs)
