"""
app.py
-------
Flask backend for the CO2 Emissions Chatbot hackathon project.

Endpoints:
  GET  /                       -> serves frontend/index.html
  GET  /api/health             -> health check
  POST /api/chat               -> {"message": "..."}  -> chatbot reply
  GET  /api/stats              -> overall dataset stats
  GET  /api/stats/<year>       -> stats for a specific year
  GET  /api/forecast?days=30   -> forecast next N days from today
  GET  /api/forecast?date=YYYY-MM-DD -> forecast for a specific date
  GET  /api/trend              -> yearly average trend
  GET  /api/seasonality        -> monthly average seasonality
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import data_utils
import predictor
import chatbot

app = Flask(__name__)
CORS(app)

# Absolute path to frontend folder
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)


@app.route("/", methods=["GET"])
def serve_home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}
    message = body.get("message", "")

    if not message.strip():
        return jsonify({"error": "message field is required"}), 400

    result = chatbot.handle_message(message)
    return jsonify(result)


@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(data_utils.overall_stats())


@app.route("/api/stats/<int:year>", methods=["GET"])
def stats_year(year):
    result = data_utils.year_stats(year)

    if result is None:
        return jsonify({"error": f"No data for year {year}"}), 404

    return jsonify(result)


@app.route("/api/forecast", methods=["GET"])
def forecast():
    date_param = request.args.get("date")
    days_param = request.args.get("days", default=30, type=int)

    if date_param:
        result = predictor.forecast_single_date(date_param)
        return jsonify(result)

    from datetime import datetime, timedelta

    start = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    result = predictor.forecast(start, days=days_param)

    return jsonify({
        "start_date": start,
        "days": days_param,
        "forecast": result
    })


@app.route("/api/trend", methods=["GET"])
def trend():
    return jsonify(data_utils.yearly_trend())


@app.route("/api/seasonality", methods=["GET"])
def seasonality():
    return jsonify(data_utils.monthly_seasonality())


@app.route("/<path:path>", methods=["GET"])
def serve_frontend_files(path):
    """
    Serves files from the frontend folder.
    If the requested file does not exist, fallback to index.html.
    """
    requested_file = os.path.join(FRONTEND_DIR, path)

    if os.path.exists(requested_file):
        return send_from_directory(FRONTEND_DIR, path)

    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)