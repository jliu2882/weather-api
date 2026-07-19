import json
import os
import uvicorn
import redis
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware  # Enable cross-origin requests
import httpx  # Asynchronous HTTP client for calling third-party APIs
from typing import Optional  # Type hints for optional parameters
from urllib.parse import quote  # Encode location names for API requests

# use flask-limiter to limit requests to the API to prevent abuse

load_dotenv()

WEATHER_API_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"  # Visual Crossing API endpoint
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS"))


client: Optional[httpx.AsyncClient] = None
redis_client = redis.from_url(REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = httpx.AsyncClient(timeout=10.0)  # Create async HTTP client with 10-second timeout
    print("✓ HTTP client initialized")
    yield
    await client.aclose()  # Gracefully close the HTTP client
    print("✓ HTTP client closed")

app = FastAPI(
    title="Weather API",
    lifespan=lifespan,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def _build_weather_url(city: str) -> str:
    return f"{WEATHER_API_URL}/{quote(city.strip())}"


def _extract_weather_metrics(weather_data: dict, city: str) -> dict:
    current = weather_data.get("currentConditions") or {}
    if not current and weather_data.get("days"):
        current = weather_data["days"][0]

    return {
        "temperature": str(current.get("temp")) + "°F",
        "feels_like": str(current.get("feelslike")) + "°F",
        "humidity": current.get("humidity"),
        "pressure": current.get("pressure"),
        "description": current.get("conditions"),
        "wind_speed": current.get("windspeed"),
    }

@app.get("/weather")
async def get_weather(city: str) -> dict:
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty")

    try:
        cached_item = redis_client.get(f"{city}")
        if cached_item:
            return {"city": city, "cached": True, "data": cached_item.decode('utf-8')}
        
        response = await client.get(
            _build_weather_url(city),
            params={
                "key": WEATHER_API_KEY,
                "unitGroup": "us",
                "include": "current",
            }
        )
        weather_data = response.json()
        if response.status_code != 200:
            error_detail = weather_data.get("message") or weather_data.get("errorMessage") or "Unknown error from weather API"
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Weather API error: {error_detail}"
            )
        
        item_data = _extract_weather_metrics(weather_data, city)
        redis_client.setex(f"{city}", CACHE_TTL_SECONDS, json.dumps(item_data))
        
        return {"city": city, "cached": False, "data": item_data}
    
    except httpx.RequestError as e: # Handle network-related errors (connection timeouts, DNS failures, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to weather service: {str(e)}"
        )
    except Exception as e: # Handle any other unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, reload=True)
