import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Property, Inquiry

app = FastAPI(title="Real Estate Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Real Estate Agent API running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
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

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Real Estate Endpoints

@app.get("/properties")
def list_properties(featured: Optional[bool] = None) -> List[dict]:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Auto-seed demo data if empty
    count = db["property"].count_documents({})
    if count == 0:
        demo_props = [
            {
                "title": "Penthouse con vista al mar",
                "location": "Miraflores, Lima",
                "price_usd": 850000,
                "beds": 3,
                "baths": 3.5,
                "area_m2": 240,
                "type": "Penthouse",
                "images": [
                    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1502673530728-f79b4cab31b1?q=80&w=1800&auto=format&fit=crop"
                ],
                "featured": True,
                "description": "Exclusivo penthouse con terraza y vista panorámica al océano Pacífico."
            },
            {
                "title": "Departamento moderno en San Isidro",
                "location": "San Isidro, Lima",
                "price_usd": 420000,
                "beds": 2,
                "baths": 2,
                "area_m2": 120,
                "type": "Departamento",
                "images": [
                    "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?q=80&w=1800&auto=format&fit=crop"
                ],
                "featured": True,
                "description": "Acabados de lujo, iluminación natural y ubicación privilegiada."
            },
            {
                "title": "Casa familiar con jardín",
                "location": "La Molina, Lima",
                "price_usd": 365000,
                "beds": 4,
                "baths": 3,
                "area_m2": 280,
                "type": "Casa",
                "images": [
                    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=1800&auto=format&fit=crop"
                ],
                "featured": False,
                "description": "Amplios ambientes, jardín y zona tranquila."
            }
        ]
        for p in demo_props:
            create_document("property", p)

    query = {}
    if featured is True:
        query["featured"] = True
    elif featured is False:
        query["featured"] = {"$ne": True}

    docs = get_documents("property", query)
    return [serialize_doc(d) for d in docs]


@app.post("/inquiries")
def create_inquiry(payload: Inquiry) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inquiry_id = create_document("inquiry", payload)
    return {"id": inquiry_id, "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
