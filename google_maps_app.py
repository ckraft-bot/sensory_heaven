import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
import requests
from config import GOOGLE_MAPS_API_KEY, GOOGLE_MAPS_API_PLACES, GOOGLE_MAPS_API_PLACES_DETAILS, GOOGLE_MAPS_API_NEARBY, GOOGLE_MAPS_API_URL_PHOTOS

def fetch_data(url, headers=None, params=None):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

@st.cache_data
def geocode_location(location_input):
    """Geocode a location using Google Maps API."""
    url = GOOGLE_MAPS_API_PLACES
    params = {"address": location_input, "key": GOOGLE_MAPS_API_KEY}
    data = fetch_data(url, headers=None, params=params)
    if data and data.get("results"):
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None

def get_sensory_friendly_places(location, radius=1000):
    """Fetch sensory-friendly places using Google Places Nearby Search API, filtered to show restaurants and limited to 10 results."""
    url = GOOGLE_MAPS_API_NEARBY
    sensory_keywords = [
        "autism", 
        "cozy", 
        "dim", 
        "peaceful",
        "quiet", 
        "booth", 
        "plant", 
        "flower", 
        "low-lighting"
    ]
    params = {
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "keyword": " OR ".join(sensory_keywords),
        "type": "restaurant",  # Filters to show only restaurants
        "key": GOOGLE_MAPS_API_KEY,
    }
    
    data = fetch_data(url, headers=None, params=params)
    if data and data.get("results"):
        return data["results"][:10]  # Limit to 10 results
    return []

def get_place_details(place_id):
    """Fetch place details using Google Maps API."""
    url = GOOGLE_MAPS_API_PLACES_DETAILS
    params = {"place_id": place_id, "fields": "name,formatted_address,photo,review", "key": GOOGLE_MAPS_API_KEY}
    data = fetch_data(url, headers=None, params=params)
    return data.get("result", {}) if data else {}

def get_place_photos(photo_reference):
    """Get photo URL from Google Maps API."""
    if not photo_reference:
        return None
    url = GOOGLE_MAPS_API_URL_PHOTOS
    params = {
        "maxwidth": 400,
        "photoreference": photo_reference,
        "key": GOOGLE_MAPS_API_KEY,
    }
    return url + "?" + "&".join(f"{k}={v}" for k, v in params.items())

def display_place_info(name, address, photos, reviews):
    """Display place information with photos and reviews."""
    st.subheader(name)
    st.write(f"Address: {address}")
    if photos:
        st.image(photos[0], caption=name, width=300)
    else:
        st.write("No photos :camera_with_flash: available.")

    # Reviews section with expandable/collapsible option
    if reviews:
        with st.expander("Reviews", expanded=False):
            for review in reviews:
                st.write(f"- Anonymous: {review['text']}")
    else:
        st.write("No reviews :speech_balloon: available.")

def main():
    st.title("Sensory Heaven")
    st.write("Discover sensory-friendly businesses near you.")

    # User inputs
    location_input = st.text_input("Enter a location:", "Stockholm")
    radius_input = st.slider("Set the radius (meters):", min_value=100, max_value=5000, value=1000, step=100)

    # Geocode Location
    if location_input:
        location = geocode_location(location_input)
        if location:
            coordinates = [location[0], location[1]]
            st.write(f"Coordinates for {location_input}: {coordinates}")

            # Fetch sensory-friendly places using Google Places Nearby Search API
            sensory_places = get_sensory_friendly_places(coordinates, radius=radius_input)

            if sensory_places:
                m = folium.Map(location=coordinates, zoom_start=15)

                for place in sensory_places:
                    name = place.get("name", "Unknown Place")
                    address = place.get("vicinity", "Address not available")
                    latitude = place["geometry"]["location"]["lat"]
                    longitude = place["geometry"]["location"]["lng"]
                    place_id = place.get("place_id")

                    # Fetch details like photos and reviews using the place_id
                    details = get_place_details(place_id)
                    photo_reference = details.get("photos", [{}])[0].get("photo_reference")
                    photo_url = get_place_photos(photo_reference)
                    reviews = details.get("reviews", [])

                    if latitude and longitude:
                        popup_content = f"<b>{name}</b><br>{address}"
                        folium.Marker(
                            [latitude, longitude],
                            popup=popup_content,
                            icon=Icon(icon="info-sign", prefix="fa", color="blue")
                        ).add_to(m)

                    display_place_info(name, address, [photo_url], reviews)

                st_folium(m, width=800, height=500)
            else:
                st.write("No sensory-friendly places found in the specified radius.")
        else:
            st.error("Unable to geocode the location. Please try again.")

if __name__ == "__main__":
    main()