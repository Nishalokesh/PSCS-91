from flask import Flask, jsonify
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend to access API

# Database credentials
DB_CONFIG = {
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": "Nisha@84"
}

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/api/weather", methods=["GET"])
def get_weather_with_risk():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            w.city, w.temperature, w.humidity, w.pressure, 
            w.wind_speed, w.cloudiness, r.risk_level, w.timestamp, r.prediction_score
        FROM weather w
        LEFT JOIN risk_predictions r ON w.city = r.city
    """)
    
    rows = cur.fetchall()
    conn.close()

    data = [
        {
            "city": row[0],
            "temperature": row[1],
            "humidity": row[2],
            "pressure": row[3],
            "wind_speed": row[4],
            "cloudiness": row[5],
            "risk_level": row[6] or "Unknown",
            "timestamp": row[7].isoformat() if row[7] else None,
            "prediction_score": row[8],
        }
        for row in rows
    ]
    return jsonify(data)


@app.route("/api/risk", methods=["GET"])
def get_risk_data():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT city, timestamp, risk_level, prediction_score FROM risk_predictions")
    rows = cursor.fetchall()
    conn.close()

    data = [{
            "city": r[0],
            "timestamp": r[1],
            "risk_level":r[2],
            "prediction_score":r[3]
        } for r in rows
    ]
    return jsonify(data)


@app.route("/api/stats", methods=["GET"])
def get_risk_stats():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT risk_level, COUNT(*) 
        FROM risk_predictions 
        GROUP BY risk_level
    """)
    results = cur.fetchall()
    conn.close()

    # Normalize keys for frontend
    stats = {
        "high_risk": 0,
        "low_risk": 0
    }

    for level, count in results:
        if level == "High Risk":
            stats["high_risk"] = count
        elif level == "Low Risk":
            stats["low_risk"] = count

    return jsonify(stats)



if __name__ == "__main__":
    app.run(debug=True)
