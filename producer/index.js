const { Kafka } = require("kafkajs");

const kafka = new Kafka({
  clientId: "simple-producer",
  brokers: [process.env.KAFKA_BROKER || "kafka:9092"],
  retry: { retries: 10, initialRetryTime: 3000 },
});

const producer = kafka.producer();
const TOPIC = "raw-messages";
let count = 0;

async function run() {
  console.log("Connecting to Kafka...");
  await producer.connect();
  console.log(`Connected. Sending to topic: ${TOPIC}`);

  setInterval(async () => {
    count++;
    const message = {
      id: count,
      text: `Hello from message #${count}`,
      timestamp: new Date().toISOString(),
    };

    await producer.send({
      topic: TOPIC,
      messages: [{ key: String(count), value: JSON.stringify(message) }],
    });

    console.log(`[SENT] #${count} → ${message.text}`);
  }, 1000); // one message per second
}

run().catch((err) => {
  console.error("Producer error:", err);
  process.exit(1);
});
