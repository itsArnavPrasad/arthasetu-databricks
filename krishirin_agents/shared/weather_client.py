import logging
from datetime import datetime, timedelta

import requests
from .config import OPENWEATHER_API_KEY

logger = logging.getLogger(__name__)

# District → approximate coordinates (top agricultural districts)
DISTRICT_COORDS = {
    "nashik": (19.99, 73.79),
    "pune": (18.52, 73.86),
    "solapur": (17.66, 75.90),
    "nagpur": (21.15, 79.09),
    "aurangabad": (19.88, 75.34),
    "kolhapur": (16.70, 74.24),
    "jalgaon": (21.01, 75.56),
    "amravati": (20.93, 77.78),
    "sangli": (16.85, 74.56),
    "latur": (18.40, 76.56),
    "varanasi": (25.32, 82.99),
    "lucknow": (26.85, 80.95),
    "patna": (25.61, 85.14),
    "jaipur": (26.91, 75.79),
    "indore": (22.72, 75.86),
    "bhopal": (23.26, 77.41),
    "hyderabad": (17.39, 78.49),
    "bengaluru": (12.97, 77.59),
    "chennai": (13.08, 80.27),
    "coimbatore": (11.01, 76.96),
}


def fetch_weather(district: str) -> dict:
    """Fetch current weather + 7-day forecast for a district."""
    district_lower = district.lower().strip()
    coords = DISTRICT_COORDS.get(district_lower)

    if not coords:
        # Fallback: use district name as city query
        return _fetch_by_city_name(district)

    lat, lon = coords
    return _fetch_by_coords(lat, lon, district)


def _fetch_by_coords(lat: float, lon: float, district: str) -> dict:
    try:
        # Current weather
        current_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        current_resp = requests.get(current_url, timeout=10)
        current_data = current_resp.json()

        # 5-day forecast (free tier)
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        forecast_resp = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_resp.json()

        return {
            "district": district,
            "current": {
                "temp_c": current_data.get("main", {}).get("temp"),
                "humidity": current_data.get("main", {}).get("humidity"),
                "description": current_data.get("weather", [{}])[0].get("description", ""),
                "wind_speed_mps": current_data.get("wind", {}).get("speed"),
                "rain_mm": current_data.get("rain", {}).get("1h", 0),
            },
            "forecast": _parse_forecast(forecast_data),
        }
    except Exception as e:
        logger.warning(f"Weather API error for {district}: {e}")
        return {"district": district, "current": None, "forecast": [], "error": str(e)}


def _fetch_by_city_name(city: str) -> dict:
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("coord"):
            return _fetch_by_coords(data["coord"]["lat"], data["coord"]["lon"], city)
        return {"district": city, "current": None, "forecast": [], "error": "District not found"}
    except Exception as e:
        return {"district": city, "current": None, "forecast": [], "error": str(e)}


def _parse_forecast(data: dict) -> list[dict]:
    """Extract daily summaries from 3-hour forecast data."""
    daily = {}
    for entry in data.get("list", []):
        date = entry["dt_txt"].split(" ")[0]
        if date not in daily:
            daily[date] = {
                "date": date,
                "temp_max": entry["main"]["temp_max"],
                "temp_min": entry["main"]["temp_min"],
                "humidity": entry["main"]["humidity"],
                "description": entry["weather"][0]["description"],
                "rain_mm": entry.get("rain", {}).get("3h", 0),
            }
        else:
            daily[date]["temp_max"] = max(daily[date]["temp_max"], entry["main"]["temp_max"])
            daily[date]["temp_min"] = min(daily[date]["temp_min"], entry["main"]["temp_min"])
            daily[date]["rain_mm"] += entry.get("rain", {}).get("3h", 0)
    return list(daily.values())[:7]


# ── NASA POWER API — Historical Weather (past 30 days) ──────────────────────


def fetch_historical_weather(lat: float, lon: float, days: int = 30) -> dict:
    """Fetch historical weather data from NASA POWER API.

    Returns precipitation, temperature, and humidity for the past N days.
    Free API, no key required, designed for agricultural applications.

    Args:
        lat: Latitude
        lon: Longitude
        days: Number of past days to fetch (default 30)

    Returns:
        dict with 'daily' list and 'summary' aggregates, or error dict.
    """
    end_date = datetime.now() - timedelta(days=1)  # API has ~1 day lag
    start_date = end_date - timedelta(days=days)

    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=PRECTOTCORR,T2M,RH2M"
        f"&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&start={start_date.strftime('%Y%m%d')}"
        f"&end={end_date.strftime('%Y%m%d')}"
        f"&format=JSON"
    )

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        params = data.get("properties", {}).get("parameter", {})
        precip = params.get("PRECTOTCORR", {})
        temp = params.get("T2M", {})
        humidity = params.get("RH2M", {})

        daily = []
        for date_key in sorted(precip.keys()):
            p = precip.get(date_key, -999)
            t = temp.get(date_key, -999)
            h = humidity.get(date_key, -999)
            # NASA POWER uses -999 for missing data
            if p == -999 or t == -999:
                continue
            daily.append({
                "date": f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:]}",
                "precip_mm": round(p, 2),
                "temp_c": round(t, 1),
                "humidity_pct": round(h, 1) if h != -999 else None,
            })

        # Summary
        if daily:
            temps = [d["temp_c"] for d in daily]
            precips = [d["precip_mm"] for d in daily]
            humidities = [d["humidity_pct"] for d in daily if d["humidity_pct"] is not None]

            total_precip = sum(precips)
            avg_temp = sum(temps) / len(temps)
            avg_humidity = sum(humidities) / len(humidities) if humidities else None
            rainy_days = sum(1 for p in precips if p > 1.0)

            # Trend: compare first half vs second half
            mid = len(temps) // 2
            first_half_temp = sum(temps[:mid]) / max(mid, 1)
            second_half_temp = sum(temps[mid:]) / max(len(temps) - mid, 1)
            temp_trend = "warming" if second_half_temp > first_half_temp + 1 else (
                "cooling" if second_half_temp < first_half_temp - 1 else "stable"
            )

            summary = {
                "avg_temp_c": round(avg_temp, 1),
                "total_precip_mm": round(total_precip, 1),
                "avg_humidity_pct": round(avg_humidity, 1) if avg_humidity else None,
                "rainy_days": rainy_days,
                "temp_trend": temp_trend,
                "period_days": len(daily),
            }
        else:
            summary = {"error": "No data points returned"}

        return {"daily": daily, "summary": summary}

    except Exception as e:
        logger.warning(f"NASA POWER API error: {e}")
        return {"daily": [], "summary": {"error": str(e)}}


def fetch_complete_weather(district: str) -> dict:
    """Fetch both current/forecast (OpenWeatherMap) and historical (NASA POWER) weather.

    Returns a combined dict with all weather context for agents.
    """
    # Current + forecast
    current_forecast = fetch_weather(district)

    # Historical (past 30 days)
    district_lower = district.lower().strip()
    coords = DISTRICT_COORDS.get(district_lower)

    if coords:
        lat, lon = coords
    elif current_forecast.get("current"):
        # If we got coords from OpenWeatherMap city lookup, use those
        lat, lon = DISTRICT_COORDS.get(district_lower, (19.99, 73.79))  # default to Nashik
    else:
        lat, lon = 19.99, 73.79  # fallback

    historical = fetch_historical_weather(lat, lon, days=30)

    return {
        "district": district,
        "current": current_forecast.get("current"),
        "forecast": current_forecast.get("forecast", []),
        "historical_30d": historical,
    }
