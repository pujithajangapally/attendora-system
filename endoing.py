import face_recognition
import mysql.connector
import pickle
import os

# ----------------- 1. Connect to MySQL -----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mysql_123",  # Replace with your MySQL password
    database="attendora_db"
)
cursor = conn.cursor()

# ----------------- 2. Path to student images -----------------
image_folder = "astudents_images"

# ----------------- 3. Retrieve all students with id, roll_no, name -----------------
cursor.execute("SELECT id, roll_no, name FROM students")
students = cursor.fetchall()  # List of tuples (id, roll_no, name)

for student in students:
    student_id = student[0]
    roll_no = student[1]
    name = student[2]

    # Construct image filename
    image_filename = f"{roll_no}_{name}.jpeg"  # e.g., S001_John.jpg
    image_path = os.path.join(image_folder, image_filename)

    if not os.path.exists(image_path):
        print(f"Image not found for ID {student_id} - {name}, skipping...")
        continue

    # Load image and compute 128-d face encoding
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        print(f"No face found in {image_filename}, skipping...")
        continue

    encoding = encodings[0]  # 128-d numpy array

    # Convert encoding to bytes for storage
    encoding_bytes = pickle.dumps(encoding)

    # Update the student row with the encoding
    cursor.execute("""
        UPDATE students
        SET encoding = %s
        WHERE id = %s
    """, (encoding_bytes, student_id))

    print(f"Updated ID {student_id} - {roll_no} - {name} with 128-d encoding.")

# ----------------- 4. Commit and close connection -----------------
conn.commit()
cursor.close()
conn.close()
print("All students updated successfully!")