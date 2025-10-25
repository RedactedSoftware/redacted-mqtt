# pico/mock_publisher.py
import json, time, random
import paho.mqtt.client as mqtt
from datetime import datetime
import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", "pico-01")
TOPIC = f"devices/{DEVICE_ID}/telemetry"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

try:
    print(f"Starting mock telemetry publisher for {DEVICE_ID} -> {MQTT_BROKER}:{MQTT_PORT}")
    while True:
        msg = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat()+"Z",
            "gps": {"lat": round(39 + random.uniform(-0.01, 0.01), 6),
                    "lon": round(-75 + random.uniform(-0.01, 0.01), 6),
                    "alt_m": round(10 + random.uniform(-2, 2), 2)},
            "accel": {"x": round(random.uniform(-0.5, 0.5), 2),
                      "y": round(random.uniform(-0.5, 0.5), 2),
                      "z": round(9.8 + random.uniform(-0.2, 0.2), 2)},
            "temp_c": round(30 + random.uniform(-5, 5), 1),
            "meta": {"battery": round(3.5 + random.uniform(-0.2, 0.2), 2), "rssi": random.randint(-70, -50)}
        }
        payload = json.dumps(msg)
        client.publish(TOPIC, payload)
        print("Published:", payload)
        time.sleep(5)
except KeyboardInterrupt:
    client.disconnect()
    print("Stopped mock publisher.")
