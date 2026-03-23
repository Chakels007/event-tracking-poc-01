"""
job.py — simplest possible Flink pipeline

  Kafka[raw-messages]
      → Flink reads each message
      → prints it to stdout
      → writes to Kafka[processed-messages]

Nothing fancy. Just shows the plumbing works.
"""

import os
import json
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaOffsetsInitializer,
    KafkaRecordSerializationSchema,
    DeliveryGuarantee,
)
from pyflink.common import WatermarkStrategy, Types
from pyflink.common.serialization import SimpleStringSchema

BROKER    = os.getenv("KAFKA_BROKER", "kafka:9092")
IN_TOPIC  = "raw-messages"
OUT_TOPIC = "processed-messages"


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(1)

    # ── Source: read from Kafka ──────────────────────────────
    source = (
        KafkaSource.builder()
        .set_bootstrap_servers(BROKER)
        .set_topics(IN_TOPIC)
        .set_group_id("flink-poc-group")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    stream = env.from_source(
        source,
        WatermarkStrategy.no_watermarks(),
        "Kafka source: raw-messages",
    )

    # ── Transform: stamp each message as "processed" ─────────
    def enrich(raw: str) -> str:
        try:
            msg = json.loads(raw)
            msg["processed"] = True          # only change: add this flag
            msg["processed_by"] = "flink"
            return json.dumps(msg)
        except Exception:
            return raw                        # pass through unparseable messages as-is

    processed = stream.map(enrich, output_type=Types.STRING())

    # ── Print to Flink stdout (visible in docker logs) ───────
    processed.print("FLINK OUT")

    # ── Sink: write to Kafka ──────────────────────────────────
    sink = (
        KafkaSink.builder()
        .set_bootstrap_servers(BROKER)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(OUT_TOPIC)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )

    processed.sink_to(sink)

    print(f"Starting Flink job: {IN_TOPIC} → {OUT_TOPIC}")
    env.execute("simple-passthrough")


if __name__ == "__main__":
    main()
