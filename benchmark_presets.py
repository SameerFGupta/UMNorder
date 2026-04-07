import time
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.models import Base, Preset
from backend.config import SQLALCHEMY_DATABASE_URL
import json
import uvicorn
import threading

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Insert 5000 presets
    if db.query(Preset).count() < 5000:
        presets = []
        for i in range(5000):
            presets.append(Preset(
                user_id=1,
                preset_name=f"Preset {i}",
                items_json=json.dumps([{"name": f"Item {i}", "modifiers": ["Mod 1"]}]),
                location_name="Location A"
            ))
        db.bulk_save_objects(presets)
        db.commit()
    db.close()

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="critical")

def run_benchmark():
    setup_db()

    # Start server in thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2) # wait for server to start

    times = []
    # Warmup
    requests.get("http://127.0.0.1:8001/api/presets")

    for _ in range(5):
        start = time.time()
        r = requests.get("http://127.0.0.1:8001/api/presets")
        end = time.time()
        times.append(end - start)
        assert r.status_code == 200
        assert len(r.json()) >= 5000

    avg_time = sum(times) / len(times)
    print(f"Average time for /api/presets: {avg_time:.4f}s")

if __name__ == "__main__":
    run_benchmark()
