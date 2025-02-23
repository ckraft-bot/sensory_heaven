import os
import requests
import smtplib
import ssl
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config
from config import (
    get_foursquare_url,
    FOURSQUARE_API_BASE_URL,
    FOURSQUARE_CATEGORIES,
    sensory_keywords
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
    """Fetch sensory-friendly places from Foursquare API."""
    params = {"ll": f"{latitude},{longitude}", "limit": 10, "radius": radius, "categories": category_id}
    data = fetch_data(FOURSQUARE_API_URL_PLACES, params)
    return data.get("results", []) if data else []

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

        location_input = st.text_input("Enter a location:", placeholder="e.g., Boston, MA")
        radius = st.slider("Set the radius (miles):", 1, 10, 1, 1) * 1609
        category_id = business_selection()

        if st.button("Find") and location_input:
            location = geocode_location(location_input)
            if location:
                places = get_sensory_friendly_places(location.latitude, location.longitude, radius, category_id)
                for place in places:
                    display_place_info(
                        place.get("name", "Unknown"),
                        place.get("location", {}).get("address", "N/A"),
                        get_place_photos(place.get("fsq_id", "")),
                        get_place_reviews(place.get("fsq_id", ""))
                    )
            else:
                st.error("Unable to geocode location.")
        credit()

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
