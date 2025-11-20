import mysql.connector

# -------------------------------------
#  DATABASE CONNECTION
# -------------------------------------
db = mysql.connector.connect(
    host="localhost",
    user="attendora_user",
    password="Mysql_123",  # <<--- CHANGE THIS
    database="attendora_db"
)

cursor = db.cursor()

# -------------------------------------
#  CREATE TABLE: students
# -------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    parent_number VARCHAR(20),
    encoding LONGBLOB
);
""")

print("✔ Table 'students' created")

# -------------------------------------
#  CREATE TABLE: attendance_attendora (with ENUM)
# -------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_attendora (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20),
    name VARCHAR(100),
    date DATE,

    period1 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period2 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period3 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period4 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period5 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period6 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period7 ENUM('Present', 'Absent') DEFAULT 'Absent',
    period8 ENUM('Present', 'Absent') DEFAULT 'Absent'
);
""")

print("✔ Table 'attendance_attendora' created with ENUM")


# -------------------------------------
#  INSERT 12 STUDENTS
# -------------------------------------
students = [
    ("101", "loukika", "9542888339"),
    ("102", "manusha", "8978137240"),
    ("103", "aishwarya", "7396841335"),
    ("104", "sravya", "9392596845"),
    ("105", "yathnika", "9959152028"),
    ("106", "rashmika", "8106143913"),
    ("107", "nandhini", "9391519382"),
    ("108", "varsha",  "7993980020"),
    ("109", "sanjana", "9121427811"),
    ("110", "charan aditya", "9182737711"),
    ("111", "akash", "8977654743"),
    ("112", "pujitha", "8919669223")
]

cursor.executemany("""
INSERT INTO students (roll_no, name, parent_number, encoding)
VALUES (%s, %s, %s, NULL);
""", students)

print("✔ Inserted 12 students")


# -------------------------------------
#  INSERT ATTENDANCE ROWS FOR TODAY
# -------------------------------------
cursor.executemany("""
INSERT INTO attendance_attendora (roll_no, name, date)
VALUES (%s, %s, CURDATE());
""", [(s[0], s[1]) for s in students])

print("✔ Inserted attendance rows for 12 students (default Absent)")


# -------------------------------------
#  SAVE CHANGES AND CLOSE
# -------------------------------------
db.commit()
db.close()

print("\n🎉 DONE! All tables created & data inserted successfully.")