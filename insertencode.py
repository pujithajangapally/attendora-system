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

# ----------------- 3. Optional parent numbers dictionary by ID -----------------
# Key: student ID, Value: parent number
parent_numbers_by_id = {
    1: "9542888339",
    2: "8978137240",
    3: "7396841335",
    4: "9392596845",
    5: "9959152028",
    6: "8106143913",
    7: "9391519382",
    8: "7993980020",
    9: "9121427811",
    10: "9182737711",
    11:  "8977654743",
    12:  "8919669223"
    # Add all student IDs and their parent numbers here
}

# ----------------- 4. Retrieve all students with IDs -----------------
cursor.execute("SELECT id, name FROM students")
students = cursor.fetchall()  # List of tuples (id, name)

for student in students:
    student_id = student[0]
    name = student[1]

    # Assume the image filename matches the student name (or use a mapping)
    image_filename = f"{name}.jpg"  # or any mapping you prefer
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
    encoding_bytes = pickle.dumps(encoding)

    # Get parent number if available
    parent_number = parent_numbers_by_id.get(student_id, None)

    # Update the row using the ID
    cursor.execute("""
        UPDATE students
        SET parent_number = %s, encoding = %s
        WHERE id = %s
    """, (parent_number, encoding_bytes, student_id))

    print(f"Updated ID {student_id} - {name}")

# ----------------- 5. Commit and close -----------------
conn.commit()
cursor.close()
conn.close()
print("All students updated successfully!")