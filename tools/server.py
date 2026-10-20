from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

app = FastAPI(title="Multi-Device Telemetry Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATENMODELLE ---

class DeviceConfig(BaseModel):
    device_id: str
    device_name: str
    device_type: str = "Generic"
    is_enabled: bool = True

class TelemetryPayload(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    telemetry: Dict[str, Any]  # Schema-freies Dict fuer alle Messwerte
    timestamp: Optional[str] = None

# --- IN-MEMORY SPEICHER ---

registered_devices: Dict[str, DeviceConfig] = {
    "fc1_can": DeviceConfig(device_id="fc1_can", device_name="Brennstoffzelle 1 (CAN)", device_type="Fuel Cell"),
    "fc2_can": DeviceConfig(device_id="fc2_can", device_name="Brennstoffzelle 2 (CAN)", device_type="Fuel Cell"),
    "power_load": DeviceConfig(device_id="power_load", device_name="Regatron Power Load", device_type="Load"),
    "gtem_battery": DeviceConfig(device_id="gtem_battery", device_name="GTEM Supercap Batterie", device_type="Battery"),
}

device_states: Dict[str, TelemetryPayload] = {}
device_history: Dict[str, List[TelemetryPayload]] = {}

# --- WEBSOCKET MANAGER ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# --- API ENDPUNKTE ---

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("index.html")

@app.get("/api/devices")
async def get_devices():
    return [dev.dict() for dev in registered_devices.values()]

@app.get("/api/devices/{device_id}/history")
async def get_device_history(device_id: str):
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Geraet nicht gefunden")
    return [p.dict() for p in device_history.get(device_id, [])]

@app.patch("/api/devices/{device_id}/toggle")
async def toggle_device(device_id: str):
    if device_id not in registered_devices:
        raise HTTPException(status_code=404, detail="Geraet nicht gefunden")

    device = registered_devices[device_id]
    device.is_enabled = not device.is_enabled

    await manager.broadcast({
        "type": "device_list_update",
        "devices": [dev.dict() for dev in registered_devices.values()]
    })
    return device.dict()

@app.post("/api/telemetry")
async def receive_telemetry(payload: TelemetryPayload):
    device_id = payload.device_id

    if device_id not in registered_devices:
        registered_devices[device_id] = DeviceConfig(
            device_id=device_id,
            device_name=payload.device_name or device_id,
            device_type=payload.device_type or "Generic",
            is_enabled=True
        )
        await manager.broadcast({
            "type": "device_list_update",
            "devices": [dev.dict() for dev in registered_devices.values()]
        })

    if not registered_devices[device_id].is_enabled:
        return {"status": "ignored", "reason": "device_disabled"}

    if not payload.timestamp:
        payload.timestamp = datetime.now(timezone.utc).isoformat()

    device_states[device_id] = payload

    if device_id not in device_history:
        device_history[device_id] = []

    device_history[device_id].append(payload)
    if len(device_history[device_id]) > 200:
        device_history[device_id].pop(0)

    await manager.broadcast({
        "type": "telemetry_update",
        "data": payload.dict()
    })

    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "init",
            "devices": [dev.dict() for dev in registered_devices.values()],
            "history": {
                k: [p.dict() for p in v]
                for k, v in device_history.items()
                if k in registered_devices and registered_devices[k].is_enabled
            }
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
