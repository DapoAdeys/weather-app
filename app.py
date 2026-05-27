from flask import Flask, request, jsonify
import requests
import json
import csv
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

if not API_KEY:
    raise EnvironmentError("WEATHER_API_KEY is not set in your .env file")


def fetch_weather(city):
    try:
        response = requests.get(
            BASE_URL,
            params={"q": city, "appid": API_KEY, "units": "metric"},
            timeout=5
        )
        data = response.json()
    except requests.exceptions.RequestException:
        return None, "Could not reach weather service"

    if str(data.get("cod")) != "200":
        return None, data.get("message", "City not found")

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": round(data["main"]["temp"], 1),
        "feels_like": round(data["main"]["feels_like"], 1),
        "temp_min": round(data["main"]["temp_min"], 1),
        "temp_max": round(data["main"]["temp_max"], 1),
        "humidity": data["main"]["humidity"],
        "weather": data["weather"][0]["main"],
        "wind_speed": data["wind"]["speed"]
    }, None


def save_data(weather_info):
    try:
        with open("weather.json", "w") as f:
            json.dump(weather_info, f, indent=4)

        with open("weather.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=weather_info.keys())
            writer.writeheader()
            writer.writerow(weather_info)
    except OSError as e:
        print(f"Warning: could not save files — {e}")


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/weather")
def weather():
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({"error": "City name is required"}), 400

    if len(city) > 100:
        return jsonify({"error": "City name is too long"}), 400

    weather_info, error = fetch_weather(city)

    if error:
        return jsonify({"error": error}), 404

    save_data(weather_info)
    return jsonify(weather_info)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True)