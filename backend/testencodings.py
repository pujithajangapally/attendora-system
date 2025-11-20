import pymysql
import pickle

# ----------------- 1. Connect to MySQL -----------------
conn = pymysql.connect(
    host="localhost",
    user="root",                   # your MySQL user
    password="Mysql_123", # your MySQL password
    database="attendora_db"
)
cursor = conn.cursor()

# ----------------- 2. Select all students' encodings -----------------
cursor.execute("SELECT id, roll_no, name, encoding FROM students")
rows = cursor.fetchall()

# ----------------- 3. Loop through and check encoding length -----------------
for row in rows:
    student_id, roll_no, name, encoding_bytes = row
    if encoding_bytes:
        encoding = pickle.loads(encoding_bytes)
        print(f"ID {student_id} - {roll_no} - {name}: Encoding length = {len(encoding)}")
    else:
        print(f"ID {student_id} - {roll_no} - {name}: No encoding stored")

# ----------------- 4. Close connection -----------------
cursor.close()
conn.close()