import os
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the AWS Keys
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region = os.getenv("AWS_DEFAULT_REGION")

# Initialize DynamoDB with loaded credentials
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region,
)

# Access a specific table
table = dynamodb.Table("tbl_sensor_data_timestamp")

# Access the threshold table name
threshold_table = dynamodb.Table("tbl_threshold")


# Function to get threshold data from DynamoDB
def fetch_thresholds_from_db():  # Renamed the function that interacts with DynamoDB
    try:
        thresholds = {}
        for sensor_type in ["temperature", "humidity"]:
            try:
                response = threshold_table.get_item(
                    Key={
                        "thresholds": str(sensor_type),
                        "sensor_type": str(sensor_type),
                    }
                )
                if "Item" in response:
                    thresholds[sensor_type] = {
                        "min": float(
                            response["Item"].get("min_value", 0)
                        ),  # Convert to float
                        "max": float(
                            response["Item"].get("max_value", 0)
                        ),  # Convert to float
                    }
                else:
                    print(f"No threshold values found for {sensor_type}")
                    thresholds[sensor_type] = {"min": None, "max": None}
            except Exception as e:
                print(f"Error fetching {sensor_type} threshold: {str(e)}")
                thresholds[sensor_type] = {"min": None, "max": None}

        print("Thresholds fetched:", thresholds)
        return thresholds

    except Exception as e:
        print(f"Critical error in get_thresholds: {str(e)}")
        return {"error": str(e)}


# Function to set threshold data in DynamoDB
from decimal import Decimal


def set_threshold(sensor_type, min_value, max_value):
    try:
        response = threshold_table.put_item(
            Item={
                "thresholds": str(sensor_type),  # Primary key
                "sensor_type": str(sensor_type),  # Sort key
                "min_value": Decimal(str(min_value)),  # Convert to Decimal
                "max_value": Decimal(str(max_value)),  # Convert to Decimal
                "updated_at": str(datetime.now()),
            }
        )
        print(
            f"Successfully updated {sensor_type} thresholds: min={min_value}, max={max_value}"
        )
        return {
            "status": "success",
            "message": f"{sensor_type} thresholds updated successfully",
            "data": {
                "sensor_type": sensor_type,
                "min_value": str(min_value),  # Convert to string for JSON response
                "max_value": str(max_value),  # Convert to string for JSON response
            },
        }
    except Exception as e:
        error_msg = f"Error setting {sensor_type} thresholds: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": str(e)}


def fetch_specific_hour_avg_data(hour):
    sensor_data = fetch_sensor_data()
    if not sensor_data:
        return None

    # Filter data for the specified hour
    hour_data = []
    for data in sensor_data:
        timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
        if timestamp.hour == hour:
            hour_data.append(data)

    if hour_data:
        # Calculate averages
        avg_temp = sum(d["temperature"] for d in hour_data) / len(hour_data)
        avg_humidity = sum(d["humidity"] for d in hour_data) / len(hour_data)
        return {"hour": hour, "temperature": avg_temp, "humidity": avg_humidity}
    else:
        return None


def fetch_hourly_avg_data():
    sensor_data = fetch_sensor_data()
    if not sensor_data:
        return None

    # Group data by hour
    hourly_data = {}
    for data in sensor_data:
        # Extract hour from timestamp
        timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
        hour = timestamp.replace(minute=0, second=0, microsecond=0)

        # Add data to the corresponding hour
        if hour not in hourly_data:
            hourly_data[hour] = {"temperature": [], "humidity": []}
        hourly_data[hour]["temperature"].append(data["temperature"])
        hourly_data[hour]["humidity"].append(data["humidity"])

    # Calculate hourly averages
    hourly_avg = []
    for hour, values in hourly_data.items():
        avg_temp = sum(values["temperature"]) / len(values["temperature"])
        avg_humidity = sum(values["humidity"]) / len(values["humidity"])
        hourly_avg.append(
            {
                "hour": hour.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": avg_temp,
                "humidity": avg_humidity,
            }
        )

    # Sort by hour
    hourly_avg.sort(key=lambda x: x["hour"])
    return hourly_avg


# Fetch daily average temperature and humidity
def fetch_daily_avg_data():
    sensor_data = fetch_sensor_data()
    if not sensor_data:
        print("No sensor data fetched.")
        return None

    today = datetime.now(pytz.timezone("Europe/Helsinki")).date()
    daily_data = [
        data
        for data in sensor_data
        if datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S").date() == today
    ]

    if daily_data:
        avg_temp = sum(d["temperature"] for d in daily_data) / len(daily_data)
        avg_humidity = sum(d["humidity"] for d in daily_data) / len(daily_data)
        print(f"Daily averages - Temp: {avg_temp}, Humidity: {avg_humidity}")
        return {"temperature": avg_temp, "humidity": avg_humidity}
    else:
        print("No daily data available.")
        return None


# Fetch weekly average temperature and humidity
def fetch_weekly_avg_data():
    sensor_data = fetch_sensor_data()
    if not sensor_data:
        return None

    # Get the date one week ago in Helsinki timezone
    one_week_ago = datetime.now(pytz.timezone("Europe/Helsinki")).date() - timedelta(
        days=7
    )

    # Filter data for the past week
    weekly_data = [
        data
        for data in sensor_data
        if datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S").date()
        >= one_week_ago
    ]

    if weekly_data:
        # Calculate averages
        avg_temp = sum(d["temperature"] for d in weekly_data) / len(weekly_data)
        avg_humidity = sum(d["humidity"] for d in weekly_data) / len(weekly_data)
        return {"temperature": avg_temp, "humidity": avg_humidity}
    else:
        return None


# fetch_data.py
def fetch_latest_sensor_data():
    # Fetch all sensor data from the database (as a list of dictionaries)
    sensor_data = fetch_sensor_data()

    # If there's data, return the latest one
    if sensor_data:
        # Sort the data by timestamp in descending order and get the first item
        latest_data = sorted(sensor_data, key=lambda x: x["timestamp"], reverse=True)[0]
        return latest_data
    else:
        return None


# Function to fetch temperatures, humidities, and timestamps
def fetch_sensor_data():
    # Scan the table to retrieve all items
    response = table.scan()
    # Check if 'Items' exist in the response
    if "Items" in response:
        sensor_data = []
        for item in response["Items"]:
            if "sensorData" in item:
                temperature = item["sensorData"].get("temperature", 0)
                humidity = item["sensorData"].get("humidity", 0)
                timestamp = item["sensorData"].get("timestamp", None)

                # Provide default timestamp if None
                if not timestamp:
                    # Use current time as default
                    timestamp_dt = datetime.now(pytz.timezone("Europe/Helsinki"))
                    timestamp_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # Convert milliseconds to seconds and cast to float
                    timestamp_sec = float(Decimal(timestamp) / 1000)
                    # Create datetime object from timestamp (assumed to be in UTC)
                    timestamp_dt = datetime.fromtimestamp(timestamp_sec, tz=pytz.UTC)
                    # Convert UTC to Helsinki time zone
                    timestamp_dt = timestamp_dt.astimezone(
                        pytz.timezone("Europe/Helsinki")
                    )

                    # Format datetime to string (e.g., "2024-12-05 19:45:36")
                    timestamp_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

                # Add the data to the list
                sensor_data.append(
                    {
                        "temperature": float(temperature) if temperature else 0.0,
                        "humidity": float(humidity) if humidity else 0.0,
                        "timestamp": timestamp_str,
                    }
                )

        # Sort the data by timestamp in descending order
        sensor_data.sort(key=lambda x: x["timestamp"], reverse=True)

        return sensor_data
    else:
        print("No items found in the table.")
        return []


# Fetch and print the sensor data (temperature, humidity, timestamp)
sensor_data = fetch_sensor_data()

# Print each entry on a new line
for data in sensor_data:
    print(
        f"Temperature: {data['temperature']} °C, Humidity: {data['humidity']} %, Timestamp: {data['timestamp']}"
    )
