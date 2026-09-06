# My Backend Notes

## Sessions
- **2026-08-25** — Started the course. Finished Phase 0 (0.1, 0.2, 0.3) and Phase 1 (1.1). Learned how programs run, sync vs async in Python, async in Django, and what a message queue is. Started the capstone (Django Policy app).

## Progress (Curriculum)

**Phase 0 — Foundations**
- ✅ 0.1 How programs run (process, thread, blocking vs non-blocking, I/O vs CPU)
- ✅ 0.2 Sync vs Async in Python (event loop, async/await, gather)
- ✅ 0.3 Async in Django (WSGI vs ASGI, async views, async ORM)

**Phase 1 — The Core Idea**
- ✅ 1.1 What is a Message Queue

**Phase 2 — The Tools**
- ⬜ 2.1 Redis
- ⬜ 2.2 Celery (+ 2.2.1 caching levels)
- ⬜ 2.3 RabbitMQ
- ⬜ 2.4 Kafka

**Phase 3 — The Architecture**
- ⬜ 3.1 Event-Driven programming
- ⬜ 3.2 Event-Driven Architecture
- ⬜ 3.3 Outbox Pattern

**Phase 4 — The Web Framework**
- ⬜ 4.1 FastAPI from A to Z

**Capstone:** Insurance system (Policies + Invoices). Started: a Django `Policy` model + sync/async views.

---

## 0.1 How Programs Run  *(Phase 0)*

**Problem it solves:** Helps you understand how one program uses the computer, so later words like "async" and "blocking" make sense.

**Main idea (simple):**
- **Process** = a running program with its own memory (a room).
- **Thread** = one hand of work inside the room; threads share memory.
- **CPU work** = the CPU thinks hard the whole time (math, image resize).
- **I/O work** = the program mostly *waits* for the outside (database, network, disk).
- **Blocking** = worker freezes and waits, doing nothing else.
- **Non-blocking** = worker starts the task, does other things while waiting.
- 🔑 **Async helps waiting (I/O), not thinking (CPU).**

**Glossary:**
- Process — running program with own memory.
- Thread — a "hand" inside a process; shares memory.
- CPU work — busy-thinking work.
- I/O — Input/Output; talking to the outside world.
- Blocking — stop and wait.
- Non-blocking — keep working while waiting.
- GIL — a Python lock; only one thread runs Python code at a time (so threads are good for waiting, weak for heavy thinking).

**Key code (smallest runnable):**
```python
import time, threading

def io_work(name):
    print(name, "waiting")
    time.sleep(2)          # I/O = waiting; overlaps across threads
    print(name, "done")

threads = [threading.Thread(target=io_work, args=(f"t{i}",)) for i in range(3)]
for t in threads: t.start()
for t in threads: t.join()
# Run: python file.py  -> 3 waits overlap, total ~2s (not 6s)
```

**Common mistakes:**
- Thinking threads speed up CPU work (they don't, in Python).
- Mixing up process (own memory) vs thread (shared memory).
- Forgetting `.join()` so the program ends before work finishes.
- Believing async/threads fix heavy CPU math.

**What's next:** 0.2 Sync vs Async in Python.

---

## 0.2 Sync vs Async in Python  *(Phase 0)*

**Problem it solves:** Reuse wasted "waiting time" for I/O work using ONE thread — lighter than threads, no shared-memory risk.

**Main idea (simple):**
- One waiter (one thread) serves many tables by never standing still during "cooking" (the wait).
- **Event loop** = the manager that runs tasks and switches at each `await`.
- **`async def`** makes a **coroutine** (a function that can pause/resume).
- **`await`** = "this is a wait; pause me, let others run."
- **`asyncio.gather(a, b, c)`** = run them together so their waits overlap.
- Only works with **non-blocking** waits. A blocking call (like `time.sleep`) freezes the whole loop.
- 🔑 Async = concurrency (juggling), not parallelism (many workers at once).

**Glossary:**
- Coroutine — `async def` function that can pause/resume.
- await — pause here for a wait; let others run.
- Event loop — manager that switches between tasks.
- asyncio — Python's built-in async library.
- asyncio.run(...) — start the loop and run a coroutine.
- asyncio.gather(...) — run many coroutines together (waits overlap).
- Concurrency — one worker juggling many tasks by switching.

**Key code (smallest runnable):**
```python
import asyncio

async def fetch(name, s):
    print(name, "start"); await asyncio.sleep(s); print(name, "done")
    return name

async def main():
    await asyncio.gather(fetch("A", 2), fetch("B", 2), fetch("C", 2))

asyncio.run(main())
# Run: python file.py  -> ~2s total (waits overlap). Sequential await = ~6s.
```

**Common mistakes:**
- Forgetting `await` (coroutine never runs).
- Blocking calls inside async (`time.sleep`, `requests`) freeze the loop.
- Expecting async to speed up CPU work.
- `await a; await b` when you meant `gather` (no overlap).

**What's next:** 0.3 Async in Django.

---

## 0.3 Async in Django  *(Phase 0)*

**Problem it solves:** Lets one worker serve other users while waiting on I/O — but only worth it in specific cases.

**Main idea (simple):**
- **WSGI** = old sync server contract. **ASGI** = new async-capable contract (also WebSockets). Async views need **ASGI** (uvicorn/daphne).
- **Sync view** = normal `def`, blocks. **Async view** = `async def`, can `await`.
- The Django ORM is mostly **sync**; calling it directly in async raises `SynchronousOnlyOperation`.
- Use **`sync_to_async`** to run sync code from async, or async ORM methods: **`aget`, `acreate`, `acount`...**
- ✅ Use async Django for: overlapping many external I/O calls (`gather`), WebSockets, very high I/O concurrency.
- ❌ Keep it sync for: normal one-DB CRUD, CPU-heavy work (use Celery instead).
- 🔑 Async overlaps waits *inside one request*; Celery moves work *out of the request*.

**Glossary:**
- WSGI — old sync server contract.
- ASGI — new async-capable contract (+ WebSockets).
- uvicorn / daphne — ASGI servers.
- SynchronousOnlyOperation — error from calling sync ORM in async unsafely.
- sync_to_async — run blocking code safely from async.
- aget/acreate/... — async ORM methods (the `a` = async).

**Key code (smallest runnable):**
```python
# policies/views.py
import asyncio
from django.http import JsonResponse
from .models import Policy

async def policy_checks_async(request, policy_number):
    policy = await Policy.objects.aget(policy_number=policy_number)  # async ORM
    a, b, c = await asyncio.gather(          # 3 slow calls overlap
        asyncio.sleep(2, result="payment-ok"),
        asyncio.sleep(2, result="fraud-ok"),
        asyncio.sleep(2, result="kyc-ok"),
    )
    return JsonResponse({"policy": policy.policy_number, "checks": [a, b, c]})
# Run: uvicorn config.asgi:application --reload  -> /checks/POL-001/ ~2s not 6s
```

**Common mistakes:**
- Calling sync ORM (`objects.get`) inside async view.
- Making views async "to be modern" (no benefit for simple CRUD).
- Running async views under WSGI (no real concurrency).
- Using async for CPU work (use Celery).
- Awaiting external calls one by one instead of `gather`.

**What's next:** 1.1 What is a Message Queue.

---

## 1.1 What is a Message Queue  *(Phase 1)*

**Problem it solves:** Do the fast part now, hand the slow/fragile part to a separate worker, answer the user instantly — and never lose the work.

**Main idea (simple — the post office 📮):**
- **Producer** = drops a box (creates a message).
- **Broker** = the post office (stores + hands out messages).
- **Queue** = the line of boxes waiting (usually first-in-first-out).
- **Consumer** = the postman/worker who takes messages and does the work.
- Flow: **Producer → message → Broker/Queue → Consumer does work.**
- **Decouple** = unhook two parts so one breaking doesn't break the other. Benefits: instant response, safe if worker is down, easy to scale, producer doesn't care who consumes.
- **Ack** = consumer confirms "done" — **only after success**. If it crashes before ack, the broker retries with another worker.
- **At-least-once** = every message runs ≥1 time, maybe more (can run twice if crash happens after work but before ack).
- **Idempotent** = safe to run twice; the fix for double-runs (built fully in Outbox, 3.3).
- 🔑 A queue gives speed + safety + decoupling, but design work to be safe if it runs more than once.

**Glossary:**
- Producer — creates/sends a message.
- Message — small package of data describing work.
- Broker — middle system storing/handing out messages (post office).
- Queue — line where messages wait (FIFO).
- Consumer — worker that takes messages and does the work.
- Decouple — unhook parts so they don't depend on each other.
- Ack — confirm "received/done, safe to delete."
- At-least-once — every message runs ≥1 time (maybe more).
- Idempotent — safe to run twice; a repeat does no extra harm.

**Key code (smallest runnable — a toy queue by hand):**
```python
# Two terminals. A file is our fake "queue".
import json, time, sys

QUEUE = "queue.log"

def produce(task):
    with open(QUEUE, "a") as f:
        f.write(json.dumps({"id": int(time.time()*1000), "task": task}) + "\n")
    print("dropped", task)          # returns instantly (fast producer)

def consume():
    seen = 0
    while True:
        try: lines = open(QUEUE).readlines()
        except FileNotFoundError: lines = []
        for line in lines[seen:]:
            msg = json.loads(line); print("working", msg["task"])
            time.sleep(2); print("done + ack", msg["id"])   # ack AFTER success
        seen = len(lines); time.sleep(1)

# Run consumer: python file.py consume   | Run producer: python file.py produce EMAIL
if __name__ == "__main__":
    (consume if sys.argv[1] == "consume" else lambda: produce(sys.argv[2]))()
```

**Common mistakes:**
- Acking before the work is done (crash = lost work).
- Assuming exactly-once (it's at-least-once; make work idempotent).
- Putting huge data in a message (send a small id/reference instead).
- Doing the slow work in the producer (defeats the purpose).
- No plan for a message that always fails (needs a dead-letter queue — see RabbitMQ 2.3).

**What's next:** 2.1 Redis — our first REAL broker (cache, simple queue, pub/sub, TTL).

---

## Capstone Progress
- Created Django project `config` + app `policies`.
- `Policy` model with: `policy_number` (unique, indexed), `holder_name`, `premium` (Decimal), `created_at`.
- Views: sync `policy_detail_sync`, async `policy_detail_async` (uses `aget`), async `policy_checks_async` (uses `gather` for overlapping I/O).
- Runs with `uvicorn config.asgi:application --reload` for async views.
  - **Next capstone step:** add Redis (2.1), then Celery (2.2) for real background jobs (send email, generate invoice PDF).