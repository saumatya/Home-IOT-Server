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