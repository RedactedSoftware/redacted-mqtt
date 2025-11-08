# main.py — Sixfab PicoLTE + BerryIMUv3 → EC2 Mosquitto (no TLS)
from pico_lte.core import PicoLTE                      # your PicoLTE class
from machine import I2C, Pin
import time, math, json

# ---- I2C + sensors (your known-good MicroPython approach) ----
i2c = I2C(0, sda=Pin(12), scl=Pin(13), freq=400000)
LSM6DSL_ADDR, LIS3MDL_ADDR = 0x6A, 0x1C

def _wr(addr, reg, val): i2c.writeto_mem(addr, reg, bytes([val]))
def _rd16s(addr, lo):
    b = i2c.readfrom_mem(addr, lo, 2)
    v = b[0] | (b[1] << 8)
    return v - 65536 if v & 0x8000 else v

def init_lsm6dsl():
    _wr(LSM6DSL_ADDR, 0x10, 0b10011111)  # accel
    _wr(LSM6DSL_ADDR, 0x11, 0b10011100)  # gyro
    _wr(LSM6DSL_ADDR, 0x12, 0b01000100)  # BDU+auto-inc
    time.sleep(0.05)

def read_accel_gyro():
    ax, ay, az = _rd16s(LSM6DSL_ADDR, 0x28), _rd16s(LSM6DSL_ADDR, 0x2A), _rd16s(LSM6DSL_ADDR, 0x2C)
    gx, gy, gz = _rd16s(LSM6DSL_ADDR, 0x22), _rd16s(LSM6DSL_ADDR, 0x24), _rd16s(LSM6DSL_ADDR, 0x26)
    return ax, ay, az, gx, gy, gz

def init_lis3mdl():
    _wr(LIS3MDL_ADDR, 0x20, 0b11111100)  # ODR 80Hz
    _wr(LIS3MDL_ADDR, 0x21, 0b00100000)  # ±8 gauss
    _wr(LIS3MDL_ADDR, 0x22, 0b00000000)  # continuous
    time.sleep(0.05)

def read_mag():
    return _rd16s(LIS3MDL_ADDR, 0x28), _rd16s(LIS3MDL_ADDR, 0x2A), _rd16s(LIS3MDL_ADDR, 0x2C)

def heading_deg(mx, my):
    ang = math.degrees(math.atan2(my, mx))
    return ang + 360 if ang < 0 else ang

# ---- Modem + MQTT ----
BROKER = "3.143.210.3"   # EC2 public IP / DNS
PORT   = 1883
TOPIC  = "sensors/imu"

p = PicoLTE()  # exposes p.network, p.mqtt, etc. 

print("📶 Registering to network…")
p.network.register_network()          # initiate registration 
print("🟢 Getting PDP ready…")
p.network.get_pdp_ready()             # bring up data context 

print("🌐 Opening MQTT TCP…")
p.mqtt.open_connection(host=BROKER, port=PORT)   # open TCP to broker
print("🔐 Connecting MQTT session…")
p.mqtt.connect_broker()                          # start MQTT session

print("🧭 Init sensors…")
init_lsm6dsl(); init_lis3mdl(); time.sleep(0.2)

print("🚀 Streaming IMU → MQTT")
while True:
    ax, ay, az, gx, gy, gz = read_accel_gyro()
    mx, my, mz = read_mag()
    h = round(heading_deg(mx, my), 1)
    payload = {
        "accelerometer": {"x": ax, "y": ay, "z": az},
        "gyroscope":     {"x": gx, "y": gy, "z": gz},
        "magnetometer":  {"x": mx, "y": my, "z": mz},
        "heading_deg":   h,
        "timestamp":     time.time()
    }
    msg = json.dumps(payload)
    print("📤", msg)
    p.mqtt.publish_message(payload=msg, topic=TOPIC)   # publish via active session
    time.sleep(2)
