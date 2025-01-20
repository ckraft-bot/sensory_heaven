import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
import requests
from config import *  
from geopy.geocoders import Nominatim  # for geocoding location

# Function to get sensory-friendly restaurants from Foursquare API
def get_sensory_friendly_restaurants(location, radius=1000):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    sensory_keywords = [
        "accessibility", 
        "autism", 
        "cozy",  
        "dim", 
        "peaceful", 
        "quiet", 
    ]
    
    query = " OR ".join(sensory_keywords)
    
    params = {
        "ll": location,
        "radius": radius,
        "query": query,
        "limit": 10,
        # Foursquare category IDs: https://docs.foursquare.com/data-products/docs/categories
        "categoryId": "56aa371be4b08b9a8d573550,"  # 63be6904847c3692a84b9bb5 = Food and Beverage Services
    }

    response = requests.get(FOURSQUARE_API_URL_SEARCH, headers=headers, params=params)
    
    if response.status_code != 200:
        st.error(f"Error: {response.status_code}")
        return []

    places_data = response.json()
    places = places_data.get("results", [])

    for place in places:
        place_id = place.get("fsq_id")
        if place_id:
            photo_urls = get_place_photos(place_id)
            place["photo_urls"] = photo_urls
            reviews = get_place_reviews(place_id)
            place["reviews"] = reviews

    return places


# Function to get photos for a specific place
def get_place_photos(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    url = FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        photos_data = response.json()
        return [
            photo["prefix"] + "300x300" + photo["suffix"]
            for photo in photos_data
        ]
    return None


# Function to get reviews for a specific place
def get_place_reviews(place_id):
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }

    url = FOURSQUARE_API_URL_REVIEWS.format(fsq_id=place_id)
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        reviews_data = response.json()
        return [
            {
                "user": tip.get("user", {}).get("firstName", "Anonymous"),
                "text": tip.get("text", "")
            }
            for tip in reviews_data
        ]
    return []


# Streamlit app layout and content
st.title("Sensory Heaven")
st.write("Discover sensory-friendly restaurants near you.")

# Add a map to the top of the page
location_input = st.text_input("Enter a location (city, address, or coordinates):", "Stockholm")
radius_input = st.slider("Search radius (meters):", min_value=100, max_value=5000, value=1000, step=100)

# geocodes a user-inputted location
# retrieves sensory-friendly places nearby
# and displays them on an interactive map with details such as name, address, photos, and reviews
if location_input:
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(location_input)
    if location:
        coordinates = [location.latitude, location.longitude]
        st.write(f"Coordinates for {location_input}: {coordinates}")

        # Get sensory-friendly places (restaurants only)
        places = get_sensory_friendly_restaurants(f"{location.latitude},{location.longitude}", radius=radius_input)

        if places:
            # Create map centered on the location
            m = folium.Map(location=coordinates, zoom_start=15)

            for place in places:
                name = place.get("name", "Unknown Place")
                address = place.get("location", {}).get("address", "Address not available")
                latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                photo_urls = place.get("photo_urls", [])
                reviews = place.get("reviews", [])

                # Add marker to the map
                if latitude and longitude:
                    # Define the custom icon with a fork and knife (utensils) icon
                    eating_icon = Icon(icon="cutlery", icon_color="white", color="green", prefix="fa") # fa = https://fontawesome.com/

                    popup_content = f"<b>{name}</b><br>{address}"
                    folium.Marker([latitude, longitude], popup=popup_content, icon=eating_icon).add_to(m)

                # Display place details in Streamlit
                st.subheader(name)
                st.write(f"Address: {address}")

                # Display photos
                if photo_urls:
                    st.image(photo_urls[0], caption=name, width=300)
                else:
                    st.write("No photos :camera_with_flash: available.")

                # Display reviews
                if reviews:
                    st.write("Reviews:")
                    for review in reviews:
                        st.write(f"- {review['user']}: {review['text']}")
                else:
                    st.write("No reviews :left_speech_bubble: available.")

            # Render map using st_folium
            st_folium(m, width=800, height=500)
        else:
            st.write("No sensory-friendly restaurants found in the specified radius.")
    else:
        st.error("Unable to geocode the location. Please try again.")
