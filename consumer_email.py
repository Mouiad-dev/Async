# consumer_email.py
# Listens ONLY to policy events (policy.*) and "sends" an email.
import json
import time
import pika

EXCHANGE = "insurance_events"
QUEUE = "email_queue"


def on_message(channel, method, properties, body) -> None:
    payload = json.loads(body)
    print(f"[email] got {method.routing_key}: {payload} -> sending email...")
    try:
        time.sleep(1)  # pretend the email send takes a moment (I/O work)
        # ack ONLY after success (at-least-once, from 1.1)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[email] done + ack {payload['ref']}")
    except Exception as exc:
        print(f"[email] FAILED: {exc} -> nack (no requeue -> would go to DLQ)")
        # requeue=False so a poison message doesn't loop forever.
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main() -> None:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", port=5672)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    # durable queue -> survives restart
    channel.queue_declare(queue=QUEUE, durable=True)
    # BINDING: this queue wants routing keys matching "policy.*"
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key="policy.*")

    # Fair dispatch: don't hand this worker more than 1 unacked message at a time.
    channel.basic_qos(prefetch_count=1)
    # auto_ack=False -> we ack manually after the work succeeds.
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)

    print("[email] waiting for policy.* events. CTRL+C to stop.")
    channel.start_consuming()


if __name__ == "__main__":
    main()