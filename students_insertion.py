import mysql.connector
import pickle

# ✅ 1. Load the encodings and student names
with open('encodings.pkl', 'rb') as f:
    encode_list_known, names = pickle.load(f)

# ✅ 2. Connect to MySQL
connection = mysql.connector.connect(
    host="localhost",
    user="root",        # change if your MySQL username is different
    password="Mysql_123",# your MySQL password
    database="attendora_db"     # make sure this DB exists
)

cursor = connection.cursor()

# ✅ 3. Create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    roll_no VARCHAR(20),
    class_name VARCHAR(50),
    phone_number varchar(20),
    encoding BLOB
)
""")

# ✅ 4. Insert student details + encoding
# You can modify roll numbers or class names as needed
student_details = [
    ("loukika", "101", "Class 13",954888339),
    ("manusha", "102", "Class 12",8978137240),
    ("aishwarya", "103", "Class 12",7396841335),
    ("sravya", "104", "Class 12",9392596845),
    ("yathnika", "105", "Class 12",9959152028),
    ("rashmika", "106", "Class 12",8106143913),
    ("nandhini", "107", "Class 12",9391519382),
    ("varsha", "108", "Class 12",7993980020),
    ("sanjana", "109", "Class 12",9121427811),
    ("charan aditya", "110", "Class 12",9182737711),
    ("akash", "111", "Class 12",8977654743),
]

# ✅ 5. Insert each student + encoding
for (name, roll_no, class_name,phone_number), encoding in zip(student_details, encode_list_known):
    data = pickle.dumps(encoding)  # convert numpy array to binary
    cursor.execute("""
        INSERT INTO students (name, roll_no, class_name, encoding)
        VALUES (%s, %s, %s, %s)
    """, (name, roll_no, class_name, data))

connection.commit()
cursor.close()
connection.close()

print("✅ All student details with encodings inserted successfully!")