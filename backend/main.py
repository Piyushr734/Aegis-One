from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import get_db_connection
from ml.predictor import predict_event

app = FastAPI(title="Aegis One")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "Aegis One",
        "status": "running"
    }


@app.get("/db-test")
def db_test():
    connection = get_db_connection()

    cursor = connection.cursor()
    cursor.execute("SELECT current_database();")
    database_name = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return {
        "status": "connected",
        "database": database_name
    }
@app.get("/events")
def get_events():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            event_time,
            source_ip,
            destination_ip,
            event_type,
            severity,
            description
        FROM security_events
        ORDER BY event_time DESC;
    """)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    events = []

    for row in rows:
        events.append({
            "id": row[0],
            "event_time": row[1],
            "source_ip": row[2],
            "destination_ip": row[3],
            "event_type": row[4],
            "severity": row[5],
            "description": row[6]
        })

    return {
        "count": len(events),
        "events": events
    }
@app.post("/predict")
def predict_security_event(event: dict):
    result = predict_event(event)

    return {
        "status": "success",
        "prediction": result
    }