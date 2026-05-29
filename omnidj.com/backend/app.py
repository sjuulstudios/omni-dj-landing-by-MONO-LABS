"""
Omni DJ website backend — Flask 3.x

Endpoints:
- POST /api/contact       — role-routed contact form
- POST /api/beta-signup   — email signup with SQLite persistence

Run dev:
    cd backend
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # then fill SMTP credentials
    python app.py          # serves on http://127.0.0.1:5556

Production: serve via gunicorn behind nginx on api.omnidj.com.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from routes.contact import contact_bp
from routes.beta import beta_bp

load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "data" / "omnidj.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*").split(",")}})


def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS beta_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            user_agent TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT,
            company TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    con.commit()
    con.close()


init_db()

# share DB path with blueprints
app.config["DB_PATH"] = str(DB_PATH)

app.register_blueprint(contact_bp, url_prefix="/api")
app.register_blueprint(beta_bp, url_prefix="/api")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": datetime.now(timezone.utc).isoformat()})


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "not found"}), 404


@app.errorhandler(500)
def server_err(_e):
    return jsonify({"error": "internal"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5556"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
