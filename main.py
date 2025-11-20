import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Sport, Booking

app = FastAPI(title="Sports Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Sports Booking API is running"}


@app.get("/schema")
def get_schema():
    # Expose schemas to the database viewer (if used)
    return {
        "sport": Sport.model_json_schema(),
        "booking": Booking.model_json_schema(),
    }


@app.get("/sports", response_model=List[Sport])
def list_sports():
    # If sports not in DB yet, seed defaults
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    sports = list(db["sport"].find({}))
    if not sports:
        defaults = [
            {
                "key": "futsal",
                "name": "Futsal",
                "courts": 3,
                "price_per_hour": 150000,
                "open_hour": 8,
                "close_hour": 23,
            },
            {
                "key": "minisoccer",
                "name": "Mini Soccer",
                "courts": 2,
                "price_per_hour": 250000,
                "open_hour": 8,
                "close_hour": 23,
            },
            {
                "key": "badminton",
                "name": "Badminton",
                "courts": 6,
                "price_per_hour": 60000,
                "open_hour": 7,
                "close_hour": 22,
            },
        ]
        db["sport"].insert_many(defaults)
        sports = list(db["sport"].find({}))

    # Convert Mongo docs to Pydantic models
    result = []
    for s in sports:
        s.pop("_id", None)
        result.append(Sport(**s))
    return result


class BookingCreate(Booking):
    pass


@app.post("/bookings", status_code=201)
def create_booking(payload: BookingCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Validate sport exists
    sport_doc = db["sport"].find_one({"key": payload.sport})
    if not sport_doc:
        raise HTTPException(status_code=404, detail="Sport not found")

    # Compute hours and total
    try:
        start_h = int(payload.start_time.split(":")[0])
        end_h = int(payload.end_time.split(":")[0])
        if end_h <= start_h:
            raise ValueError("End time must be after start time")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid time range")

    hours = end_h - start_h
    total = hours * int(sport_doc.get("price_per_hour", 0))

    # Check court availability (no overlapping bookings)
    conflict = db["booking"].find_one({
        "sport": payload.sport,
        "court": payload.court,
        "date": payload.date,
        "$or": [
            {"start_time": {"$lt": payload.end_time}, "end_time": {"$gt": payload.start_time}}
        ],
    })
    if conflict:
        raise HTTPException(status_code=409, detail="Slot already booked for this court")

    data = payload.model_dump()
    data["total_price"] = total
    create_document("booking", data)
    return {"message": "Booking created", "total_price": total}


@app.get("/bookings")
def list_bookings(sport: Optional[str] = None, date: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    query = {}
    if sport:
        query["sport"] = sport
    if date:
        query["date"] = date

    items = db["booking"].find(query).sort([("date", 1), ("start_time", 1)])
    result = []
    for b in items:
        b["id"] = str(b.pop("_id"))
        result.append(b)
    return result


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
