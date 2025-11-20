import mysql.connector
import face_recognition
import numpy as np
import json

# -----------------------------------------------------------
# 1. DATABASE CONNECTION FUNCTION
# -----------------------------------------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mysql_123",#<<< CHANGE THIS
        database="attendora_db"            # <<< Your DB name
    )


# -----------------------------------------------------------
# 2. FUNCTION TO INSERT A NEW STUDENT INTO 'students' TABLE
# -----------------------------------------------------------
def insert_student(id, name, roll_no, class_name, phone_number, image_path):

    print("\n📌 Step 1: Loading student image...")
    try:
        image = face_recognition.load_image_file(image_path)
    except FileNotFoundError:
        print(f"❌ ERROR: Image not found at path: {image_path}")
        return

    print("📌 Step 2: Generating face encoding...")
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        print("❌ ERROR: No face detected in the image.")
        return

    face_encoding = encodings[0].tolist()   # Convert to list → Storable in MySQL
    face_encoding_json = json.dumps(face_encoding)

    print("📌 Step 3: Connecting to MySQL database...")
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO students
        (id, name, roll_no, class_name, phone_number, encoding)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    print("📌 Step 4: Inserting data into students table...")

    cursor.execute(sql, (
        id,
        name,
        roll_no,
        class_name,
        phone_number,
        face_encoding_json
    ))

    conn.commit()
    conn.close()

    print("\n✅ SUCCESS: Student inserted along with face encoding!")
    print("--------------------------------------------------------")


# -----------------------------------------------------------
# 3. CALL THE FUNCTION → ENTER NEW STUDENT VALUES HERE
# -----------------------------------------------------------

insert_student(
    id=12,                                  # <--- CHANGE FOR NEW STUDENT
    name="pujitha",                 # <--- CHANGE
    roll_no="112",                    # <--- CHANGE
    class_name=" class 12",                  # <--- CHANGE
    phone_number="8919669223",               # <--- CHANGE
    image_path=r"astudents_images/112_pujitha.jpeg"  # <--- EXACT IMAGE NAME
)