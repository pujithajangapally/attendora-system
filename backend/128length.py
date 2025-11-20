import os
import cv2
import numpy as np
import face_recognition
import mysql.connector

# ====== DB CONNECTION ======
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mysql_123",
    database="attendora_db"
)
cursor = conn.cursor()

# ====== IMAGES PATH ======
IMAGES_PATH = "astudents_images"

# ====== START PROCESS ======
print("Starting encoding generation...")

for filename in os.listdir(IMAGES_PATH):

    if not (filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png")):
        continue

    roll_no = filename.split('_')[0]   # extract 101 from "101_name.jpg"
    img_path = os.path.join(IMAGES_PATH, filename)

    print(f"\nProcessing: {filename} (Roll: {roll_no})")

    # Load image
    img = cv2.imread(img_path)
    if img is None:
        print("❌ Bad image file. Skipping.")
        continue

    # Convert BGR → RGB
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detect face
    face_locations = face_recognition.face_locations(rgb)

    if len(face_locations) == 0:
        print("❌ No face found. Skipping.")
        continue

    if len(face_locations) > 1:
        print("❌ Multiple faces found. Skipping.")
        continue

    # Encode face
    encoding = face_recognition.face_encodings(rgb, face_locations)[0]

    if len(encoding) != 128:
        print(f"❌ Invalid encoding length ({len(encoding)}). Skipping.")
        continue

    encoding_str = np.array(encoding).tobytes()

    # Check student exists
    cursor.execute("SELECT roll_no FROM students WHERE roll_no=%s", (roll_no,))
    if cursor.fetchone() is None:
        print("❌ Student not found in database. Skipping.")
        continue

    # UPDATE DATABASE
    cursor.execute(
        "UPDATE students SET encoding=%s WHERE roll_no=%s",
        (encoding_str, roll_no)
    )
    conn.commit()

    print("✅ Encoding saved successfully.")

print("\n=== DONE ===")
cursor.close()
conn.close()