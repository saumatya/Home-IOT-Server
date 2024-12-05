# main_api.py
from flask import Flask, jsonify,request

from fetch import (
    fetch_daily_avg_data,
    fetch_hourly_avg_data,
    fetch_latest_sensor_data,
    fetch_specific_hour_avg_data,
    fetch_weekly_avg_data,

)

app = Flask(__name__)


# Endpoint to get the latest temperature
@app.route("/latest-temperature", methods=["GET"])
def latest_temperature():
    latest_data = fetch_latest_sensor_data()
    if latest_data:
        temperature = round(float(latest_data["temperature"]), 1)
        return jsonify({"temperature": temperature})
    else:
        return jsonify({"error": "No sensor data available"}), 404


# Endpoint to get the latest humidity
@app.route("/latest-humidity", methods=["GET"])
def latest_humidity():
    latest_data = fetch_latest_sensor_data()
    if latest_data:
        humidity = round(float(latest_data["humidity"]), 1)
        return jsonify({"humidity": humidity})
    else:
        return jsonify({"error": "No sensor data available"}), 404


@app.route("/hourly-average/<int:hour>", methods=["GET"])
def hourly_average(hour):
    if hour < 0 or hour > 23:
        return jsonify({"error": "Hour must be between 0 and 23"}), 400

    hourly_avg_data = fetch_specific_hour_avg_data(hour)
    if hourly_avg_data:
        # Round temperature and humidity
        hourly_avg_data["temperature"] = round(hourly_avg_data["temperature"], 1)
        hourly_avg_data["humidity"] = round(hourly_avg_data["humidity"], 1)
        return jsonify(hourly_avg_data)
    else:
        return jsonify({"error": f"No data available for hour {hour}"}), 404


@app.route("/hourly-averages", methods=["GET"])
def hourly_averages():
    hourly_avg_data = fetch_hourly_avg_data()
    if hourly_avg_data:
        # Round all hourly data
        for hour_data in hourly_avg_data:
            hour_data["temperature"] = round(hour_data["temperature"], 1)
            hour_data["humidity"] = round(hour_data["humidity"], 1)
        return jsonify(hourly_avg_data)
    else:
        return jsonify({"error": "No hourly data available"}), 404


# Endpoint to get daily average temperature and humidity
@app.route("/daily-averages", methods=["GET"])
def daily_averages():
    daily_avg_data = fetch_daily_avg_data()
    if daily_avg_data:
        return jsonify(
            {
                "average_temperature": round(daily_avg_data["temperature"], 1),
                "average_humidity": round(daily_avg_data["humidity"], 1),
            }
        )
    else:
        return jsonify({"error": "No daily data available"}), 404


# Endpoint to get weekly average temperature and humidity
@app.route("/weekly-averages", methods=["GET"])
def weekly_averages():
    weekly_avg_data = fetch_weekly_avg_data()
    if weekly_avg_data:
        return jsonify(
            {
                "average_temperature": round(weekly_avg_data["temperature"], 1),
                "average_humidity": round(weekly_avg_data["humidity"], 1),
            }
        )
    else:
        return jsonify({"error": "No weekly data available"}), 404


# In-memory storage for thresholds (can be replaced with a database or other persistent storage)
thresholds = {
    "temperature": {"min": None, "max": None},
    "humidity": {"min": None, "max": None},
}


# POST endpoint to set thresholds for temperature and humidity
@app.route("/set-thresholds", methods=["POST"])
def set_thresholds():
    try:
        data = request.json  # Get JSON payload
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate and set temperature thresholds
        if "temperature" in data:
            if "min" in data["temperature"]:
                thresholds["temperature"]["min"] = data["temperature"]["min"]
            if "max" in data["temperature"]:
                thresholds["temperature"]["max"] = data["temperature"]["max"]

        # Validate and set humidity thresholds
        if "humidity" in data:
            if "min" in data["humidity"]:
                thresholds["humidity"]["min"] = data["humidity"]["min"]
            if "max" in data["humidity"]:
                thresholds["humidity"]["max"] = data["humidity"]["max"]

        return jsonify(
            {"message": "Thresholds updated successfully", "thresholds": thresholds}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET endpoint to retrieve current thresholds
@app.route("/get-thresholds", methods=["GET"])
def get_thresholds():
    return jsonify(thresholds)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
