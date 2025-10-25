# backend/dashboard_api.py
from fastapi import FastAPI, WebSocket
import pymysql
import asyncio
import json
import os
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "your_db_user")
DB_PASS = os.getenv("DB_PASS", "your_db_password")
DB_NAME = os.getenv("DB_NAME", "telemetry_db")

app = FastAPI()
db_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor)
cursor = db_conn.cursor()
clients = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        clients.remove(ws)

async def broadcast_latest():
    while True:
        cursor.execute("SELECT device_id, ts, lat, lon, alt_m, accel_x, accel_y, accel_z, temp_c FROM telemetry ORDER BY ts DESC LIMIT 10")
        rows = cursor.fetchall()
        for c in clients:
            await c.send_text(json.dumps(rows, default=str))
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_latest())
