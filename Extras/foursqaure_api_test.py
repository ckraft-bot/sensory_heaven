import requests
FOURSQUARE_API_KEY = "fsq3WjxLfw81YTLiIkIONlz1sw3NwOezY8aYySRxbjl6OXc="

single_test = "https://api.foursquare.com/v3/places/search?ll=35.0457219%2C-85.3094883&radius=8045&limit=50&categories=4d4b7105d754a06374d81259"
headers = {
    "accept": "application/json",
    "Authorization": FOURSQUARE_API_KEY
}

response = requests.get(single_test, headers=headers)
print("Single Test Status Code:", response.status_code)
print("Response Text:", response.text)

#----------------------- places
FOURSQUARE_API_KEY = ""

url = "https://api.foursquare.com/v3/places/search?ll=35.0457219%2C-85.3094883&radius=4827&limit=10"
headers = {
    "accept": "application/json",
    "Authorization": FOURSQUARE_API_KEY
}

response = requests.get(url, headers=headers)
print("Places Status Code:", response.status_code)
# print("Response Text:", response.text)

#----------------------- details

url = "https://api.foursquare.com/v3/places/4b993c6ff964a520536c35e3"
headers = {
    "accept": "application/json",
    "Authorization": FOURSQUARE_API_KEY
}

response = requests.get(url, headers=headers)
print("Details Status Code:", response.status_code)
# print(response.text)

#----------------------- photos
url = "https://api.foursquare.com/v3/places/4bace4ebf964a520b7163be3/photos?limit=1&sort=NEWEST&classifications=indoor"

headers = {
    "accept": "application/json",
    "Authorization": FOURSQUARE_API_KEY
}

response = requests.get(url, headers=headers)

print("Photo Status Code:", response.status_code)
# print(response.text)

#----------------------- reviews
import requests

url = "https://api.foursquare.com/v3/places/4bace4ebf964a520b7163be3/tips?limit=5&fields=text&sort=NEWEST"

headers = {
    "accept": "application/json",
    "Authorization": "fsq3WjxLfw81YTLiIkIONlz1sw3NwOezY8aYySRxbjl6OXc="
}

response = requests.get(url, headers=headers)
print("Reviews Status Code:", response.status_code)
# print(response.text)