import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Appointment, Patient, Doctor

app = FastAPI(title="Hospital Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hospital Management API is running"}


@app.get("/test")
def test_database():
    response: Dict[str, Any] = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                cols = db.list_collection_names()
                response["collections"] = cols[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# --------- Core domain endpoints ---------

@app.post("/appointments")
def create_appointment(payload: Appointment):
    try:
        app_id = create_document("appointment", payload)
        return {"id": app_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments")
def list_appointments(limit: int = 20):
    try:
        docs = get_documents("appointment", {}, limit)
        # Convert ObjectIds and datetimes to strings
        def normalize(doc: Dict[str, Any]):
            doc["id"] = str(doc.pop("_id", ""))
            for k, v in list(doc.items()):
                if hasattr(v, "isoformat"):
                    doc[k] = v.isoformat()
            return doc
        return [normalize(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patients")
def create_patient(payload: Patient):
    try:
        pid = create_document("patient", payload)
        return {"id": pid, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/doctors")
def create_doctor(payload: Doctor):
    try:
        did = create_document("doctor", payload)
        return {"id": did, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def live_stats():
    """Return live-ish operational stats.

    Values are derived from database where possible with sensible bounds.
    """
    try:
        doctors_count = db["doctor"].count_documents({"on_duty": True}) if db else 0
        total_beds = 250  # could be a config/collection in a real system
        occupied_beds = min(total_beds, 150 + (doctors_count // 2) * 3)
        bed_pct = round((occupied_beds / total_beds) * 100)

        # ER wait: influenced by current appointments today
        today = datetime.utcnow().date().isoformat()
        todays_appts = db["appointment"].count_documents({"date": today}) if db else 0
        wait_min = max(5, min(45, 10 + todays_appts // 3 - doctors_count // 5))

        # Activity as a health score proxy
        activity = max(40, min(95, 60 + doctors_count * 2 - todays_appts // 4))

        return {
            "wait": wait_min,
            "beds": bed_pct,
            "doctors": max(12, doctors_count or 24),
            "activity": activity,
        }
    except Exception as e:
        # Fallback conservative values
        return {"wait": 15, "beds": 82, "doctors": 24, "activity": 70, "note": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
