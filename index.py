import os
import uvicorn
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware  # Enable cross-origin requests
import httpx  # Asynchronous HTTP client for calling third-party APIs
from typing import Optional  # Type hints for optional parameters
from urllib.parse import quote  # Encode location names for API requests


load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "demo")
WEATHER_API_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"  # Visual Crossing API endpoint

client: Optional[httpx.AsyncClient] = None


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

# Configure CORS (Cross-Origin Resource Sharing)
# This allows requests from different domains to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from all origins (change to specific domains in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


def _build_weather_url(city: str) -> str:
    return f"{WEATHER_API_URL}/{quote(city.strip())}"


def _extract_weather_metrics(weather_data: dict, city: str) -> dict:
    """Transform the Visual Crossing payload into the API's response shape."""
    current = weather_data.get("currentConditions") or {}
    print(current)
    if not current and weather_data.get("days"):
        current = weather_data["days"][0]

    city_name = city.strip()
    address = weather_data.get("address") or ""
    if address:
        city_name = address.split(",")[0].strip() or city_name

    return {
        "city": city_name,
        "temperature": current.get("temp"),
        "feels_like": current.get("feelslike"),
        "humidity": current.get("humidity"),
        "pressure": current.get("pressure"),
        "description": current.get("conditions"),
        "wind_speed": current.get("windspeed"),
        "units": "us",
    }

@app.get("/weather")
async def get_weather(city: str) -> dict:
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty")
    
    try:
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
        return _extract_weather_metrics(weather_data, city)
    
    except httpx.RequestError as e: # Handle network-related errors (connection timeouts, DNS failures, etc.)
        raise HTTPException(
            detail=f"Failed to connect to weather service: {str(e)}"
        )
    except Exception as e: # Handle any other unexpected errors
        raise HTTPException(
            detail=f"An error occurred: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("index:app", port=8000, reload=True)
