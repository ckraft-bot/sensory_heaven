# Foursquare API Base URL
FOURSQUARE_API_BASE_URL = "https://api.foursquare.com/v3/places"

# Function to construct Foursquare API URLs
def get_foursquare_url(endpoint, params=""):
   return f"{FOURSQUARE_API_BASE_URL}/{endpoint}{params}"

# Foursquare category IDs: https://docs.foursquare.com/data-products/docs/categories
FOURSQUARE_CATEGORIES = {
      "Restaurant": "4d4b7105d754a06374d81259",  # Dining and Drinking > Restaurant
      "Cafe": "4bf58dd8d48988d16d941735",  # Dining and Drinking > Cafe, Coffee, and Tea House > Café
      "Retail": "4d4b7105d754a06378d81259",  # Retail
      "Sports & Rec": "4f4528bc4b90abdf24c9de85",  # Sports and Recreation
      "Park": "4bf58dd8d48988d163941735",  # Landmarks and Outdoors > Park
      "Library": "4bf58dd8d48988d12f941735",  # Community and Government > Library
      "Movie Theater": "4bf58dd8d48988d17f941735",  # Arts and Entertainment > Movie Theater
      "Museum": "4bf58dd8d48988d181941735",  # Arts and Entertainment > Museum
      "Hospital": "4bf58dd8d48988d196941735",  # Health and Medicine > Hospital
      "Places of Worship": "4bf58dd8d48988d131941735",  # Community and Government > Spiritual Center
      "Zoo": "4bf58dd8d48988d17b941735",  # Arts and Entertainment > Zoo
      "Aquarium": "4fceea171983d5d06c3e9823",  # Arts and Entertainment > Aquarium
      "Airport": "4bf58dd8d48988d1ed931735"  # Travel and Transportation > Transport Hub > Airport
   }

#-------------------------------------------------- Google --------------------------------------------------#
GOOGLE_MAPS_API_BASE_URL = "https://maps.googleapis.com/maps/api"
GOOGLE_MAPS_API_PLACES = f"{GOOGLE_MAPS_API_BASE_URL}/geocode/json"
GOOGLE_MAPS_API_PLACES_DETAILS = f"{GOOGLE_MAPS_API_BASE_URL}/place/details/json" 
GOOGLE_MAPS_API_NEARBY = f"{GOOGLE_MAPS_API_BASE_URL}/place/nearbysearch/json"
GOOGLE_MAPS_API_URL_PHOTOS = f"{GOOGLE_MAPS_API_BASE_URL}/place/photo"  

# Google categories: https://developers.google.com/maps/documentation/places/web-service/supported_types#table1
GOOGLE_PLACE_TYPES = [
      "accounting",
      "airport",
      "amusement_park",
      "aquarium",
      "art_gallery",
      "atm",
      "bakery",
      "bank",
      "bar",
      "beauty_salon",
      "bicycle_store",
      "book_store",
      "bowling_alley",
      "bus_station",
      "cafe",
      "campground",
      "car_dealer",
      "car_rental",
      "car_repair",
      "car_wash",
      "casino",
      "cemetery",
      "church",
      "city_hall",
      "clothing_store",
      "convenience_store",
      "courthouse",
      "dentist",
      "department_store",
      "doctor",
      "drugstore",
      "electrician",
      "electronics_store",
      "embassy",
      "fire_station",
      "florist",
      "funeral_home",
      "furniture_store",
      "gas_station",
      "gym",
      "hair_care",
      "hardware_store",
      "hindu_temple",
      "home_goods_store",
      "hospital",
      "insurance_agency",
      "jewelry_store",
      "laundry",
      "lawyer",
      "library",
      "light_rail_station",
      "liquor_store",
      "local_government_office",
      "locksmith",
      "lodging",
      "meal_delivery",
      "meal_takeaway",
      "mosque",
      "movie_rental",
      "movie_theater",
      "moving_company",
      "museum",
      "night_club",
      "painter",
      "park",
      "parking",
      "pet_store",
      "pharmacy",
      "physiotherapist",
      "plumber",
      "police",
      "post_office",
      "real_estate_agency",
      "restaurant",
      "roofing_contractor",
      "rv_park",
      "school",
      "secondary_school",
      "shoe_store",
      "shopping_mall",
      "spa",
      "stadium",
      "storage",
      "store",
      "subway_station",
      "supermarket",
      "synagogue",
      "taxi_stand",
      "tourist_attraction",
      "train_station",
      "transit_station",
      "travel_agency",
      "university",
      "veterinary_care",
      "zoo"
   ]

