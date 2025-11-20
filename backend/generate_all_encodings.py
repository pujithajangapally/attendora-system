import face_recognition
import mysql.connector
import pickle
import os

# ----------------- 1. Connect to MySQL -----------------
conn = mysql.connector.connect(
    host="localhost",
    user="attendora_user",
    password="Mysql_123",  # Replace with your MySQL password
    database="attendora_db"
)
cursor = conn.cursor()

# ----------------- 2. Path to student images -----------------
image_folder = "astudents_images"  # Folder containing all 12 student images

# ----------------- 3. Student data -----------------
# id, roll_no, name, parent_number
students_data = [
    (1, "101", "loukika", "9542888339"),
    (2, "102", "manusha", "8978137240"),
    (3, "103", "aishwarya", "7396841225"),
    (4, "104", "sravya", "9392596845"),
    (5, "105", "yathnika", "9959152028"),
    (6, "106", "rashmika", "8106143913"),
    (7, "107", "nandhini", "9391519382"),
    (8, "108", "varsha", "7993980020"),
    (9, "109", "sanjana", "9121427811"),
    (10, "110", "charan_aditya", "9182737711"),
    (11, "111", "akash", "8977654743"),
    (12, "112", "pujitha", "8919669223")
]

# ----------------- 4. Loop through students and insert -----------------
for student in students_data:
    student_id, roll_no, name, parent_number = student

    # Image filename should match the student's name (or roll_no_name)
    image_filename = f"{roll_no}_{name}.jpeg"  # Adjust if your images are .jpg
    image_path = os.path.join(image_folder, image_filename)

    if not os.path.exists(image_path):
        print(f"Image not found for {roll_no} - {name}, skipping...")
        continue

    # Load image and compute 128-d face encoding
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        print(f"No face found in {image_filename}, skipping...")
        continue

    encoding = encodings[0]  # 128-d numpy array
    encoding_bytes = pickle.dumps(encoding)  # Convert to bytes for storage

    # Insert into students table
    cursor.execute("""
        INSERT INTO students (id, roll_no, name, parent_number, encoding)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, roll_no, name, parent_number, encoding_bytes))

    print(f"Inserted ID {student_id} - {roll_no} - {name}")

# ----------------- 5. Commit and close connection -----------------
conn.commit()
cursor.close()
conn.close()
print("All 12 students inserted successfully!")