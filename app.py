import streamlit as st
import folium  # For drawing maps
import requests
import config
from config import *  # Assuming FOURSQUARE_API_KEY and URL are stored in config.py
from geopy.geocoders import Nominatim  # For geocoding location

# Function to get sensory-friendly places from Foursquare API
def get_sensory_friendly_places(location, radius=1000):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    sensory_keywords = [
        "accessible", "autism", "autism-friendly", "calming", "comfortable", 
        "comfortable seating", "dim", "flowers", "low", "noise-cancelling", 
        "peaceful", "quiet", "sensory", "water feature"
    ]

    query = " OR ".join(sensory_keywords)
    
    params = {
        "ll": location,
        "radius": radius,
        "query": query,
        "limit": 10
    }

    response = requests.get(FOURSQUARE_API_URL_SEARCH, headers=headers, params=params)
    
    print("Request URL:", response.url)  # Print the full request URL for debugging

    if response.status_code != 200:
        st.error(f"Error: {response.status_code}")
        print("Error details:", response.json())  # Print the error details
        return []
    
    places_data = response.json()
    print("API Response:", places_data)
    
    places = places_data.get("results", [])

    for place in places:
        place_id = place.get("fsq_id")
        if place_id:
            photo_url = get_place_photos(place_id)
            place["photo_url"] = photo_url
            reviews = get_place_reviews(place_id)
            place["reviews"] = reviews

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

# Function to get reviews for a specific place using its fsq_id
def get_place_reviews(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    
    # Request reviews for the place
    response = requests.get(f"{FOURSQUARE_API_URL_REVIEWS.format(place_id)}", headers=headers)
    if response.status_code == 200:
        reviews_data = response.json()
        reviews = reviews_data.get("response", {}).get("reviews", [])
        return reviews
    return []  # If no reviews found

# Function to display the map
def display_map(location, places):
    # Create a Folium map centered at the user's location
    map_ = folium.Map(location=location, zoom_start=14)
    
    # Add markers for each place
    for place in places:
        try:
            name = place.get("name", "Unnamed place")
            lat = None
            lon = None

            # Try to access geocodes and coordinates
            if "geocodes" in place and "main" in place["geocodes"]:
                lat = place["geocodes"]["main"].get("lat", None)
                lon = place["geocodes"]["main"].get("lng", None)

            # If geocodes are not available, fall back to location coordinates
            if not lat or not lon:
                if "location" in place:
                    lat = place["location"].get("lat", None)
                    lon = place["location"].get("lng", None)

            # If no valid latitude and longitude, skip this place
            if not lat or not lon:
                continue

            address = place.get("location", {}).get("address", "No address")
            rating = place.get("rating", "No rating")
            photo_url = place.get("photo_url", None)
            reviews = place.get("reviews", [])

            # Popup info
            popup_text = f"<b>{name}</b><br>{address}<br>Rating: {rating}<br>"
            if photo_url:
                popup_text += f"<img src='{photo_url}' width='100' height='100'/><br>"
            
            # Add reviews to the popup
            if reviews:
                for review in reviews:
                    user_name = review.get("user", {}).get("firstName", "Anonymous")
                    review_text = review.get("text", "No review text")
                    popup_text += f"<br><i>{user_name}: {review_text}</i>"
            
            # Create a marker on the map
            folium.Marker([lat, lon], popup=popup_text).add_to(map_)
        
        except KeyError as e:
            print(f"Error processing place: {e}")  # Log the error if something goes wrong
    
    # Return the map object
    return map_

# Geocoding function to convert location name to lat/lon
def geocode_location(location_name):
    geolocator = Nominatim(user_agent="sensory_friendly_app")
    location = geolocator.geocode(location_name)
    if location:
        return location.latitude, location.longitude
    return None, None

# Streamlit app UI
st.title("Sensory-Friendly Places Finder")
st.write("Find sensory-friendly places near you!")

# User input for radius in meters
radius_in_meters = st.number_input("Enter radius (in meters):", min_value=1, value=1000, step=100)

# User inputs for location
location_name = st.text_input("Enter a location (city or address):", "New York")

# Fetch places based on the location entered
if location_name:
    lat, lon = geocode_location(location_name)
    if lat and lon:
        location = f"{lat},{lon}"
        places = get_sensory_friendly_places(location, radius=radius_in_meters)

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
            
            # Display reviews
            reviews = place.get("reviews", [])
            if reviews:
                for review in reviews:
                    user_name = review.get("user", {}).get("firstName", "Anonymous")
                    review_text = review.get("text", "No review text")
                    st.write(f"Review by {user_name}: {review_text}")
    else:
        st.error("Location not found.")
