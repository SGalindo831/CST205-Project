from flask import Flask, render_template, request
import requests
import os
from PIL import Image, ImageEnhance

app = Flask(__name__)

# Weather API endpoint
API_KEY = "4b0777b8f1654b8af05312207e81d722" 
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# City information
cities = {
    "Los Angeles": {"id": 5368361, "image": "los_angeles.jpg"},
    "Anchorage": {"id": 5879400, "image": "anchorage.jpg"},
    "New York": {"id" : 5128581, "image": "new_york.jpg"}
}


def get_hue_value(temp):
    if temp >= 78:
        hue_value = 1.0  # Red
    elif temp >= 65:
        hue_value = 0.5  # Normal
    else:
        hue_value = 0.0  # Blue
    return hue_value


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city_name = request.form['city']
        city_id = cities[city_name]['id']

        # Fetch weather data from API
        params = {
            "id": city_id,
            "appid": API_KEY,
            "units": "imperial"
        }
        response = requests.get(WEATHER_API_URL, params=params)
        weather_data = response.json()

        # Get temperature and modify image hue
        temperature = weather_data['main']['temp']
        hue_value = get_hue_value(temperature)
        image_path = os.path.join('static', cities[city_name]['image'])
        modify_image_hue(image_path, hue_value)

        return render_template('index.html', cities=cities, selected_city=city_name, temperature=temperature)

    return render_template('index.html', cities=cities)

def modify_image_hue(image_path, hue_value):
    image = Image.open(image_path)
    enhancer = ImageEnhance.Color(image)
    modified_image = enhancer.enhance(hue_value)
    modified_image.save(image_path)
    print("Hue Value:", hue_value)
    print("Image modified and saved successfully.") 


if __name__ == '__main__':
    app.run(debug=True)
