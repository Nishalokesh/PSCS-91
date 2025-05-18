import requests
import psycopg2
import psycopg2.extras
import numpy as np
import joblib
import time
from datetime import datetime, timezone,timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

# API & Database Credentials
OWM_API_KEY = "2c97b54a95dfe0a037bd517c8aec46b1"
GEONAMES_USERNAME = "nisha_l"

DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "Nisha@84"
COUNTRY_CODE = "IN"

IST = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time (UTC+5:30)

# Connect to PostgreSQL
def connect_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f" Database Connection Error: {e}")
        return None

# Get cities from API
def get_cities_in_country(country_code, max_total=1000, batch_size=100):
    all_cities = []
    start_row = 0

    while len(all_cities) < max_total:
        url = f"http://api.geonames.org/searchJSON?country={country_code}&featureClass=P&maxRows={batch_size}&startRow={start_row}&username={GEONAMES_USERNAME}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            cities_data = response.json()
            cities = [(city["name"], city["lat"], city["lng"]) for city in cities_data.get("geonames", [])]

            if not cities:
                break  # No more cities available

            all_cities.extend(cities)
            start_row += batch_size
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch cities: {e}")
            break

    print(f"Total cities fetched: {len(all_cities)}")
    return all_cities[:max_total]

# Fetch weather data
def fetch_weather_data(city, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Convert to IST datetime object (not string)
        utc_time = datetime.fromtimestamp(data["dt"], tz=timezone.utc)
        ist_time = utc_time.astimezone(IST)

        return {
            "timestamp": ist_time.strftime('%Y-%m-%d %H:%M:%S%z'),  # Keep as datetime object
            "city": city,
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "cloudiness": data["clouds"]["all"],
        }
    except requests.exceptions.RequestException as e:
        print(f" Failed to fetch weather data for {city}: {e}")
        return None

# Insert weather data into the database
def insert_weather_data(conn, weather_data_list):
    if not weather_data_list:
        return

    try:
        with conn.cursor() as cur:
            # Debug: Show what timestamps you're inserting
            print(f"Inserting {len(weather_data_list)} weather records:")
            for data in weather_data_list:
                print(f"City: {data['city']}, Time: {data['timestamp']}")

            psycopg2.extras.execute_values(cur, """
                INSERT INTO weather (timestamp, city, temperature, humidity, pressure, wind_speed, cloudiness)
                VALUES %s
                ON CONFLICT (city) DO UPDATE
                SET timestamp = EXCLUDED.timestamp,
                    temperature = EXCLUDED.temperature,
                    humidity = EXCLUDED.humidity,
                    pressure = EXCLUDED.pressure,
                    wind_speed = EXCLUDED.wind_speed,
                    cloudiness = EXCLUDED.cloudiness;
            """, [
                (data["timestamp"], data["city"], data["temperature"], data["humidity"], 
                 data["pressure"], data["wind_speed"], data["cloudiness"])
                for data in weather_data_list
            ])
            conn.commit()
            print(f" {len(weather_data_list)} records inserted/updated successfully!")
    except Exception as e:
        print(f" Error inserting/updating data: {e}")

# Load weather data for AI model training
def load_weather_data():
    conn = connect_db()
    if not conn:
        return None, None

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT temperature, humidity, pressure, wind_speed, cloudiness FROM weather")
            rows = cur.fetchall()

        conn.close()
        if not rows:
            print(" No data found for training!")
            return None, None

        data = np.array(rows)
        X = data[:, :-1]  # Features: temp, humidity, pressure, wind speed
        y = (data[:, -1] > 50).astype(int)  # Convert cloudiness into binary risk (threshold = 50)

        # Debugging: Print class distribution
        unique, counts = np.unique(y, return_counts=True)
        print(f"Label Distribution: {dict(zip(unique, counts))}")

        return X, y
    except Exception as e:
        print(f" Error loading data: {e}")
        return None, None

# Train and save Random Forest model
def train_rf_model():
    X, y = load_weather_data()
    if X is None or y is None:
        return
    
    # Scale Data
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    
    # Debugging: Print first few training labels
    print("First few labels:", y_train[:10])

    # Train Random Forest Model
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Save Model & Scaler
    joblib.dump(rf_model, "cloudburst_rf_model.pkl")
    joblib.dump(scaler, "scaler.pkl")

    print(" Random Forest model trained and saved successfully!")

# Predict cloudburst risk using RF model
def predict_rf_cloudburst_risk(weather_data):
    try:
        # Load Model & Scaler
        rf_model = joblib.load("cloudburst_rf_model.pkl")
        scaler = joblib.load("scaler.pkl")

        # Prepare Input Data
        input_data = np.array([[weather_data["temperature"], weather_data["humidity"], 
                                weather_data["pressure"], weather_data["wind_speed"]]])
        input_scaled = scaler.transform(input_data)

        # Make Prediction
        prediction = rf_model.predict(input_scaled)[0]
        risk_level = "High Risk" if prediction == 1 else "Low Risk"

        print(f"Predicted Cloudburst Risk: {risk_level} (Probability: {prediction})")
        return risk_level, prediction

    except Exception as e:
        print(f"Error predicting cloudburst risk: {e}")
        return None, None

# Update the database with predictions
def save_prediction_to_db(weather, risk_level, prediction_score):
    conn = connect_db()
    if not conn:
        print("Database connection failed")
        return

    try:
        with conn.cursor() as cur:
            print(f"DEBUG: Updating city={weather['city']}, timestamp={weather['timestamp']}, risk_level={risk_level}")

            prediction_score = float(prediction_score) 
            cur.execute("""
                  INSERT INTO risk_predictions (city, timestamp, risk_level, prediction_score)
                      VALUES (%s, %s, %s, %s)
                      ON CONFLICT (city) 
                      DO UPDATE SET 
                        timestamp = EXCLUDED.timestamp,  -- Ensure latest timestamp is updated
                       risk_level = EXCLUDED.risk_level,
                      prediction_score = EXCLUDED.prediction_score;
                """, (weather['city'], weather['timestamp'], risk_level, prediction_score))

            
            if cur.rowcount == 0:
                print(f"WARNING: No rows updated! Check if city='{weather['city']}' and timestamp='{weather['timestamp']}' exist in the database.")

            conn.commit()
            print("Prediction saved successfully!")
    except Exception as e:
        print(f"Error saving prediction: {e}")
    finally:
        conn.close()

# Process weather data and update risk levels
def process_weather_data_rf():
    conn = connect_db()
    if not conn:
        return

    cities = get_cities_in_country(COUNTRY_CODE,max_total=100)
    if not cities:
        print("No cities found. Exiting...")
        return
    
    weather_data_list = []
    for city, lat, lon in cities:
        weather = fetch_weather_data(city, lat, lon)
        if weather:
            weather_data_list.append(weather)

    insert_weather_data(conn, weather_data_list)

    for weather in weather_data_list:
        risk_level, prediction_score = predict_rf_cloudburst_risk(weather)
        if risk_level:
            save_prediction_to_db(weather, risk_level, prediction_score)
        time.sleep(1)

    conn.close()
    print("Weather data processing & prediction (RF) completed!")

# Run the script
if __name__ == "__main__":
    load_weather_data()  # Step 1: Collect & Store Weather Data
    train_rf_model()  # Step 2: Train RF Model
    process_weather_data_rf()  # Step 3: Cloudburst risk analysis using RF
