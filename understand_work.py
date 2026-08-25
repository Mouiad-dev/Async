import time
import threading


def cpu_work(name: str) -> None:
    """CPU work: the CPU must think the whole time.
    We add many numbers. No waiting, only working.
    """
    print(f"[{name}] CPU work START")
    total = 0
    for i in range(30_000_000):   # heavy thinking
        total += i
    print(f"[{name}] CPU work DONE, total={total}")


def io_work(name: str) -> None:
    """I/O work: the program just WAITS.
    time.sleep(2) means: do nothing for 2 seconds (like waiting for the postman).
    The CPU is free during this wait.
    """
    print(f"[{name}] I/O work START (waiting 2s...)")
    time.sleep(2)                 # pretend we wait for a database/network
    print(f"[{name}] I/O work DONE")


def run_and_time(label: str, func, count: int) -> None:
    """Run 'func' 'count' times using threads, and measure total time."""
    start = time.time()
    threads = [threading.Thread(target=func, args=(f"task{i}",)) for i in range(count)]
    for t in threads:
        t.start()      # start all hands
    for t in threads:
        t.join()       # wait for all hands to finish
    elapsed = time.time() - start
    print(f"\n>>> {label}: {elapsed:.2f} seconds\n")


if __name__ == "__main__":
    print("=== Test 1: I/O work with threads (waiting) ===")
    run_and_time("3 I/O tasks with threads", io_work, 3)

    print("=== Test 2: CPU work with threads (thinking) ===")
    run_and_time("3 CPU tasks with threads", cpu_work, 3)