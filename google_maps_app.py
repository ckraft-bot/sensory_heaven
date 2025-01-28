import streamlit as st
from streamlit_folium import st_folium
import os
import requests
import folium
from folium import Icon
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from config import (
    # GOOGLE_MAPS_API_KEY, <-- for nonprod only
    GOOGLE_MAPS_API_PLACES,
    GOOGLE_MAPS_API_PLACES_DETAILS,
    GOOGLE_MAPS_API_NEARBY,
    GOOGLE_MAPS_API_URL_PHOTOS,
    GOOGLE_PLACE_TYPES,
)

# Fetch credentials securely (use environment variables in production)
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY'] # [should match yaml def]

def fetch_data(url, params=None):
    """Fetch data from an API endpoint."""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

@st.cache_data
def geocode_location(location_input):
    """Geocode a location using Google Maps API."""

    params = {"address": location_input, "key": GOOGLE_MAPS_API_KEY} # repinted, secure now
    data = fetch_data(GOOGLE_MAPS_API_PLACES, params=params)
    if data and data.get("results"):
        location = data["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None

def get_sensory_friendly_places(location, radius=1000, place_types="bakery|bar|cafe|restaurant"):
    """Fetch sensory-friendly places using Google Places Nearby Search API."""
    keywords = [
        "autism", "cozy", "dim", "peaceful", "quiet", "booth", "plant", "flower", "low-lighting", "ambiance"
    ]
    params = {
        "location": f"{location[0]},{location[1]}",
        "radius": radius,
        "keyword": " OR ".join(keywords),
        "type": place_types,
        "key": GOOGLE_MAPS_API_KEY, # repinted, secure now
    }
    data = fetch_data(GOOGLE_MAPS_API_NEARBY, params=params)
    return data.get("results", [])[:10] if data else []

def get_place_details(place_id):
    """Fetch detailed information about a place."""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,photo,review,rating,user_ratings_total,opening_hours,url",
        "key": GOOGLE_MAPS_API_KEY, # repinted, secure now
    }
    data = fetch_data(GOOGLE_MAPS_API_PLACES_DETAILS, params=params)
    return data.get("result", {}) if data else {}

def get_place_photos(photo_reference):
    """Construct a photo URL from the photo reference."""
    if not photo_reference:
        return None
    params = {
        "maxwidth": 400,
        "photoreference": photo_reference,
        "key": GOOGLE_MAPS_API_KEY, # repinted, secure now
    }
    return f"{GOOGLE_MAPS_API_URL_PHOTOS}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

def display_place_info(place, details):
    """Display information about a place, including photos, reviews, and ratings."""
    name = place.get("name", "Unknown Place")
    address = details.get("formatted_address", "Address not available")
    url = details.get("url", "#")  # Default to "#" if no URL is available

    # Display place name and hyperlink the address to Google Maps URL
    st.subheader(name)
    st.markdown(f"**[📍 {address}]({url})**")  # Hyperlinked address

    # Display photo
    photo_ref = details.get("photos", [{}])[0].get("photo_reference")
    photo_url = get_place_photos(photo_ref)
    if photo_url:
        st.image(photo_url, caption=name, use_container_width=True)
    else:
        st.write("No photos available.")

    # Display overall rating
    rating = details.get("rating", "No rating available")
    user_ratings = details.get("user_ratings_total", 0)
    st.write(f"Rating: {rating} ({user_ratings} reviews)")

    # Display reviews
    reviews = details.get("reviews", [])
    with st.expander("Reviews", expanded=False):
        if reviews:
            for review in reviews:
                author = review.get("author_name", "Anonymous")
                text = review.get("text", "No review text provided.")
                st.write(f"**{author}**: {text}")
        else:
            st.write("No reviews available.")

def render_map(location, places):
    """Render a map with markers for each sensory-friendly place."""
    m = folium.Map(location=location, zoom_start=15)
    for place in places:
        name = place.get("name", "Unknown Place")
        address = place.get("vicinity", "Address not available")
        lat = place["geometry"]["location"]["lat"]
        lng = place["geometry"]["location"]["lng"]
        popup_content = f"<b>{name}</b><br>{address}"

        folium.Marker(
            [lat, lng],
            popup=popup_content,
            icon=Icon(icon="cutlery", prefix="fa", color="green"),
        ).add_to(m)
    st_folium(m, width=800, height=500)

def send_email(name, sender_email, message):
    """Send the email from the contact page."""
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SUBJECT = "Sensory Heaven Contact Form Submission"
    
    # Fetch credentials securely (use environment variables in production)
    EMAIL_USERNAME = os.environ['EMAIL_USERNAME'] # [should match yaml def]
    EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD'] # [should match yaml def]

    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        raise ValueError("Email credentials not found. Ensure they are set properly.")

    # Email content
    recipient_email = EMAIL_USERNAME  
    body = f"""
    <html>
        <body>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email (sender):</strong> {sender_email}</p>
            <p><strong>Message:</strong> {message}</p>
        </body>
    </html>
    """

    # Compose email
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = SUBJECT
    msg.attach(MIMEText(body, 'html'))

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(sender_email, recipient_email, msg.as_string())

# Main function for Contact page
def contact_form():
    # Input fields
    user_name = st.text_input("Your Name")
    user_email = st.text_input("Your Email")
    user_message = st.text_area("Your Message")

    if st.button("Submit"):
        # Validate inputs
        if not user_name or not user_email or not user_message:
            st.error("All fields are required!")
        elif "@" not in user_email:  # Basic email validation
            st.error("Please enter a valid email address!")
        else:
            # Send the email
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
        location_input = st.text_input("Enter a location:", "Stockholm")
        radius_input = st.slider("Set the radius (meters):", 100, 5000, 1000, 100)

        if location_input:
            location = geocode_location(location_input)
            if location:
                st.write(f"Coordinates for {location_input}: {location}")
                places = get_sensory_friendly_places(location, radius=radius_input)
                if places:
                    for place in places:
                        details = get_place_details(place.get("place_id"))
                        display_place_info(place, details)
                    render_map(location, places)
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
        If a business has these _keywords_ in either their map profile or reviews then the establishment will be flagged as sensory friendly.
        - ambiance
        - autism
        - booth
        - cozy
        - dim
        - low-lighting
        - peaceful
        - quiet
        """)

    elif page == "Contact":
        st.title("Sensory Heaven - Contact")
        contact_form()
    elif page == "Donate":
        st.title("Sensory Heaven - Donate")
        st.write("Venmo link: https://venmo.com/code?user_id=2471244549062656744")
        st.image('venmo_qr.jpg', caption='Venmo QR code')
        
if __name__ == "__main__":
    main()
