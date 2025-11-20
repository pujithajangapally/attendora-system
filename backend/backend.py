import cv2
import time
import numpy as np
import face_recognition
import pymysql
import pickle
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import threading
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "attendora"
CORS(app)

# ---------- STATUS CHECK ----------
@app.route("/api/status", methods=["GET"])
def api_status():
    db = get_db()
    present_count = 0

    if current_period:
        cur = db.cursor()
        cur.execute(f"SELECT COUNT(*) as cnt FROM attendance_attendora WHERE {current_period}=%s", ("Present",))
        result = cur.fetchone()
        if result:
            present_count = result["cnt"]
        db.close()

    return jsonify({
        "running": attendance_running,   # True if attendance thread is running
        "stats": {
            "present": present_count     # Live present count
        }
    }), 200
# ---------- GLOBAL FLAGS ----------
attendance_running = False
current_period = None
valid_periods = ["period1", "period2", "period3","period4","period5","period6","period7","period8"]  # adjust as per your table

# ---------- TWILIO CONFIG ----------
account_sid = "AC115fd4c34e0d3366cba43a3ae9240756"
auth_token = "cf4b27d191274419481dee121b8f9dd2"
from_whatsapp = "whatsapp:+14155238886"
client = Client(account_sid, auth_token)

# ---------- DATABASE ----------
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Mysql_123",
        database="attendora_db",
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM teachers WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    db.close()
    
    if user:
        session["teacher"] = username
        return jsonify({"status": "success"})
    return jsonify({"status": "fail", "msg": "Invalid login"})

# ---------- SELECT PERIOD ----------
@app.route("/select_period", methods=["POST"])
def select_period():
    global current_period
    period = request.json.get("period")
    if period not in valid_periods:
        return jsonify({"status": "fail", "msg": "Invalid period"})
    current_period = period
    return jsonify({"status": "success"})

# ---------- START ATTENDANCE ----------
@app.route("/start_attendance", methods=["POST"])
def start_attendance():
    global attendance_running
    attendance_running = True
    threading.Thread(target=capture_attendance).start()
    return jsonify({"status": "running"})

# ---------- STOP ATTENDANCE ----------
@app.route("/stop_attendance", methods=["POST"])
def stop_attendance():
    global attendance_running
    attendance_running = False
    return jsonify({"status": "stopped"})

# ---------- CAPTURE ATTENDANCE ----------
def capture_attendance():
    global attendance_running, current_period
    if not current_period:
        print("Error: current_period is None")
        return

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT roll_no, name, parents_number, encoding FROM students")
    students = cur.fetchall()

    known_encodings = []
    roll_numbers = []

    for s in students:
        if s["encoding"]:
            enc = pickle.loads(s["encoding"])
            if len(enc) == 128:
                known_encodings.append(enc)
                roll_numbers.append(s["roll_no"])

    camera = cv2.VideoCapture(0)
    marked = set()

    while attendance_running:
        ret, frame = camera.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        for enc in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
            if True in matches:
                idx = matches.index(True)
                roll = roll_numbers[idx]
                if roll not in marked:
                    marked.add(roll)
                    cur.execute(f"UPDATE attendance_attendora SET {current_period}=%s WHERE roll_no=%s", ("Present", roll))
                    db.commit()

        cv2.imshow("Attendora Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()
    db.close()
    mark_absent(marked)

# ---------- MARK ABSENT AND SEND WHATSAPP ----------
def mark_absent(marked):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT roll_no, name, parents_number FROM students")
    all_students = cur.fetchall()

    for s in all_students:
        roll = s["roll_no"]
        name = s["name"]
        parent_phone = s["parents_number"]

        # Only mark absent if the student wasn't detected
        if roll not in marked:
            try:
                cur.execute(f"UPDATE attendance_attendora SET {current_period}=%s WHERE roll_no=%s", ("Absent", roll))
                db.commit()
            except Exception as e:
                print(f"Error updating attendance for {roll}: {e}")
                continue

            # Send WhatsApp if number exists
            if parent_phone:
                try:
                    to_number = f"whatsapp:+91{parent_phone}"
                    print(f"Sending WhatsApp to {to_number}")
                    message = client.messages.create(
                        body=f"Attendora Alert\nYour child {name} (Roll: {roll}) is absent for Period {current_period}.",
                        from_=from_whatsapp,
                        to=to_number
                    )
                    print(f"Sent SID: {message.sid}")
                    time.sleep(1)
                except Exception as e:
                    print(f"WhatsApp Error for {roll}: {e}")

    db.close()
# ---------- SUMMARY ----------
@app.route("/summary", methods=["GET"])
def summary():
    if not current_period:
        return jsonify({"present": 0, "absent": 0, "present_list": [], "absent_list": []})

    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT roll_no, name FROM attendance_attendora WHERE {current_period}=%s", ("Present",))
    present_list = [f"{r['roll_no']} - {r['name']}" for r in cur.fetchall()]

    cur.execute(f"SELECT roll_no, name FROM attendance_attendora WHERE {current_period}=%s", ("Absent",))
    absent_list = [f"{r['roll_no']} - {r['name']}" for r in cur.fetchall()]

    db.close()
    return jsonify({
        "present": len(present_list),
        "absent": len(absent_list),
        "present_list": present_list,
        "absent_list": absent_list
    })
# ---------- ATTENDANCE LIST ----------
@app.route("/attendance_list", methods=["GET"])
def attendance_list():
    if not current_period:
        return jsonify({"present": [], "absent": []})

    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT roll_no, name, parents_number FROM attendance_attendora WHERE {current_period}=%s", ("Present",))
    present = cur.fetchall()

    cur.execute(f"SELECT roll_no, name, parents_number FROM attendance_attendora WHERE {current_period}=%s", ("Absent",))
    absent = cur.fetchall()

    db.close()
    return jsonify({"present": present, "absent": absent})

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True)