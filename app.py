from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
from datetime import datetime
import csv

app = Flask(__name__)
CORS(app)

DB_NAME = "data.db"

# -------------------------
# INIT DB
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            mobile TEXT PRIMARY KEY,
            name TEXT,
            total_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT,
            count INTEGER,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# SUBMIT
# -------------------------
@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()

    name = data.get("name")
    mobile = data.get("mobile")
    count = int(data.get("count"))

    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT total_count FROM users WHERE mobile = ?", (mobile,))
    user = cursor.fetchone()

    if user:
        new_total = user[0] + count
        cursor.execute(
            "UPDATE users SET total_count = ?, name = ? WHERE mobile = ?",
            (new_total, name, mobile)
        )
    else:
        new_total = count
        cursor.execute(
            "INSERT INTO users (mobile, name, total_count) VALUES (?, ?, ?)",
            (mobile, name, new_total)
        )

    cursor.execute(
        "INSERT INTO entries (mobile, count, date) VALUES (?, ?, ?)",
        (mobile, count, today)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Success"})

# -------------------------
# STATS
# -------------------------
@app.route('/stats')
def stats():
    mobile = request.args.get("mobile")
    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(total_count) FROM users")
    total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(count) FROM entries WHERE date = ?", (today,))
    today_count = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM users")
    unique_users = cursor.fetchone()[0]

    individual = 0
    if mobile:
        cursor.execute("SELECT total_count FROM users WHERE mobile = ?", (mobile,))
        result = cursor.fetchone()
        if result:
            individual = result[0]

    conn.close()

    return jsonify({
        "totalCount": total,
        "todayCount": today_count,
        "uniqueUsers": unique_users,
        "individualCount": individual
    })

# -------------------------
# PAGES
# -------------------------
@app.route('/')
def home():
    return send_file("index.html")

@app.route('/dashboard')
def dashboard():
    return send_file("dashboard.html")

# -------------------------
# DOWNLOAD CSV
# -------------------------
@app.route('/download', methods=['GET'])
def download():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT mobile, name, total_count FROM users")
    users = cursor.fetchall()

    file_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Mobile", "Name", "Total Count"])

        for user in users:
            writer.writerow(user)

    conn.close()

    return send_file(file_name, as_attachment=True)

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)