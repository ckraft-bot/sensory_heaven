import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
import requests
from config import *
from geopy.geocoders import Nominatim

def business_selection():
    selected_category = st.selectbox(
        "Select the business category you are interested in?",
        options=list(CATEGORIES.keys()),
        index=0
    )
    st.sidebar.write(f"You selected: **{selected_category}**")
    return CATEGORIES[selected_category]

def fetch_data(url, headers, params=None):
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

# maybe on another tab?
def get_accessible_places(location, radius=1000, category_id=None):
    """
    Fetches accessible places from the Foursquare API using specific accessibility tags and categories.
    
    Args:
        location (str): The latitude and longitude of the location, formatted as "lat,lng".
        radius (int): Search radius in meters (default is 1000).
        category_id (str, optional): The ID of a specific category to filter by.

    Returns:
        list: A list of accessible places matching the query.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    # Accessibility-related tags and categories
    accessibility_keywords = [
        "accessible", 
        "wheelchair accessible", 
        "family-friendly", 
        "ramps", 
        "accessible parking", 
        "accessible toilets", 
    ]

    # Build the query using OR to include multiple keywords
    params = {
        "ll": location,
        "radius": radius,
        "query": " OR ".join(accessibility_keywords),
        "limit": 10,  # Limit the results for performance
    }

    # Add categoryId if provided (e.g., specific business categories)
    if category_id:
        params["categoryId"] = category_id

    # Fetch data from the Foursquare API
    response = requests.get(FOURSQUARE_API_URL_SEARCH, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])  # Return the results
    else:
        # Handle errors and return an empty list if the request fails
        st.error(f"Error fetching accessible places: {response.status_code}")
        return []

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

def main():
    st.title("Sensory Heaven")
    st.write("Discover sensory-friendly businesses near you.")

    location_input = st.text_input("Enter a location (city, address, or coordinates):", "Stockholm")
    radius_input = st.slider("Set the radius (meters):", min_value=100, max_value=5000, value=1000, step=100)
    category_id = business_selection()

    if location_input:
        geolocator = Nominatim(user_agent="streamlit_app")
        location = geolocator.geocode(location_input)
        if location:
            coordinates = [location.latitude, location.longitude]
            st.write(f"Coordinates for {location_input}: {coordinates}")

            places = get_sensory_friendly_places(f"{location.latitude},{location.longitude}", radius=radius_input, category_id=category_id)

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
                        eating_icon = Icon(icon="cutlery", icon_color="white", color="green", prefix="fa")
                        popup_content = f"<b>{name}</b><br>{address}"
                        folium.Marker([latitude, longitude], popup=popup_content, icon=eating_icon).add_to(m)

                    st.subheader(name)
                    st.write(f"Address: {address}")

                    if photo_urls:
                        st.image(photo_urls[0], caption=name, width=300)
                    else:
                        st.write("No photos available.")

                    if reviews:
                        st.write("Reviews:")
                        for review in reviews:
                            st.write(f"- {review['user']}: {review['text']}")
                    else:
                        st.write("No reviews available.")

                st_folium(m, width=800, height=500)
            else:
                st.write("No sensory-friendly places found in the specified radius.")
        else:
            st.error("Unable to geocode the location. Please try again.")

if __name__ == "__main__":
    main()