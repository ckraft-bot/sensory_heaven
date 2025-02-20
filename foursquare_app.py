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
    FOURSQUARE_API_URL_PLACES,
    FOURSQUARE_API_URL_DETAILS,
    FOURSQUARE_API_URL_PHOTOS,
    FOURSQUARE_API_URL_REVIEWS,
    FOURSQUARE_CATEGORIES,
    sensory_keywords
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
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429: # out of credit
            st.error("Sorry for the inconvenience, the API limit has been reached. Please try again later.")
        elif response.status_code == 401: # oauth token invalid
            st.error("Sorry for the inconvenience, the oauth token is invalid. Please try again later.")
        else:
            st.error("Sorry for the inconvenience. Please try again later.")
            # for debugging
            st.error(f"HTTP error occurred: {http_err}")
        return None
    except requests.RequestException as e:
        # for debugging
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

# accessiblility through keyword search in reviews and descriptions
# def is_accessible(place):
#     """Check if a place has accessibility-related keywords."""
#     # What’s new in Google accessibility: https://www.youtube.com/playlist?list=PL590L5WQmH8ce6ZPBbh0v1XVptLJXmQ0K
#     accessibility_keywords = [
#         "wheelchair",
#         "accessible",
#         # "wheelchair accessible entrance", # too specific, getting filtered out
#         # "wheelchair accessible restroom", # too specific, getting filtered out 
#         # "wheelchair accessible seating", # too specific, getting filtered out
#         # "wheelchair accessible parking", # too specific, getting filtered out
#         # "wheelchair-accessible elevator" # too specific, getting filtered out
#         "elevator",
#         "ramp"
#     ]
#     # Combine relevant fields to search for keywords
#     place_info = (
#         place.get("description", "") + 
#         " ".join([review["text"] for review in get_place_reviews(place.get("fsq_id", ""))])
#     ).lower()

#     # Check for any accessibility keyword
#     return any(keyword in place_info for keyword in accessibility_keywords)

def is_accessible(place):
    """Check if a place is ADA compliant."""
    return place.get("wheelchair_accessible", False)

def get_place_photos(place_id):
    """Fetch photos for a place from Foursquare API."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}"
        #"Authorization": FOURSQUARE_API_KEY
}

    url = FOURSQUARE_API_URL_PHOTOS.format(fsq_id=place_id)
    data = fetch_data(url, headers)
    return [photo["prefix"] + "300x300" + photo["suffix"] for photo in data] if data else []

def get_place_reviews(place_id):
    """Fetch reviews for a place from Foursquare API."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}"
        #"Authorization": FOURSQUARE_API_KEY
    }
    url = FOURSQUARE_API_URL_REVIEWS.format(fsq_id=place_id)
    data = fetch_data(url, headers)
    return [
        {"user": tip.get("user", {}).get("firstName", "Anonymous"), "text": tip.get("text", "")}
        for tip in data
    ] if data else []

# def get_sensory_friendly_places(location, radius=None, category_id=None):
#     """Fetch sensory-friendly places using Foursquare API."""
#     headers = {
#         "Accept": "application/json",
#         "Authorization": f"Bearer {FOURSQUARE_API_KEY}"
#         #"Authorization": FOURSQUARE_API_KEY
#     }

#     params = {
#         "ll": location,
#         "radius": radius,
#         #"query": "",
#         #"query": " OR ".join(sensory_keywords),
#         "limit": 10,
#     }
    
#     if category_id:
#         if isinstance(category_id, list):  # Ensure correct format
#             category_id = ",".join(map(str, category_id))
#         params["categories"] = category_id  # Use correct parameter name

#     # for debugging
#     st.write("API Request Parameters:", params)  
#     data = fetch_data(FOURSQUARE_API_URL_SEARCH, headers, params)
#     return data.get("results", []) if data else []

# for debugging
def get_sensory_friendly_places(location, radius=None, category_id=None):
    """Fetch sensory-friendly places using Foursquare API."""
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {FOURSQUARE_API_KEY}"
    }

    params = {
        "ll": location,
        "radius": radius,
        "limit": 10,
    }
    
    if category_id:
        if isinstance(category_id, list):  # Ensure correct format
            category_id = ",".join(map(str, category_id))
        params["categories"] = category_id  # Use correct parameter name

    # Debugging: Print API Request Parameters and the full URL
    st.write("API Request Parameters:", params)
    prepared_request = requests.Request("GET", FOURSQUARE_API_URL_SEARCH, params=params).prepare()
    full_url = prepared_request.url
    st.write("Request URL:", full_url)

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
    page = st.sidebar.radio("Go to", ["Find", "Learn", "Contact", "Donate"])
    logo_path = 'Media/sensory_heaven_logo.png' 

    if page == "Find":
        st.title("Sensory Heaven - Find")
        st.logo(logo_path, size='large') 

        # User input fields
        location_input = st.text_input("Enter a location:", placeholder="e.g., Boston, MA")

        # Slider in miles (converted to meters)
        radius_miles = st.slider("Set the radius (miles):", 1, 10, 1, 1)  # min, max, default, step size (1 mile increments)
        radius = radius_miles * 1609  # rounding to whole number for api call
        st.write(f"Radius: {type(radius)}")

        category_id = business_selection()
        
        if st.button("Find"):  # Button triggers API calls
            if location_input:
                location = geocode_location(location_input)
                if location:
                    coordinates = [location.latitude, location.longitude]
                    st.session_state["location_coordinates"] = coordinates  # Store location
                    
                    # Fetch sensory-friendly places using converted meters
                    sensory_places = get_sensory_friendly_places(
                        f"{location.latitude},{location.longitude}", 
                        radius=radius, 
                        category_id=category_id
                    )
                    
                    st.session_state["sensory_places"] = sensory_places  # Store places
                else:
                    st.error("Unable to geocode the location. Please try again.")


        # Display results if they exist in session state
        if "sensory_places" in st.session_state and st.session_state["sensory_places"]:
            coordinates = st.session_state.get("location_coordinates", [0, 0])
            m = folium.Map(location=coordinates, zoom_start=15)
            
            for place in st.session_state["sensory_places"]:
                name = place.get("name", "Unknown Place")
                address = place.get("location", {}).get("address", "Address not available")
                latitude = place.get("geocodes", {}).get("main", {}).get("latitude")
                longitude = place.get("geocodes", {}).get("main", {}).get("longitude")
                photo_urls = get_place_photos(place.get("fsq_id", ""))
                reviews = get_place_reviews(place.get("fsq_id", ""))
                accessible = is_accessible(place)
                
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