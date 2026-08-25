import asyncio
import time


async def fetch_data(name: str, seconds: int) -> str:
    """Pretend to call a database or an API.
    'await asyncio.sleep(seconds)' = a NON-BLOCKING wait.
    While we wait here, the event loop can run other coroutines.
    """
    print(f"[{name}] START (will wait {seconds}s)")
    await asyncio.sleep(seconds)      # <-- the wait; we give our turn away here
    print(f"[{name}] DONE")
    return f"result-from-{name}"


# ---------- WAY 1: one after another (feels sync) ----------
async def run_one_by_one() -> None:
    start = time.time()
    r1 = await fetch_data("A", 2)     # wait 2s fully...
    r2 = await fetch_data("B", 2)     # ...THEN wait 2s more
    r3 = await fetch_data("C", 2)     # ...THEN 2s more
    print("results:", r1, r2, r3)
    print(f">>> one-by-one took {time.time() - start:.2f}s\n")


# ---------- WAY 2: all together with gather ----------
async def run_together() -> None:
    start = time.time()
    # Create 3 coroutines and run them CONCURRENTLY.
    results = await asyncio.gather(
        fetch_data("A", 2),
        fetch_data("B", 2),
        fetch_data("C", 2),
    )
    print("results:", results)
    print(f">>> gather took {time.time() - start:.2f}s\n")


async def main() -> None:
    print("=== WAY 1: one after another ===")
    await run_one_by_one()

    print("=== WAY 2: all together (gather) ===")
    await run_together()


if __name__ == "__main__":
    asyncio.run(main())      # this starts the event loop