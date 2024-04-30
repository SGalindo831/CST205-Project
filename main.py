from flask import Flask, render_template, request
import requests
from PIL import Image
import io
import base64
import cv2
import numpy as np
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# Weather API endpoint
API_KEY = "4b0777b8f1654b8af05312207e81d722"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# Unsplash API endpoint
FORECAST_API_URL = "http://api.openweathermap.org/data/2.5/forecast"
UNSPLASH_API_KEY = "pvqedyI7MPnBOZJTuooFM4rsHjp3RG98YttAKZrRYYA"
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# List of cities for random selection
CITIES = ["New York", "London", "Tokyo", "Sydney", "Paris", "Berlin", "Moscow", "Los Angeles", "Rio de Janeiro", "Cape Town"]

"""Applies a color map based on temperature."""
def apply_temperature_based_filter(image, temp):

    image_cv = np.array(image)

    image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)

    if temp >= 78:
        color_map = cv2.COLORMAP_HOT
    elif temp >= 50:
        color_map = cv2.COLORMAP_COOL
    elif temp >= 32:
        color_map = cv2.COLORMAP_WINTER
    else:
        color_map = cv2.COLORMAP_BONE

    filtered_image = cv2.applyColorMap(image_cv, color_map)
    filtered_image = cv2.cvtColor(filtered_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(filtered_image)

"""Encodes an image to base64 format."""
def encode_image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

"""Converts a Unix timestamp to a local time, taking into account the timezone offset."""
def convert_to_local_time(unix_time, timezone_offset):
    utc_time = datetime.utcfromtimestamp(unix_time)
    local_time = utc_time + timedelta(seconds=timezone_offset)
    return local_time.strftime("%Y-%m-%d %H:%M:%S")

"""Handles requests to the home page."""
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'lucky' in request.form:
            city_name = random.choice(CITIES)
        else:
            city_name = request.form['city']

        # Fetch weather data from OpenWeatherAPI
        params = {
            "q": city_name,
            "appid": API_KEY,
            "units": "imperial",
        }
        response = requests.get(WEATHER_API_URL, params=params)
        weather_data = response.json()

        if response.status_code != 200 or 'main' not in weather_data:
            return render_template('index.html', error="City not found or API error occurred.")

        temperature = weather_data['main']['temp']
        weather_description = weather_data['weather'][0]['description']
        weather_icon = weather_data['weather'][0]['icon']
        unix_time = weather_data['dt']
        timezone_offset = weather_data['timezone']

        # Convert Unix timestamp to local time
        local_time = convert_to_local_time(unix_time, timezone_offset)

        # Fetch an image from Unsplash
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_API_KEY}"
        }
        unsplash_params = {
            "query": city_name,
            "per_page": 1,
        }
        unsplash_response = requests.get(UNSPLASH_API_URL, headers=headers, params=unsplash_params)
        unsplash_data = unsplash_response.json()

        if unsplash_response.status_code != 200 or not unsplash_data['results']:
            return render_template('index.html', error="No image found for the city.")

        image_url = unsplash_data['results'][0]['urls']['regular']

        # Load the image as a PIL object directly from the URL
        image_response = requests.get(image_url, stream=True)
        image = Image.open(image_response.raw)

        # Apply a color map filter based on temperature
        filtered_image = apply_temperature_based_filter(image, temperature)

        # Encode it to a base64 string for rendering
        encoded_image = encode_image_to_base64(filtered_image)

        # Fetch forecast data
        forecast_response = requests.get(FORECAST_API_URL, params=params)
        forecast_data = forecast_response.json()

        forecast_for_next_day = []

        if forecast_data.get("list"):
            forecast_for_next_day = [
                forecast for forecast in forecast_data["list"]
                if "dt_txt" in forecast and "12:00:00" in forecast["dt_txt"]
            ]

        return render_template(
            'index.html', city_name=city_name, temperature=temperature,
            weather_description=weather_description, weather_icon=weather_icon,
            local_time=local_time, forecast_for_next_day=forecast_for_next_day, image=encoded_image
        )

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)