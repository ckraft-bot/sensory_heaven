import os
import requests
import smtplib
from urllib.parse import quote_plus
import ssl
import streamlit as st
import folium
from folium import Icon
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config
from config import (
    get_foursquare_url,
    FOURSQUARE_API_BASE_URL,
    FOURSQUARE_CATEGORIES,
)

FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# API URLs
FOURSQUARE_API_URL_PLACES = get_foursquare_url("search")
FOURSQUARE_API_URL_DETAILS = get_foursquare_url("{fsq_id}")
FOURSQUARE_API_URL_PHOTOS = get_foursquare_url("{fsq_id}/photos", params="?limit=1&sort=NEWEST&classifications=indoor")
FOURSQUARE_API_URL_REVIEWS = get_foursquare_url("{fsq_id}/tips", params="?limit=5&fields=text&sort=NEWEST")

HEADERS = {"Authorization": FOURSQUARE_API_KEY}

#-------------------------------------------------- Utility Functions --------------------------------------------------#
@st.cache_data
def geocode_location(location_input):
    """Geocode a location using Nominatim."""
    geolocator = Nominatim(user_agent="streamlit_app")
    return geolocator.geocode(location_input)

def fetch_data(url, params=None):
    """Fetch data from Foursquare API."""
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        st.error(f"API request failed ({response.status_code}): {response.text}")
        return {}
    try:
        return response.json()
    except ValueError as e:
        st.error(f"Failed to parse JSON response: {e}")
        return {}

#-------------------------------------------------- Foursquare API Calls --------------------------------------------------#
def get_sensory_friendly_places(latitude, longitude, radius=None, category_id=None):
    """Fetch sensory-friendly places from Foursquare API, including sensory keywords."""
    
    # Sensory Keywords to filter places
    sensory_keywords = [
        "quiet", "calm", "low lighting", "soft music",
        "not crowded", "spacious", "gentle lighting",
        "low noise", "comfortable seating", "sensory friendly"
    ]
    
    # This step combines all the words in the 'sensory_keywords' list into one long string.
    # The 'join' function adds a space between each keyword in the list.
    # Example: "quiet calm low lighting soft ... sensory friendly"
    query_string = " ".join(sensory_keywords)

    # This step ensures that the entire query string can be sent over the web properly.
    # URL encode the query string to make it safe to include in the API request URL
    # 'quote_plus' converts special characters like spaces into URL-safe characters.
    # A space between words becomes '%20', which is the URL encoding for a space.
    # example: quiet%20calm%20low%20lighting%20soft%20music%20not%20crowded%20spacious%20gentle%20lighting%20low%20noise%20comfortable%20seating%20sensory-friendly
    encoded_query = quote_plus(query_string)  

    # Use Foursquare API URL to make the request
    url = get_foursquare_url("search", params=f"?ll={latitude}%2C{longitude}&radius={radius}&limit=10&categories={category_id}&query={encoded_query}")
    data = fetch_data(url)
    
    # Return the list of results
    return data.get("results", []) if data else []

def is_accessible(place):
    """Determine if the place is accessible based on keywords or attributes."""
    
    # Define accessibility keywords that suggest the establishment is accessible
    accessible_keywords = [
        "wheelchair", "accessible", "ramp", "elevator", "wide doors", "barrier-free", "ADA", "mobility"
    ]
    
    # Check if any of the keywords are in the place's name, address, or reviews
    name = place.get("name", "").lower()
    address = place.get("location", {}).get("address", "").lower()
    reviews = get_place_reviews(place.get("fsq_id", ""))
    
    # Search for accessibility keywords in name, address, or reviews
    for keyword in accessible_keywords:
        if keyword.lower() in name or keyword.lower() in address:
            return True
        for review in reviews:
            if keyword.lower() in review.get("text", "").lower():
                return True
    
    if place.get('wheelchair_access', False):
        return True
    
    return False

def get_place_details(place_id):
    return fetch_data(FOURSQUARE_API_URL_DETAILS.format(fsq_id=place_id))

def get_place_photos(place_id):
    data = fetch_data(FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id))
    return [photo["prefix"] + "300x300" + photo["suffix"] for photo in data] if data else []

def get_place_reviews(place_id):
    data = fetch_data(FOURSQUARE_API_URL_REVIEWS.format(fsq_id=place_id))
    return [{"user": tip.get("user", {}).get("firstName", "Anonymous"), "text": tip.get("text", "")} for tip in data] if data else []

#-------------------------------------------------- UI & Display Functions --------------------------------------------------#
def display_place_info(name, address, photos, reviews):
    """Display place information in Streamlit."""
    st.subheader(name)
    st.write(f"**Address**: {address or 'N/A'}")
    
    if photos:
        st.image(photos[0], caption=name, width=300)
    else:
        st.write("No photos available.")
    
    st.write("**Reviews:**")
    if reviews:
        for review in reviews:
            st.write(f"- {review['user']}: {review['text']}")
    else:
        st.write("No reviews available.")

def business_selection():
    """Dropdown to select a business category."""
    selected_category = st.selectbox("Select a business category:", list(FOURSQUARE_CATEGORIES.keys()))
    return FOURSQUARE_CATEGORIES.get(selected_category)

def contact_form():
    """Contact form for user messages."""
    user_name = st.text_input("Your Name")
    user_email = st.text_input("Your Email")
    user_message = st.text_area("Your Message")

    if st.button("Submit"):
        if not all([user_name, user_email, user_message]):
            st.error("All fields are required!")
        elif "@" not in user_email or not any(domain in user_email for domain in [".net", ".com", ".edu"]):
            st.error("Please enter a valid email address!")
        else:
            try:
                send_email(user_name, user_email, user_message)
                st.success("Your message has been sent.")
            except Exception as e:
                st.error(f"Failed to send your message: {e}")

def send_email(name, sender_email, message):
    """Send email via SMTP."""
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise ValueError("Email credentials not found.")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = EMAIL_USERNAME
    msg['Subject'] = "Sensory Heaven Contact Form Submission"
    msg.attach(MIMEText(f"<html><body><p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {sender_email}</p><p><strong>Message:</strong> {message}</p></body></html>", 'html'))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(sender_email, EMAIL_USERNAME, msg.as_string())

def credit():
    """Credits section."""
    st.markdown("""<div style='text-align: center;'>
        <p>Developed with ❤️ by Claire Kraft</p>
        <p>Powered 🔌 by Foursquare</p>
    </div>""", unsafe_allow_html=True)

def explanation():
    st.write("""
    **What is sensory-friendly?**  
    Sensory-friendly spaces are designed to accommodate individuals who experience sensory sensitivities.
    
    **Call to action:**  
    Autistic individuals often report that their external environments can be overwhelming due to sensory sensitivities. 
    This app aims to help users discover establishments that offer a more accommodating and tolerable experience. 
    While the app is primarily designed for individuals with sensory sensitivities, it is also beneficial for wheelchair users, those with chronic illnesses, neurodivergent individuals, anyone experiencing anxiety, and loved ones of these populations. 
    It is essential that people with disabilities have opportunities to enjoy public spaces, be included in the community, and feel a sense of belonging in society. 
    
    Currently, there is no such app on the market; this presents a prime opportunity to fill the gap. 
    I invite you to join me in imporving this app for everyone. 
    Look at the "Features" list below to see what features are driving the search results on the "Find" tab and offer feedback on the features (to add, or modify, or omit). 
    You can contact me via the "Contact" tab.
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

def donate():
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

#-------------------------------------------------- UI --------------------------------------------------#
def main():
    """Main function to handle page navigation."""
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Find", "Learn", "Contact", "Donate"])

    logo_path = 'Media/sensory_heaven_logo.png' 
    st.logo(logo_path, size='large') 

    if page == "Find":
        st.title("Sensory Heaven - Find")
        st.logo(logo_path, size='large') 

        # User input fields
        location_input = st.text_input("Enter a location:", placeholder="e.g., Boston, MA")

        # Slider in miles (converted to meters)
        radius_miles = st.slider("Set the radius (miles):", 1, 10, 1, 1)  # min, max, default, step size (1 mile increments)
        radius = radius_miles * 1609  # Convert miles to meters

        category_id = business_selection() 

        if st.button("Find"):  # Button triggers API calls
            if location_input:
                location = geocode_location(location_input)
                if location:
                    coordinates = [location.latitude, location.longitude]
                    st.session_state["location_coordinates"] = coordinates  # Store location
                    
                    # Fetch sensory-friendly places using converted meters
                    sensory_places = get_sensory_friendly_places(
                        location.latitude, 
                        location.longitude, 
                        radius=radius, 
                        category_id=category_id
                    )

                    st.session_state["sensory_places"] = sensory_places  # Store places
                else:
                    st.error("Unable to geocode the location. Please try again.")

        # Display results if they exist in session state
        if "sensory_places" in st.session_state and st.session_state["sensory_places"]:
            coordinates = st.session_state.get("location_coordinates", [0, 0])
            
            # Dynamically adjust the zoom level based on radius
            # If radius is smaller (1 mile), use a higher zoom level (e.g., 15)
            # If radius is larger (10 miles), use a lower zoom level (e.g., 12)
            zoom_level = 15 - (radius_miles - 1)
            
            # Center map based on user location input
            m = folium.Map(location=coordinates, zoom_start=zoom_level)

            for place in st.session_state["sensory_places"]:
                name = place.get("name", "Unknown Place")
                address = place.get("location", {}).get("address", "Address not available")
                latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                photo_urls = get_place_photos(place.get("fsq_id", ""))
                reviews = get_place_reviews(place.get("fsq_id", ""))
                accessible = is_accessible(place)

                # Set icon based on accessibility
                if accessible:
                    icon = Icon(
                        icon="wheelchair",  
                        icon_color="white",
                        color="blue",  
                        prefix="fa"
                    )
                else:
                    icon = Icon(
                        icon="smile",
                        icon_color="white",
                        color="green", 
                        prefix="fa"
                    )
                    
                tooltip_content = f"<b>{name}</b><br>{address}"
                if latitude and longitude:
                    popup_content = f"<b>{name}</b><br>{address}"
                    folium.Marker(
                        [latitude, longitude], 
                        popup=popup_content, 
                        icon=icon,  # Use the icon defined above
                        tooltip=tooltip_content  
                    ).add_to(m)

                display_place_info(name, address, photo_urls, reviews)

            # Display map with sensory-friendly places and markers
            st_folium(m, width=800, height=500)
        else:
            st.write("No sensory-friendly places found. Please try again.")


    elif page == "Learn":
        st.title("Sensory Heaven - Learn")
        st.logo(logo_path, size='large') 
        explanation()
        credit()

    elif page == "Donate":
        st.title("Sensory Heaven - Donate")
        st.logo(logo_path, size='large') 
        donate()
        credit()

    elif page == "Contact":
        st.title("Sensory Heaven - Contact")
        st.logo(logo_path, size='large') 
        contact_form()
        credit()

if __name__ == "__main__":
    main()
