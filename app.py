from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import cv2
import numpy as np
import base64
import sqlite3
from deepface import DeepFace
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "known_faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = "gizli_admin_sifre"

def save_image_from_base64(base64_data, name):
    img_bytes = base64.b64decode(base64_data.split(',')[1])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    filepath = os.path.join(UPLOAD_FOLDER, f"{name}.jpg")
    cv2.imwrite(filepath, img)
    return filepath

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    image_data = data["image"]
    name = data["name"]

    filepath = save_image_from_base64(image_data, name)

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT NOT NULL,
            register_date TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT INTO users (name, image_path, register_date) VALUES (?, ?, ?)",
                   (name, filepath, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"{name} başarıyla kaydedildi."})

@app.route("/verify_face", methods=["POST"])
def verify_face():
    data = request.json
    image_data = data["image"]

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_path = f"temp_{now}.jpg"
    img_bytes = base64.b64decode(image_data.split(",")[1])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    cv2.imwrite(temp_path, img)

    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith(".jpg"):
                result = DeepFace.verify(
                    img1_path=temp_path,
                    img2_path=os.path.join(UPLOAD_FOLDER, filename),
                    model_name="VGG-Face",
                    detector_backend="opencv",
                    enforce_detection=True
                )

                if result["verified"] and result["distance"] < 0.4:
                    os.remove(temp_path)
                    return jsonify({"success": True, "name": filename.split('.')[0]})

    except Exception as e:
        os.remove(temp_path)
        return jsonify({"success": False, "message": f"Hata: {str(e)}"})

    os.remove(temp_path)
    return jsonify({"success": False, "message": "Yüz eşleşmedi."})

@app.route("/dashboard")
def dashboard():
    name = request.args.get("name", "Ziyaretçi")
    return render_template("dashboard.html", name=name)

@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    password = request.form.get("password")
    if password == "1234":
        session["admin"] = True
        return redirect("/admin_panel")
    else:
        return "Hatalı şifre", 403

@app.route("/admin_panel")
def admin_panel():
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_panel.html", users=users)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT image_path FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        image_path = result[0]
        if os.path.exists(image_path):
            os.remove(image_path)
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    conn.close()
    return redirect("/admin_panel")

if __name__ == "__main__":
    app.run(debug=True)