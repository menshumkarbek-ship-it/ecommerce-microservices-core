import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from databases import Database

# 1. Initialize FastAPI with metadata for your Swagger UI
app = FastAPI(
    title="TechVault Async Microservice",
    description="High-performance async sidecar service for checking real-time stock and dynamic specs.",
    version="1.0.0",
)

# Enable CORS so your Django frontend can talk to your FastAPI backend if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000').split(',') if origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configure the Async PostgreSQL Database Connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mobile_shop_db')
database = Database(DATABASE_URL)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# 3. SWAGGER ENDPOINT 1: Fetch Live Inventory Check (Async)
@app.get(
    "/api/v1/stock-check/",
    response_model=List[Dict[str, Any]],
    tags=["Inventory Operations"],
    summary="Get all available items directly from database"
)
async def get_live_stock():
    """
    Connects directly to the shared PostgreSQL database and returns
    all active products that are NOT marked as sold. Runs asynchronously!
    """
    query = "SELECT id, brand, name, price, specifications FROM shop_product WHERE is_sold = FALSE"
    try:
        rows = await database.fetch_all(query=query)
        # Convert database records to standard dictionaries
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


# 4. SWAGGER ENDPOINT 2: Live Price Check for Specific Brands
@app.get(
    "/api/v1/stock-check/{brand}",
    response_model=List[Dict[str, Any]],
    tags=["Inventory Operations"],
    summary="Filter available stock by brand asynchronously"
)
async def get_stock_by_brand(brand: str):
    """
    Async query that filters active inventory items by a specific brand.
    """
    query = "SELECT id, name, price, specifications FROM shop_product WHERE is_sold = FALSE AND LOWER(brand) = LOWER(:brand)"
    try:
        rows = await database.fetch_all(query=query, values={"brand": brand})
        if not rows:
            raise HTTPException(status_code=404, detail=f"No active inventory found for brand: {brand}")
        return [dict(row) for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
