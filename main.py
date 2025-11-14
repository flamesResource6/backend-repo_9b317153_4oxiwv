import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Property, Inquiry
from bson import ObjectId

app = FastAPI(title="Real Estate Agent API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prepare uploads directory and static mount
BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


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


# ----------------------- File Uploads -----------------------

@app.post("/upload")
async def upload_images(request: Request, files: List[UploadFile] = File(...)):
    """Accept one or multiple image files and store them under /uploads.
    Returns absolute URLs for immediate use on the frontend.
    """
    saved_urls: List[str] = []
    for f in files:
        # Basic security: keep only filename tail
        original = os.path.basename(f.filename)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        name, ext = os.path.splitext(original)
        safe_name = f"{name[:30].replace(' ', '_')}_{ts}{ext.lower()}"
        dest_path = os.path.join(UPLOAD_DIR, safe_name)
        content = await f.read()
        with open(dest_path, "wb") as out:
            out.write(content)
        base = str(request.base_url).rstrip('/')
        saved_urls.append(f"{base}/uploads/{safe_name}")
    return {"urls": saved_urls}


# ----------------------- Real Estate Endpoints -----------------------

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
                "description": "Exclusivo penthouse con terraza y vista panorámica al océano Pacífico.",
                "views": 0,
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
                "description": "Acabados de lujo, iluminación natural y ubicación privilegiada.",
                "views": 0,
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
                "description": "Amplios ambientes, jardín y zona tranquila.",
                "views": 0,
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


@app.get("/properties/{property_id}")
def get_property(property_id: str) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        obj_id = ObjectId(property_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")
    doc = db["property"].find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found")
    # Increment views for analytics
    try:
        db["property"].update_one({"_id": obj_id}, {"$inc": {"views": 1}, "$set": {"updated_at": datetime.now(timezone.utc)}})
    except Exception:
        pass
    return serialize_doc(doc)


# ----------------------- Admin: CRUD Properties -----------------------

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    price_usd: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    area_m2: Optional[float] = None
    type: Optional[str] = None
    images: Optional[List[str]] = None
    featured: Optional[bool] = None
    description: Optional[str] = None


@app.post("/properties")
def create_property(payload: Property) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    data = payload.model_dump()
    if "views" not in data:
        data["views"] = 0
    prop_id = create_document("property", data)
    return {"id": prop_id, "status": "ok"}


@app.put("/properties/{property_id}")
def update_property(property_id: str, payload: PropertyUpdate) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        obj_id = ObjectId(property_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc)
    res = db["property"].update_one({"_id": obj_id}, {"$set": update_data})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    doc = db["property"].find_one({"_id": obj_id})
    return serialize_doc(doc)


@app.delete("/properties/{property_id}")
def delete_property(property_id: str) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        obj_id = ObjectId(property_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")
    res = db["property"].delete_one({"_id": obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"status": "ok"}


# ----------------------- Admin: Inquiries & Stats -----------------------

@app.get("/inquiries")
def list_inquiries() -> List[dict]:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    cursor = db["inquiry"].find({}).sort("created_at", -1)
    return [serialize_doc(d) for d in cursor]


@app.post("/inquiries")
def create_inquiry(payload: Inquiry) -> dict:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inquiry_id = create_document("inquiry", payload)
    return {"id": inquiry_id, "status": "ok"}


@app.get("/stats")
def get_stats():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    total_properties = db["property"].count_documents({})
    total_inquiries = db["inquiry"].count_documents({})
    top_properties = list(db["property"].find({}).sort("views", -1).limit(5))
    top_properties = [serialize_doc(p) for p in top_properties]
    recent_inquiries = list(db["inquiry"].find({}).sort("created_at", -1).limit(5))
    recent_inquiries = [serialize_doc(i) for i in recent_inquiries]
    return {
        "total_properties": total_properties,
        "total_inquiries": total_inquiries,
        "top_properties": top_properties,
        "recent_inquiries": recent_inquiries,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
