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
    """Fetch sensory-friendly places using Google Places Nearby Search API, filtered to show restaurants, bars, cafes, and coffee shops."""
    url = GOOGLE_MAPS_API_NEARBY
    sensory_keywords = [
        "autism", 
        "cozy", 
        "dim", 
        "peaceful",
        "quiet", 
        "booth", 
        "plant",  
        "low-lighting",
        "dimmed lighting",
        "sensory friendly",
        "sensory-friendly"
    ]
    
    # Standardize keywords to uppercase
    standardized_keywords = [keyword.upper() for keyword in sensory_keywords]
    
    # Expanding the scope to include restaurants, bars, cafes, and coffee shops
    place_types = "restaurant|bar|cafe|coffee_shop"
    
    params = {
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "keyword": " OR ".join(standardized_keywords),
        "type": place_types,
        "key": GOOGLE_MAPS_API_KEY,
    }
    
    data = fetch_data(url, headers=None, params=params)
    if data and data.get("results"):
        return data["results"][:10]
    return []

def get_place_details(place_id):
    """Fetch place details using Google Maps API, including rating, user ratings, opening hours, URL, and accessibility information."""
    url = GOOGLE_MAPS_API_PLACES_DETAILS
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,photo,review,rating,user_ratings_total,opening_hours,url,types", 
        "key": GOOGLE_MAPS_API_KEY
    }
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
                st.write(f"{review['text']}")
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
                    place_details = get_place_details(place_id)

                    # Rating and total reviews
                    rating = place_details.get("rating", "No rating available")
                    user_ratings_total = place_details.get("user_ratings_total", 0)

                    # Fetch the photo
                    photo_reference = place_details.get("photos", [{}])[0].get("photo_reference")
                    photo_url = get_place_photos(photo_reference) if photo_reference else None

                    # Reviews
                    reviews = place_details.get("reviews", [])

                    # Opening hours (if available)
                    opening_hours = place_details.get("opening_hours", {}).get("weekday_text", [])

                    # URL to the Google Maps page of the place
                    url = place_details.get("url", "No URL available")

                    # Accessibility-related keywords
                    # accessibility_keywords = [
                    #     "wheelchair accessible parking lot", 
                    #     "wheelchair accessible seating", 
                    #     "wheelchair accessible restroom", 
                    #     "wheelchair accessible entrance",
                    #     "elevator", 
                    #     "lift"
                    # ]
                    # types = place_details.get("types", [])
                    # accessible = any(keyword.lower() in " ".join(types).lower() for keyword in accessibility_keywords)

                    # Displaying the restaurant high level information
                    st.write(f"### {name}")
                    #st.write(f"**Address**: {address} [take me to Google Maps]({url})")
                    st.write(f"**[{address}]({url})**")

                    if photo_url:
                        st.image(photo_url, caption=f"Photo of {name}", use_container_width=True)

                    # Opening Hours (collapsible)
                    if opening_hours:
                        with st.expander("Opening Hours"):
                            for day in opening_hours:
                                st.write(day)
                    else:
                        st.write("No opening hours available.")

                    # Rating & Review Count (collapsible)
                    with st.expander("Rating & Reviews"):
                        st.write(f"Rating: {rating}")
                        st.write(f"Review Count: {user_ratings_total}")
                        if reviews:
                            for review in reviews:
                                st.write(f"{review['text']}")
                        else:
                            st.write("No reviews available :speech_balloon:")



                    # Displaying accessibility information
                    # if accessible:
                    #     st.write("This place is accessible.")
                    # else:
                    #     st.write("No explicit accessibility information found.")

                    # Map Marker
                    if latitude and longitude:
                        popup_content = f"<b>{name}</b><br>{address}"
                        folium.Marker(
                            [latitude, longitude],
                            popup=popup_content,
                            icon=Icon(icon="cutlery", prefix="fa", color="green")
                        ).add_to(m)

                st_folium(m, width=800, height=500)
            else:
                st.write("No sensory-friendly places found in the specified radius.")
        else:
            st.error("Unable to geocode the location. Please try again.")
if __name__ == "__main__":
    main()