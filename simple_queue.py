"""A tiny message queue by hand, to FEEL the concept.

The 'broker/queue' here is a simple file (one JSON message per line).
Real brokers (Redis, RabbitMQ) do this properly. This is only for learning.
"""

import json
import os
import time
from datetime import datetime

QUEUE_FILE = "queue.log"          # our fake "queue" lives in this file
DONE_FILE = "done.log"            # messages we finished (acked)


# ---------------- PRODUCER ----------------
def produce(task: str, payload: dict) -> None:
    """Create a message and drop it in the queue. Returns immediately."""
    message = {
        "id": f"{int(time.time() * 1000)}",   # a simple unique id
        "task": task,
        "payload": payload,
        "created_at": datetime.now().isoformat(),
    }
    # append one line = drop one box at the post office
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(message) + "\n")
    print(f"[PRODUCER] dropped message {message['id']} -> {task}")


# ---------------- CONSUMER ----------------
def _already_done(message_id: str) -> bool:
    """Idempotency check: did we already finish this message before?"""
    if not os.path.exists(DONE_FILE):
        return False
    with open(DONE_FILE) as f:
        return any(line.strip() == message_id for line in f)


def _do_work(message: dict) -> None:
    """Pretend to do the slow work (send email, make PDF...)."""
    print(f"[CONSUMER] working on {message['id']} ({message['task']})... waiting 2s")
    time.sleep(2)                 # the slow I/O work
    print(f"[CONSUMER] DONE {message['id']}")


def _ack(message_id: str) -> None:
    """Acknowledge: mark this message as finished so we never redo it."""
    with open(DONE_FILE, "a") as f:
        f.write(message_id + "\n")


def consume_forever() -> None:
    """The worker: keep reading the queue and processing new messages."""
    print("[CONSUMER] started. Watching the queue... (Ctrl+C to stop)")
    seen_lines = 0
    while True:
        if not os.path.exists(QUEUE_FILE):
            time.sleep(1)
            continue

        with open(QUEUE_FILE) as f:
            lines = f.readlines()

        # process only new lines we haven't read yet
        for line in lines[seen_lines:]:
            line = line.strip()
            if not line:
                continue
            message = json.loads(line)

            # IDEMPOTENCY: skip if we already finished this one
            if _already_done(message["id"]):
                print(f"[CONSUMER] skip {message['id']} (already done)")
                continue

            _do_work(message)      # do the work
            _ack(message["id"])    # only ack AFTER success

        seen_lines = len(lines)
        time.sleep(1)              # poll the queue every second


# ---------------- CLI ----------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python simple_queue.py consume          # start the worker")
        print("  python simple_queue.py produce EMAIL    # drop a message")
        raise SystemExit(1)

    command = sys.argv[1]

    if command == "consume":
        consume_forever()
    elif command == "produce":
        task = sys.argv[2] if len(sys.argv) > 2 else "SEND_EMAIL"
        produce(task, {"policy": "POL-001"})
    else:
        print(f"Unknown command: {command}")