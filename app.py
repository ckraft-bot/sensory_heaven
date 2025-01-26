import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
import requests
from config import *
from geopy.geocoders import Nominatim

# Cache geocoding results to improve performance
@st.cache_data
def geocode_location(location_input):
    geolocator = Nominatim(user_agent="streamlit_app")
    return geolocator.geocode(location_input)

def business_selection():
    """Streamlit widget for selecting a business category."""
    selected_category = st.selectbox(
        "Select the business category you are interested in:",
        options=list(CATEGORIES.keys()),
        index=0
    )
    st.write(f"You selected: **{selected_category}**")
    return CATEGORIES[selected_category]

def fetch_data(url, headers, params=None):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def get_sensory_friendly_places(location, radius=1000, category_id=None):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    sensory_keywords = [
        "accessibility", "accessible", "autism", "cozy", "dim", "peaceful",
        "quiet", "booths", "plant", "flower", "low-lighting"
    ]
    params = {
        "ll": location,
        "radius": radius,
        "query": " OR ".join(sensory_keywords),
        "limit": 10,
    }
    if category_id:
        params["categoryId"] = category_id

    data = fetch_data(FOURSQUARE_API_URL_SEARCH, headers, params)
    return data.get("results", []) if data else []

def get_place_photos(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    url = FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id)
    data = fetch_data(url, headers)
    return [photo["prefix"] + "300x300" + photo["suffix"] for photo in data] if data else []

def get_place_reviews(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    url = FOURSQUARE_API_URL_REVIEWS.format(fsq_id=place_id)
    data = fetch_data(url, headers)
    return [
        {"user": tip.get("user", {}).get("firstName", "Anonymous"), "text": tip.get("text", "")}
        for tip in data
    ] if data else []

def display_place_info(name, address, photos, reviews):
    """Display place information with photos and reviews."""
    st.subheader(name)
    st.write(f"Address: {address}")
    if photos:
        st.image(photos[0], caption=name, width=300)
    else:
        st.write("No photos :camera_with_flash: available.")
    if reviews:
        st.write("Reviews:")
        for review in reviews:
            st.write(f"- {review['user']}: {review['text']}")
    else:
        st.write("No reviews :speech_balloon: available.")

def main():
    st.title("Sensory Heaven")
    st.write("Discover sensory-friendly businesses near you.")

    location_input = st.text_input("Enter a location:", "Stockholm")
    radius_input = st.slider("Set the radius (meters):", min_value=100, max_value=5000, value=1000, step=100)
    category_id = business_selection()

    # Geocode Location
    if location_input:
        location = geocode_location(location_input)
        if location:
            coordinates = [location.latitude, location.longitude]
            st.write(f"Coordinates for {location_input}: {coordinates}")

            # Fetch sensory-friendly places
            places = get_sensory_friendly_places(
                f"{location.latitude},{location.longitude}", 
                radius=radius_input, 
                category_id=category_id
            )

            if places:
                m = folium.Map(location=coordinates, zoom_start=15)

                for place in places:
                    name = place.get("name", "Unknown Place")
                    address = place.get("location", {}).get("address", "Address not available")
                    latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                    longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                    photo_urls = get_place_photos(place.get("fsq_id", ""))
                    reviews = get_place_reviews(place.get("fsq_id", ""))

                    if latitude and longitude:
                        popup_content = f"<b>{name}</b><br>{address}"
                        folium.Marker(
                            [latitude, longitude], 
                            popup=popup_content, 
                            icon=Icon(icon="cutlery", icon_color="white", color="green", prefix="fa")
                        ).add_to(m)

                    display_place_info(name, address, photo_urls, reviews)

                st_folium(m, width=800, height=500)
            else:
                st.write("No sensory-friendly places found in the specified radius.")
        else:
            st.error("Unable to geocode the location. Please try again.")

if __name__ == "__main__":
    main()