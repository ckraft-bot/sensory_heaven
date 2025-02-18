import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import os
import requests
from requests.auth import HTTPBasicAuth
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

# Foursquare API keys
FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')

@st.cache_data
def geocode_location(location_input):
    """Geocode a location using Nominatim and return coordinates and Foursquare ID."""
    geolocator = Nominatim(user_agent="streamlit_app")
    try:
        location = geolocator.geocode(location_input)
        if location is None:
            st.error("Unable to geocode the location. Please try again with a different input.")
        return location.latitude, location.longitude, location.address  # Return lat, lon, address
    except Exception as e:
        st.error(f"An error occurred during geocoding: {e}")
        return None, None, None

def fetch_data(url, headers, params=None):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 429:  # Too many requests (rate limited)
            remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
            reset_time = response.headers.get('X-RateLimit-Reset', 'Unknown')
            st.warning(f"API limit reached. Remaining requests: {remaining}. Will reset at: {reset_time}.")
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err} (Status Code: {response.status_code})")
        return None
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def get_place_photos(place_id):
    """Fetch photos for a place from Foursquare API."""
    headers = {"Accept": "application/json", "Authorization": FOURSQUARE_API_KEY}
    url = FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id)
    return fetch_data(url, headers)

def get_place_reviews(place_id):
    """Fetch reviews for a place from Foursquare API."""
    headers = {"Accept": "application/json", "Authorization": FOURSQUARE_API_KEY}
    url = FOURSQUARE_API_URL_REVIEWS.format(fsq_id=place_id)
    return fetch_data(url, headers)

def is_accessible(place_id):
    """Check if a place has wheelchair accessibility based on place details."""
    url = FOURSQUARE_API_URL_SEARCH.format(fsq_id=place_id)
    headers = {
        "Accept": "application/json",
        "Authorization": FOURSQUARE_API_KEY
    }
    
    # Fetch the place details using the Foursquare API
    data = fetch_data(url, headers)
    
    # Check for wheelchair accessibility (or other similar fields)
    if data and 'data' in data:
        wheelchair_accessible = data['data'].get("wheelchairAccessible", None)  # Adjust based on actual response fields
        if wheelchair_accessible is not None:
            return wheelchair_accessible  # Return True/False if available
    return False  # Default to False if the data is unavailable

def get_sensory_friendly_places(coordinates, radius=1000, category_id=None):
    """Fetch sensory-friendly places using Foursquare API."""
    headers = {"Accept": "application/json", "Authorization": FOURSQUARE_API_KEY}
    params = {
        "ll": coordinates,  # Pass coordinates as a string 'lat,lng'
        "radius": radius,
        "limit": 10
    }
    
    if category_id:
        params["categories"] = category_id  # Add category filter if provided
    
    return fetch_data(FOURSQUARE_API_URL_SEARCH, headers, params)

def business_selection():
    """Take in user input on preferred business."""
    selected_category = st.selectbox(
        "Select the business category you are interested in:",
        list(FOURSQUARE_CATEGORIES.keys()), index=0
    )
    st.write(f"You selected: **{selected_category}**")
    return FOURSQUARE_CATEGORIES[selected_category]

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

def donate():
    """Streamlit donation options."""
    # Creating an expander for Kofi
    with st.expander("Kofi"):
        st.markdown(
            '<a href="https://ko-fi.com/clairekraft" target="_blank">'
            '<img src="https://miro.medium.com/v2/resize:fit:1200/1*HdRAxEVwO_27UL1e6QhUeA.png" width="100" alt="Buy Me a Coffee">'
            '</a>',
            unsafe_allow_html=True
        )
    
    # Creating an expander for Venmo
    with st.expander("Venmo"):
        st.write("Venmo link: https://account.venmo.com/u/Claire-Kraft-4")
        st.image('Media/venmo_qr.jpg', caption='Venmo QR code')

    # Creating an expander for CashApp
    with st.expander("CashApp"):
        st.write("Venmo link: https://cash.app/$claireykraft")
        st.image('Media/cashapp_qr.jpg', caption='CashApp QR code')

    # Creating an expander for PayPal
    with st.expander("PayPal"):
        st.write("PayPal link: https://paypal.me/KraftClaire?country.x=US&locale.x=en_US")
        st.image('Media/paypal_qr.jpeg', caption='PayPal QR code')

def credit():
    footer_html = """<div style='text-align: center;'>
        <p>Developed with ❤️ by Claire Kraft</p>
        <p>Powered 🔌 by Foursquare</p>
    </div>"""
    st.markdown(footer_html, unsafe_allow_html=True)


def main():
    st.sidebar.title("Navigation")
    logo_path = 'Media/sensory_heaven_logo.png' 
    page = st.sidebar.radio("Go to", ["Find", "Learn", "Contact", "Donate"])
    
    if page == "Find":
        st.logo(logo_path,size='large')
        st.title("Sensory Heaven - Find")

        # User input fields
        location_input = st.text_input("Enter a location:", placeholder="e.g., Boston, MA")

        # Slider in miles (converted to meters)
        radius_miles = st.slider("Set the radius (miles):", 1, 10, 1, 1)  # min, max, default, step size (1 mile increments)
        radius_meters = radius_miles * 1609.344  # Convert miles to meters

        category_id = business_selection()
        
        if st.button("Find"):  # Button triggers API calls
            if location_input:
                latitude, longitude, address = geocode_location(location_input)  # Geocode the location input
                if latitude and longitude:
                    coordinates = f"{latitude},{longitude}"
                    st.session_state["location_coordinates"] = coordinates  # Store coordinates
                    st.session_state["location_address"] = address  # Store address

                    # Pass the geocoded coordinates to Foursquare API call
                    sensory_places = get_sensory_friendly_places(
                        coordinates,  # Use lat, long here
                        radius=radius_meters, 
                        category_id=category_id
                    )

                    st.session_state["sensory_places"] = sensory_places  # Store places
                else:
                    st.error("Unable to geocode the location. Please try again.")
        
        # Display results if they exist in session state
        if "sensory_places" in st.session_state and st.session_state["sensory_places"]:
            coordinates = st.session_state.get("location_coordinates", "")
            m = folium.Map(location=[latitude, longitude], zoom_start=15)

            for place in st.session_state["sensory_places"]:
                name = place.get("name", "Unknown Place")
                address = place.get("location", {}).get("address", "Address not available")
                latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                fsq_id = place.get("fsq_id", "")
                photo_urls = get_place_photos(fsq_id)
                reviews = get_place_reviews(fsq_id)
                accessible = is_accessible(fsq_id)  # Check accessibility

                if latitude and longitude:
                    popup_content = f"<b>{name}</b><br>{address}"
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

                display_place_info(name, address, photo_urls, reviews)

            st_folium(m, width=800, height=500)
        elif "sensory_places" in st.session_state and not st.session_state["sensory_places"]:
            st.write("No sensory-friendly places found in the specified radius.")
        
        credit()

    elif page == "Learn":
        st.logo(logo_path,size='large') 
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
        - sensory
        """)

        credit()

    elif page == "Contact":
        st.logo(logo_path, size='large') 
        st.title("Sensory Heaven - Contact")
        contact_form()

        credit()

    elif page == "Donate":
        st.logo(logo_path, size='large') 
        st.title("Sensory Heaven - Donate")
        
        st.write("""Are you enjoying the app? Is it helpful? If you would like to throw in a few bucks to help me cover the ongoing costs of these API services, that would be much appreciated.
                Below I have added a few options, you can choose the one that is convenient to you.
                Again, I really appreciate your support!""")

        donate()
        credit()
        
if __name__ == "__main__":
    main()