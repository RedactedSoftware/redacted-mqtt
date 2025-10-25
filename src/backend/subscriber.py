# backend/subscriber.py
import json
import logging
import os
import pymysql
import paho.mqtt.client as mqtt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # .env in same dir or project root

# -----------------------
# CONFIGURATION (from env)
# -----------------------
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "devices/+/telemetry")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASS = os.getenv("DB_PASS", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "telemetry_db")

# -----------------------
# LOGGING
# -----------------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

# -----------------------
# DATABASE CONNECTION
# -----------------------
def get_db_conn():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

db_conn = get_db_conn()
cursor = db_conn.cursor()

# -----------------------
# JSON VALIDATION (simple)
# -----------------------
def validate_json(msg):
    required_fields = ["device_id", "timestamp", "gps", "accel", "temp_c"]
    gps_fields = ["lat", "lon", "alt_m"]
    accel_fields = ["x", "y", "z"]

    for field in required_fields:
        if field not in msg:
            return False

    for g in gps_fields:
        if g not in msg["gps"]:
            return False

    for a in accel_fields:
        if a not in msg["accel"]:
            return False

    return True

# -----------------------
# INSERT FUNCTION
# -----------------------
def insert_telemetry(msg):
    sql = """
    INSERT INTO telemetry (device_id, ts, lat, lon, alt_m,
                           accel_x, accel_y, accel_z, temp_c, meta)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    ts = datetime.fromisoformat(msg["timestamp"].replace("Z","+00:00"))
    meta_json = json.dumps(msg.get("meta", {}))
    values = (msg["device_id"], ts, msg["gps"]["lat"], msg["gps"]["lon"], msg["gps"]["alt_m"],
              msg["accel"]["x"], msg["accel"]["y"], msg["accel"]["z"], msg["temp_c"], meta_json)
    cursor.execute(sql, values)
    db_conn.commit()
    logging.info(f"Inserted telemetry from {msg['device_id']} at {msg['timestamp']}")

# -----------------------
# MQTT CALLBACKS
# -----------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"Failed to connect with result code {rc}")

def on_message(client, userdata, message):
    try:
        payload = message.payload.decode()
        msg = json.loads(payload)
        if validate_json(msg):
            insert_telemetry(msg)
        else:
            logging.warning(f"Invalid message schema: {payload}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# -----------------------
# MAIN
# -----------------------
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("Starting MQTT subscriber...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
