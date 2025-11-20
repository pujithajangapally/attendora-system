# attendora_backend_debug.py
# Robust Attendora backend with strict loading & diagnostics
# Edit CONFIG only, then run: python attendora_backend_debug.py

import cv2
import face_recognition
import numpy as np
import mysql.connector
import base64
from datetime import date
from twilio.rest import Client
import sys

# ------------- CONFIG (EDIT THESE) -------------
CONFIG = {
    "DB_HOST": "localhost",
    "DB_USER": "root",
    "DB_PASS": "Mysql_123",   # <-- CHANGE
    "DB_NAME": "attendora_db",

    "TOLERANCE": 0.48,
    "FRAME_SCALE": 0.5,
    "MOTION_THRESHOLD": 8.0,

    # Twilio (optional)
    "TWILIO_ENABLED": False,
    "TWILIO_ACCOUNT_SID": "YOUR_SID",
    "TWILIO_AUTH_TOKEN": "YOUR_TOKEN",
    "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
}

# ------------- DB helpers -------------
def get_db_conn():
    return mysql.connector.connect(
        host=CONFIG["DB_HOST"],
        user=CONFIG["DB_USER"],
        password=CONFIG["DB_PASS"],
        database=CONFIG["DB_NAME"],
        autocommit=True
    )

# ------------- Load encodings strictly -------------
def load_encodings_strict():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT roll_no, name, phone_number, encoding FROM students")
    rows = cur.fetchall()

    known_rolls = []
    known_names = []
    known_phones = []
    known_encodings = []

    print(f"DEBUG: loaded {len(rows)} rows from students table")

    for i, row in enumerate(rows):
        roll_no, name, phone, enc_field = row

        if enc_field is None:
            print(f"DEBUG SKIP: roll_no={roll_no} - encoding is NULL")
            continue

        arr = None
        # Attempt 1: enc_field is raw BLOB of float32 (512 bytes)
        try:
            if isinstance(enc_field, (bytes, bytearray)):
                b = enc_field
            else:
                # sometimes MySQL returns str for blob; try to handle
                b = enc_field.encode('latin1') if isinstance(enc_field, str) else None

            if b is not None:
                arr_try = np.frombuffer(b, dtype=np.float32)
                if arr_try.size == 128:
                    arr = arr_try.astype(np.float64)   # convert to float64 to match face_recognition
                    print(f"DEBUG OK (BLOB float32) roll_no={roll_no}")
                else:
                    # maybe it's float64 buffer
                    arr_try2 = np.frombuffer(b, dtype=np.float64)
                    if arr_try2.size == 128:
                        arr = arr_try2
                        print(f"DEBUG OK (BLOB float64) roll_no={roll_no}")
        except Exception as e:
            print(f"DEBUG BLOB parse error for {roll_no}: {e}")

        # Attempt 2: maybe stored as comma-separated string of floats
        if arr is None:
            try:
                if isinstance(enc_field, str) and ',' in enc_field:
                    parts = enc_field.split(',')
                    if len(parts) == 128:
                        arr = np.array([float(x) for x in parts], dtype=np.float64)
                        print(f"DEBUG OK (csv string) roll_no={roll_no}")
            except Exception as e:
                print(f"DEBUG CSV parse error for {roll_no}: {e}")

        # Attempt 3: maybe stored as JSON list
        if arr is None:
            try:
                import json
                if isinstance(enc_field, str):
                    parsed = json.loads(enc_field)
                    if isinstance(parsed, list) and len(parsed) == 128:
                        arr = np.array(parsed, dtype=np.float64)
                        print(f"DEBUG OK (json) roll_no={roll_no}")
            except Exception as e:
                # ignore JSON parse errors
                pass

        if arr is None:
            print(f"DEBUG BAD ENCODING: roll_no={roll_no} - could not parse into 128-vector")
            continue

        # final shape check
        if arr.shape != (128,):
            print(f"DEBUG WRONG SHAPE: roll_no={roll_no} shape={arr.shape} - skipping")
            continue

        known_rolls.append(str(roll_no))
        known_names.append(name if name else str(roll_no))
        known_phones.append(phone if phone else "")
        known_encodings.append(arr)

    cur.close()
    conn.close()
    print(f"DEBUG: loaded {len(known_encodings)} valid encodings (expected all students).")
    return known_rolls, known_names, known_phones, known_encodings

# ------------- Twilio helper -------------
def send_whatsapp(number, body):
    if not CONFIG["TWILIO_ENABLED"]:
        print("[TWILIO DISABLED] would send:", number, body)
        return
    try:
        client = Client(CONFIG["TWILIO_ACCOUNT_SID"], CONFIG["TWILIO_AUTH_TOKEN"])
        msg = client.messages.create(from_=CONFIG["TWILIO_WHATSAPP_FROM"], body=body, to=f"whatsapp:{number}")
        print("Sent msg sid:", msg.sid)
    except Exception as e:
        print("Twilio send error:", e)

# ------------- DB attendance helpers -------------
def ensure_today_rows():
    conn = get_db_conn()
    cur = conn.cursor()
    today = date.today().isoformat()
    cur.execute("SELECT roll_no FROM students")
    for (roll,) in cur.fetchall():
        try:
            cur.execute("INSERT IGNORE INTO attendance_attendora (date, roll_no) VALUES (%s, %s)", (today, roll))
        except Exception as e:
            print("ensure_today_rows error:", e)
    cur.close()
    conn.close()

def mark_present_db(roll_no, period_col):
    conn = get_db_conn()
    cur = conn.cursor()
    today = date.today().isoformat()
    try:
        cur.execute("INSERT IGNORE INTO attendance_attendora (date, roll_no) VALUES (%s, %s)", (today, roll_no))
        cur.execute(f"UPDATE attendance_attendora SET {period_col}='present' WHERE roll_no=%s AND date=%s", (roll_no, today))
    except Exception as e:
        print("mark_present_db error:", e)
    cur.close()
    conn.close()

def finalize_and_notify(all_rolls, all_names, all_phones, seen_set, period_col):
    conn = get_db_conn()
    cur = conn.cursor()
    today = date.today().isoformat()
    for roll, name, phone in zip(all_rolls, all_names, all_phones):
        if roll not in seen_set:
            try:
                cur.execute("INSERT IGNORE INTO attendance_attendora (date, roll_no) VALUES (%s, %s)", (today, roll))
                cur.execute(f"UPDATE attendance_attendora SET {period_col}='absent' WHERE roll_no=%s AND date=%s", (roll, today))
                print(f"Marked absent: {roll} - {name}")
                if phone:
                    body = f"Dear Parent, {name} (Roll {roll}) was absent today ({period_col})."
                    send_whatsapp(phone, body)
            except Exception as e:
                print("finalize error:", e)
    conn.commit()
    cur.close()
    conn.close()

# ------------- Main camera function -------------
def run_attendance(period_col="period1"):
    # 1) load known encodings strictly
    known_rolls, known_names, known_phones, known_encodings = load_encodings_strict()
    if not known_encodings:
        print("No valid encodings found -- abort.")
        return

    # convert to numpy array for face_distance (list of arrays ok too)
    known_encodings = [np.asarray(e, dtype=np.float64) for e in known_encodings]

    # show a small sanity table
    print("Sanity check (first 10):")
    for i in range(min(10, len(known_rolls))):
        print(f"  {i}. roll={known_rolls[i]} name={known_names[i]} enc_dtype={known_encodings[i].dtype} enc_shape={known_encodings[i].shape}")

    ensure_today_rows()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam")
        return

    # warmup frame for motion detection
    ret, prev_frame = cap.read()
    if not ret:
        print("Camera read error")
        cap.release()
        return
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21,21), 0)

    seen = set()
    print("Attendance running. Press 'q' to stop and finalize.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # simple motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21,21), 0)
            diff = cv2.absdiff(prev_gray, gray)
            motion_level = float(np.mean(diff))
            prev_gray = gray

            if motion_level < CONFIG["MOTION_THRESHOLD"]:
                cv2.putText(frame, "No motion detected - move to camera", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                cv2.imshow("Attendora", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            # scale & convert
            small = cv2.resize(frame, (0,0), fx=CONFIG["FRAME_SCALE"], fy=CONFIG["FRAME_SCALE"])
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            # detect & encode
            face_locs = face_recognition.face_locations(rgb_small)
            face_encs = face_recognition.face_encodings(rgb_small, face_locs)

            for enc in face_encs:
                enc = np.asarray(enc, dtype=np.float64)  # ensure dtype
                # compute distances
                try:
                    distances = face_recognition.face_distance(known_encodings, enc)
                except Exception as e:
                    print("ERROR computing distances:", e)
                    print("known_encodings count:", len(known_encodings), "enc shape:", enc.shape)
                    raise

                best_idx = np.argmin(distances)
                best_dist = float(distances[best_idx])

                if best_dist <= CONFIG["TOLERANCE"]:
                    roll = known_rolls[best_idx]
                    name = known_names[best_idx]
                    if roll not in seen:
                        print(f"Recognized {name} (roll {roll}) dist={best_dist:.3f} -> marking present")
                        mark_present_db(roll, period_col)
                        seen.add(roll)
                else:
                    # unknown
                    pass

            cv2.imshow("Attendora", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    # finalize
    finalize_and_notify = finalize_and_notify if False else finalize_and_notify  # placeholder to avoid lint
    finalize_and_notify = globals()['finalize_and_notify'] if 'finalize_and_notify' in globals() else finalize_and_notify
    finalize_and_notify(known_rolls, known_names, known_phones, seen, period_col)
    print("Done.")

# ------------- run if main -------------
if __name__ == "__main__":
    # change period if you want (period1..period8)
    run_attendance("period1")