import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os
import requests
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config
from config import (
    FOURSQUARE_API_URL_PHOTOS,
    FOURSQUARE_API_URL_REVIEWS,
    FOURSQUARE_API_URL_SEARCH,
    FOURSQUARE_CATEGORIES
)
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')

@st.cache_data
def geocode_location(location_input):
    """Geocode a location using Nominatim."""
    geolocator = Nominatim(user_agent="streamlit_app")
    return geolocator.geocode(location_input)

def fetch_data(url, headers, params=None):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def business_selection():
    """Take in user input on prefered business."""
    selected_category = st.selectbox(
        "Select the business category you are interested in:",
        list(FOURSQUARE_CATEGORIES.keys()), index=0
    )
    st.write(f"You selected: **{selected_category}**")
    return FOURSQUARE_CATEGORIES[selected_category]

def is_accessible(place):
    """Check if a place has accessibility-related keywords."""
    # What’s new in Google accessibility: https://www.youtube.com/playlist?list=PL590L5WQmH8ce6ZPBbh0v1XVptLJXmQ0K
    accessibility_keywords = [
        "wheelchair",
        "accessible",
        # "wheelchair accessible entrance", # too specific, getting filtered out
        # "wheelchair accessible restroom", # too specific, getting filtered out 
        # "wheelchair accessible seating", # too specific, getting filtered out
        # "wheelchair accessible parking", # too specific, getting filtered out
        # "wheelchair-accessible elevator" # too specific, getting filtered out
        "elevator",
        "ramp"
    ]
    # Combine relevant fields to search for keywords
    place_info = (
        place.get("description", "") + 
        " ".join([review["text"] for review in get_place_reviews(place.get("fsq_id", ""))])
    ).lower()

    # Check for any accessibility keyword
    return any(keyword in place_info for keyword in accessibility_keywords)

def get_place_photos(place_id):
    """Fetch photos for a place from Foursquare API."""
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    url = FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id)
    data = fetch_data(url, headers)
    return [photo["prefix"] + "300x300" + photo["suffix"] for photo in data] if data else []

def get_place_reviews(place_id):
    """Fetch reviews for a place from Foursquare API."""
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

def get_sensory_friendly_places(location, radius=1000, category_id=None):
    """Fetch sensory-friendly places using Foursquare API."""
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    sensory_keywords = [
        "ambiance",
        "autism",
        "booth",
        "cozy",
        "dim", 
        "low-lighting",
        "peaceful", 
        "quiet", 
        "sensory"
        # "sensory-friendly" # pulled in reviews where customer service was friendly
    ]
    params = {
        "ll": location,
        "radius": radius,
        "query": " OR ".join(sensory_keywords),
        "limit": 10,
    }
    
    if category_id:
        if isinstance(category_id, list):  # Ensure correct format
            category_id = ",".join(map(str, category_id))
        params["categories"] = category_id  # Use correct parameter name

    # Debugging use only
    #st.write("API Request Parameters:", params)  
    
    data = fetch_data(FOURSQUARE_API_URL_SEARCH, headers, params)
    return data.get("results", []) if data else []

def display_place_info(name, address, photos, reviews):
    """Display place information including photos and reviews."""
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

def send_email(name, sender_email, message):
    """Send the email from the contact page."""
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise ValueError("Email credentials not found. Ensure they are set properly.")
    
    msg = MIMEMultipart('alternative')
    msg['From'], msg['To'], msg['Subject'] = sender_email, EMAIL_USERNAME, "Sensory Heaven Contact Form Submission"
    msg.attach(MIMEText(f"<html><body><p><strong>Name:</strong> {name}</p><p><strong>Email (sender):</strong> {sender_email}</p><p><strong>Message:</strong> {message}</p></body></html>", 'html'))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(sender_email, EMAIL_USERNAME, msg.as_string())

def contact_form():
    """Streamlit contact form."""
    user_name, user_email, user_message = st.text_input("Your Name"), st.text_input("Your Email"), st.text_area("Your Message")
    if st.button("Submit"):
        if not all([user_name, user_email, user_message]):
            st.error("All fields are required!")
        elif "@" not in user_email or not any(domain in user_email for domain in [".net", ".com", ".edu"]):
            st.error("Please enter a valid email address!")
        else:
            try:
                send_email(user_name, user_email, user_message)
                st.success("Thank you! Your message has been sent.")
            except Exception as e:
                st.error(f"Failed to send your message: {e}")

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Find", "Learn", "Contact", "Donate"])

    if page == "Find":
        st.title("Sensory Heaven - Find")
        location_input = st.text_input("Enter a location:", "Boston")
        radius_input = st.slider("Set the radius (meters):", 100, 5000, 1000, 100)
        category_id = business_selection()

        if location_input:
            location = geocode_location(location_input)
            if location:
                coordinates = [location.latitude, location.longitude]
                st.write(f"Coordinates for {location_input}: {coordinates}")

                # Fetch sensory-friendly places
                sensory_places = get_sensory_friendly_places(
                    f"{location.latitude},{location.longitude}", 
                    radius=radius_input, 
                    category_id=category_id
                )
                
                if sensory_places:
                    m = folium.Map(location=coordinates, zoom_start=15)
                    
                    # Iterate over each place to display on the map and in the UI
                    for place in sensory_places:
                        name = place.get("name", "Unknown Place")
                        address = place.get("location", {}).get("address", "Address not available")
                        latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                        longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                        photo_urls = get_place_photos(place.get("fsq_id", ""))
                        reviews = get_place_reviews(place.get("fsq_id", ""))
                        accessible = is_accessible(place)
                        
                        if latitude and longitude:
                            popup_content = f"<b>{name}</b><br>{address}"
                            
                            # Add markers to the map based on accessibility
                            folium.Marker(
                                [latitude, longitude], 
                                popup=popup_content, 
                                icon=Icon(
                                    icon="wheelchair" if accessible else "smile", 
                                    icon_color="white", 
                                    color="blue" if accessible else "green", 
                                    prefix="fa"
                                )
                            ).add_to(m)
                        
                        # Display place information below the map
                        display_place_info(name, address, photo_urls, reviews)
                        
                    # Render the map
                    st_folium(m, width=800, height=500)
                else:
                    st.write("No sensory-friendly places found in the specified radius.")
            else:
                st.error("Unable to geocode the location. Please try again.")

    elif page == "Learn":
        st.title("Sensory Heaven - Learn")
        st.write("""
        **What is sensory-friendly?**  
        Sensory-friendly spaces are designed to accommodate individuals who experience sensory sensitivities.
        """)
        st.write("""
        **Features:**  
        If a business has these _keywords_ in either their business profile or reviews then the establishment will be flagged as sensory friendly.
        - ambiance
        - autism
        - booth
        - cozy
        - dim
        - low-lighting
        - peaceful
        - quiet
        - sensory-friendly
        """)


    elif page == "Contact":
        st.title("Sensory Heaven - Contact")
        contact_form()

    elif page == "Donate":
        st.title("Sensory Heaven - Donate")
        
        st.write("""Are you enjoying the app? Is it helpful? If you would like to throw in a few bucks to help me cover the ongoing costs of these API services, that would be much appreciated.
                Below I have added two options, you can choose the one that is convenient to you.
                Again, I really appreciate your support!""")

        # Creating an expander for Venmo
        with st.expander("Venmo"):
            st.write("Venmo link: https://venmo.com/code?user_id=2471244549062656744")
            st.image('Media/venmo_qr.jpg', caption='Venmo QR code')

        # Creating an expander for CashApp
        with st.expander("CashApp"):
            st.write("Venmo link: https://cash.app/$claireykraft")
            st.image('Media/cashapp_qr.jpg', caption='CashApp QR code')
            
if __name__ == "__main__":
    main()