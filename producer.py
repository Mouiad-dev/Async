# producer.py
# Publishes insurance events to a TOPIC exchange.
import json
import sys
import pika

EXCHANGE = "insurance_events"


def get_channel() -> tuple[pika.BlockingConnection, "pika.channel.Channel"]:
    """One place to open the connection + channel (DRY)."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost", port=5672)
    )
    channel = connection.channel()
    # Declare the exchange. `durable=True` -> survives a broker restart.
    # Declaring is idempotent: safe to call every time; creates it if missing.
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    return connection, channel


def publish(routing_key: str, payload: dict) -> None:
    connection, channel = get_channel()
    try:
        body = json.dumps(payload)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,          # the address label
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,              # 2 = persistent message (saved to disk)
                content_type="application/json",
            ),
        )
        print(f"[producer] sent '{routing_key}': {payload}")
    finally:
        connection.close()


if __name__ == "__main__":
    # Usage: python producer.py policy.issued POL-001
    #        python producer.py invoice.created INV-500
    routing_key = sys.argv[1] if len(sys.argv) > 1 else "policy.issued"
    ref = sys.argv[2] if len(sys.argv) > 2 else "POL-001"
    publish(routing_key, {"ref": ref, "event": routing_key})