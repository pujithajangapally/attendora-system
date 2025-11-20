import face_recognition
import pymysql
import pickle
import os

# ----------------- 1. Connect to MySQL -----------------
conn = pymysql.connect(
    host="localhost",
    user="root",                   # or your MySQL user
    password="Mysql_123", # replace with your password
    database="attendora_db"
)
cursor = conn.cursor()

# ----------------- 2. Student data -----------------
student_id = 110
roll_no = "110"
name = "charanaditya"          # replace with actual name
parent_number = "9182737711"      # replace with actual parent number

# ----------------- 3. Path to image -----------------
image_folder = "astudents_images"
image_filename = f"{roll_no}_{name}.jpeg"  # adjust if .jpg
image_path = os.path.join(image_folder, image_filename)

# ----------------- 4. Generate 128-d encoding -----------------
image = face_recognition.load_image_file(image_path)
encodings = face_recognition.face_encodings(image)

if len(encodings) == 0:
    print(f"No face found in {image_filename}, cannot insert.")
else:
    encoding = encodings[0]  # 128-d numpy array
    encoding_bytes = pickle.dumps(encoding)

    # ----------------- 5. Insert into students table -----------------
    cursor.execute("""
        INSERT INTO students (id, roll_no, name, parent_number, encoding)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, roll_no, name, parent_number, encoding_bytes))

    conn.commit()
    print(f"Inserted ID {student_id} - {roll_no} - {name}")

# ----------------- 6. Close connection -----------------
cursor.close()
conn.close()