"""
Free-form place lookup with optional local suggestions for Indian locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches

from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim


@dataclass(frozen=True)
class PlaceLocation:
    name: str
    state: str
    latitude: float
    longitude: float
    address: str


KNOWN_PLACES = [
    "Agra",
    "Ahmedabad",
    "Amritsar",
    "Bengaluru",
    "Bhopal",
    "Bhubaneswar",
    "Chandigarh",
    "Chennai",
    "Coimbatore",
    "Dehradun",
    "Delhi",
    "Gangtok",
    "Guwahati",
    "Hyderabad",
    "Indore",
    "Jaipur",
    "Jammu",
    "Kanpur",
    "Kochi",
    "Kolkata",
    "Kozhikode",
    "Leh",
    "Lucknow",
    "Mangaluru",
    "Mumbai",
    "Mysuru",
    "Nagpur",
    "Patna",
    "Port Blair",
    "Pune",
    "Raipur",
    "Ranchi",
    "Shillong",
    "Shimla",
    "Srinagar",
    "Surat",
    "Thiruvananthapuram",
    "Udaipur",
    "Varanasi",
    "Visakhapatnam",
]

PLACE_ALIASES = {
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "cochin": "Kochi",
    "madras": "Chennai",
    "mysore": "Mysuru",
    "new delhi": "Delhi",
    "trivandrum": "Thiruvananthapuram",
    "vizag": "Visakhapatnam",
}

_GEOCODER = Nominatim(user_agent="weather_pattern_clustering", timeout=10)


def normalize_place_name(name: str) -> str:
    normalized = " ".join(name.strip().lower().split())
    return PLACE_ALIASES.get(normalized, normalized)


def suggest_place_names(query: str, limit: int = 6) -> list[str]:
    query = normalize_place_name(query)
    if not query:
        return KNOWN_PLACES[:limit]

    direct = [
        place for place in KNOWN_PLACES
        if query in place.lower()
    ]
    if len(direct) >= limit:
        return direct[:limit]

    fuzzy = get_close_matches(query, [place.lower() for place in KNOWN_PLACES], n=limit, cutoff=0.4)
    fuzzy_title = []
    for match in fuzzy:
        for place in KNOWN_PLACES:
            if place.lower() == match and place not in direct and place not in fuzzy_title:
                fuzzy_title.append(place)
                break

    return (direct + fuzzy_title)[:limit]


def _extract_state(raw: dict) -> str:
    address = raw.get("address", {}) if isinstance(raw, dict) else {}
    for key in ("state", "state_district", "region", "county"):
        value = address.get(key)
        if value:
            return str(value)
    return "Unknown"


def _extract_name(raw: dict, fallback_query: str) -> str:
    if isinstance(raw, dict):
        address = raw.get("address", {})
        for key in ("city", "town", "village", "municipality", "suburb", "state_district", "state"):
            value = address.get(key)
            if value:
                return str(value)

        display_name = raw.get("display_name")
        if display_name:
            return str(display_name).split(",")[0].strip()
    return fallback_query.strip().title()


def resolve_place(name: str) -> PlaceLocation:
    query = name.strip()
    if not query:
        raise ValueError("Place name cannot be empty.")

    normalized = normalize_place_name(query)
    geocode_query = normalized if normalized != query.lower() else query

    try:
        location = _GEOCODER.geocode(
            geocode_query,
            country_codes="in",
            addressdetails=True,
            exactly_one=True,
        )
    except (GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError) as exc:
        raise RuntimeError(f"Geocoding failed for '{name}': {exc}") from exc

    if location is None:
        suggestions = suggest_place_names(query)
        suggestion_text = f" Suggestions: {', '.join(suggestions)}" if suggestions else ""
        raise KeyError(f"Could not resolve place '{name}'.{suggestion_text}")

    raw = location.raw if hasattr(location, "raw") else {}
    resolved_name = _extract_name(raw, query)
    state = _extract_state(raw)
    address = getattr(location, "address", resolved_name)

    return PlaceLocation(
        name=resolved_name,
        state=state,
        latitude=float(location.latitude),
        longitude=float(location.longitude),
        address=str(address),
    )
