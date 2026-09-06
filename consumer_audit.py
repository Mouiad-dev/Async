# consumer_audit.py
# Listens to ALL events (#) and writes an audit log line.
import json
import pika

EXCHANGE = "insurance_events"
QUEUE = "audit_queue"


def on_message(channel, method, properties, body) -> None:
    payload = json.loads(body)
    print(f"[audit] logged {method.routing_key}: {payload}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main() -> None:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", port=5672)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    # BINDING: "#" matches every routing key -> audit hears everything.
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key="#")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)

    print("[audit] waiting for ALL events. CTRL+C to stop.")
    channel.start_consuming()


if __name__ == "__main__":
    main()