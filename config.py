#-------------------------------------------------- Foursquare --------------------------------------------------#
FOURSQUARE_API_URL_SEARCH = "https://api.foursquare.com/v3/places/search"
FOURSQUARE_API_URL_PHOTOS = "https://api.foursquare.com/v3/places/{fsq_id}/photos"
FOURSQUARE_API_URL_REVIEWS = "https://api.foursquare.com/v3/places/{fsq_id}/tips"
FOURSQUARE_API_KEY = "fsq3COFPhHd+kdomv9CJza3DLGw60xtpEn5S1VWauImxDZE="
# Foursquare category IDs: https://docs.foursquare.com/data-products/docs/categories
FOURSQUARE_CATEGORIES = {#"Food and Beverage":"56aa371be4b08b9a8d573550", # Business and Professional Services > Food and Beverage Service
            #"Dinning and Drinking":"63be6904847c3692a84b9bb5", # Dinning and Drinking
            "Restaurant": "4d4b7105d754a06374d81259" # Dining and Drinking > Restaurant

               } 

#-------------------------------------------------- Google --------------------------------------------------#
GOOGLE_MAPS_API_BASE_URL = "https://maps.googleapis.com/maps/api"
GOOGLE_MAPS_API_PLACES = f"{GOOGLE_MAPS_API_BASE_URL}/geocode/json"
GOOGLE_MAPS_API_PLACES_DETAILS = f"{GOOGLE_MAPS_API_BASE_URL}/place/details/json" 
GOOGLE_MAPS_API_NEARBY = f"{GOOGLE_MAPS_API_BASE_URL}/place/nearbysearch/json"
GOOGLE_MAPS_API_URL_PHOTOS = f"{GOOGLE_MAPS_API_BASE_URL}/place/photo"  

# https://developers.google.com/maps/documentation/places/web-service/supported_types#table1
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