# main_api.py
# import threading
from threading import Thread
from time import sleep

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

from fetch import (
    fetch_daily_avg_data,
    fetch_hourly_avg_data,
    fetch_latest_sensor_data,
    fetch_specific_hour_avg_data,
    fetch_thresholds_from_db,
    fetch_weekly_avg_data,
    set_threshold,
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Add cors_allowed_origins if needed


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


@app.route("/set-thresholds", methods=["POST"])
def set_thresholds():
    try:
        data = request.json  # Get JSON payload
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Set temperature thresholds
        if "temperature" in data:
            if "min" in data["temperature"]:
                min_temp = data["temperature"]["min"]
                max_temp = data["temperature"]["max"]
                response = set_threshold("temperature", min_temp, max_temp)

        # Set humidity thresholds
        if "humidity" in data:
            if "min" in data["humidity"]:
                min_humidity = data["humidity"]["min"]
                max_humidity = data["humidity"]["max"]
                response = set_threshold("humidity", min_humidity, max_humidity)

        return jsonify(
            {"message": "Thresholds updated successfully", "response": response}
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-thresholds", methods=["GET"])
def get_thresholds():  # This is the route handler
    try:
        thresholds = fetch_thresholds_from_db()
        if "error" in thresholds:
            return jsonify({"error": thresholds["error"]}), 500

        return jsonify({"status": "success", "data": thresholds})
    except Exception as e:
        print(f"Error in get_thresholds route: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def monitor_sensor_data():
    while True:
        try:
            # Fetch the latest sensor data
            latest_data = fetch_latest_sensor_data()

            if not latest_data:
                print("Warning: No sensor data received")
                sleep(5)
                continue

            try:
                temperature = float(latest_data["temperature"])
                humidity = float(latest_data["humidity"])
            except (KeyError, ValueError) as e:
                print(f"Error parsing sensor data: {e}")
                print(f"Received data: {latest_data}")
                sleep(5)
                continue

            # Fetch the current threshold values from DynamoDB
            thresholds = fetch_thresholds_from_db()

            if thresholds is None:
                print("Error: get_thresholds() returned None")
                sleep(5)
                continue

            if not isinstance(thresholds, dict):
                print(f"Error: thresholds is not a dictionary. Got {type(thresholds)}")
                sleep(5)
                continue

            if "temperature" not in thresholds or "humidity" not in thresholds:
                print("Error: Missing required threshold keys")
                print(f"Available keys: {thresholds.keys()}")
                sleep(5)
                continue

            # Check temperature thresholds
            temp_threshold = thresholds["temperature"]
            if (
                temp_threshold["min"] is not None
                and temperature < temp_threshold["min"]
            ):
                try:
                    socketio.emit(
                        "alert",
                        {
                            "type": "temperature",
                            "value": temperature,
                            "message": f"Temperature too low! Current: {temperature}°C, Minimum: {temp_threshold['min']}°C",
                        },
                    )
                except Exception as e:
                    print(f"Error sending temperature low alert: {e}")

            if (
                temp_threshold["max"] is not None
                and temperature > temp_threshold["max"]
            ):
                try:
                    socketio.emit(
                        "alert",
                        {
                            "type": "temperature",
                            "value": temperature,
                            "message": f"Temperature too high! Current: {temperature}°C, Maximum: {temp_threshold['max']}°C",
                        },
                    )
                except Exception as e:
                    print(f"Error sending temperature high alert: {e}")

            # Check humidity thresholds
            humid_threshold = thresholds["humidity"]
            if humid_threshold["min"] is not None and humidity < humid_threshold["min"]:
                try:
                    socketio.emit(
                        "alert",
                        {
                            "type": "humidity",
                            "value": humidity,
                            "message": f"Humidity too low! Current: {humidity}%, Minimum: {humid_threshold['min']}%",
                        },
                    )
                except Exception as e:
                    print(f"Error sending humidity low alert: {e}")

            if humid_threshold["max"] is not None and humidity > humid_threshold["max"]:
                try:
                    socketio.emit(
                        "alert",
                        {
                            "type": "humidity",
                            "value": humidity,
                            "message": f"Humidity too high! Current: {humidity}%, Maximum: {humid_threshold['max']}%",
                        },
                    )
                except Exception as e:
                    print(f"Error sending humidity high alert: {e}")

            # Log successful monitoring iteration
            print(f"Monitored - Temp: {temperature}°C, Humidity: {humidity}%")

        except Exception as e:
            print(f"Unexpected error in monitor_sensor_data: {e}")

        sleep(5)  # Monitor every 5 seconds


@socketio.on("connect")
def handle_connect():
    print("Client connected.")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected.")


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=False)
    socketio.start_background_task(monitor_sensor_data)
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
