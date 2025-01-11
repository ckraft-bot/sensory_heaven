import streamlit as st
import folium  # For drawing maps
import requests
import config
from config import *  # Assuming FOURSQUARE_API_KEY and URL are stored in config.py

# Function to get sensory-friendly places from Foursquare API
def get_sensory_friendly_places(location, radius=500):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    
    # Search for sensory-friendly places
    params = {
        "ll": location,  # Latitude and longitude
        "radius": radius,  # Radius around location
        "query": "sensory friendly",  # Search query
        "limit": 10  # Number of results to fetch
    }

    # Make the request to get places
    response = requests.get(FOURSQUARE_API_URL_SEARCH, headers=headers, params=params)
    if response.status_code != 200:
        st.error(f"Error: {response.status_code}")
        return []
    
    places_data = response.json()
    places = places_data.get("results", [])

    # Now get photos for each place
    for place in places:
        place_id = place["fsq_id"]  # Extract the place ID
        photo_url = get_place_photos(place_id)
        place["photo_url"] = photo_url  # Add photo URL to place data

    return places

# Function to get photos for a specific place using its fsq_id
def get_place_photos(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    # Request photos for the place
    params = {
        "limit": 1  # You can adjust how many photos you want
    }
    
    response = requests.get(f"{FOURSQUARE_API_URL_PHOTOS}/{place_id}/photos", headers=headers, params=params)
    if response.status_code == 200:
        photos_data = response.json()
        if photos_data["results"]:
            # Return the first photo URL (you can select other sizes too)
            return photos_data["results"][0]["prefix"] + "500x500" + photos_data["results"][0]["suffix"]
    return None  # If no photos found

# Function to display the map
def display_map(location, places):
    # Create a Folium map centered at the user's location
    map_ = folium.Map(location=location, zoom_start=14)
    
    # Add markers for each place
    for place in places:
        name = place.get("name")
        lat = place["geocodes"]["main"]["lat"]
        lon = place["geocodes"]["main"]["lng"]
        address = place.get("location", {}).get("address", "No address")
        rating = place.get("rating", "No rating")
        photo_url = place.get("photo_url", None)

        # Popup info
        popup_text = f"<b>{name}</b><br>{address}<br>Rating: {rating}<br>"
        if photo_url:
            popup_text += f"<img src='{photo_url}' width='100' height='100'/>"
        
        # Create a marker on the map
        folium.Marker([lat, lon], popup=popup_text).add_to(map_)
    
    # Return the map object
    return map_

# Streamlit app UI
st.title("Sensory-Friendly Places Finder")
st.write("Find sensory-friendly places near you!")

# User inputs for location
location = st.text_input("Enter a location (city or address):", "New York")
radius = st.slider("Radius (meters):", 100, 5000, 500)

# Fetch places based on the location entered
if location:
    # Get latitude and longitude for the location (you can expand this with geocoding APIs)
    # Example: New York coordinates (you can replace this with dynamic geocoding in the future)
    if location.lower() == "new york":
        lat, lon = 40.7128, -74.0060  # Default New York City coordinates
    else:
        lat, lon = 40.7128, -74.0060  # Placeholder for other location input

    location = f"{lat},{lon}"
    places = get_sensory_friendly_places(location, radius)
    
    # Display the map with places
    map_ = display_map([lat, lon], places)
    st.components.v1.html(map_._repr_html_(), height=500)

    # Show details of the places
    st.write(f"Found {len(places)} sensory-friendly places nearby.")
    for place in places:
        name = place.get("name")
        address = place.get("location", {}).get("address", "No address")
        rating = place.get("rating", "No rating")
        st.write(f"{name} - {address} - Rating: {rating}")
