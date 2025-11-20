import mysql.connector

# -----------------------------
# 1. CONNECT TO MYSQL DATABASE
# -----------------------------
connection = mysql.connector.connect(
    host="localhost",            # change to your MySQL host or PlanetScale host
    user="root",                 # your MySQL username
    password="Mysql_123",    # your MySQL password
    database="attendora_db"         # your database name
)

cursor = connection.cursor()

# -----------------------------
# 2. CREATE ATTENDANCE TABLE
# -----------------------------
create_table_query = """
CREATE TABLE IF NOT EXISTS attendance_attendora (
    id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no INT NOT NULL,
    date DATE NOT NULL,

    period1 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period2 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period3 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period4 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period5 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period6 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period7 ENUM('present', 'absent', 'late') DEFAULT 'absent',
    period8 ENUM('present', 'absent', 'late') DEFAULT 'absent',

    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (roll_no, date)
);
"""

cursor.execute(create_table_query)
connection.commit()
print("✔ attendance_attendora table created successfully.")


# -------------------------------------
# 3. INSERT ROLL NUMBERS FOR TODAY
# -------------------------------------

# Fetch roll numbers from the students table
cursor.execute("SELECT roll_no FROM students;")
students = cursor.fetchall()

if not students:
    print("⚠ No students found in students table. Add students first.")
else:
    print(f"✔ Found {len(students)} students. Preparing attendance rows...")

# Insert row for each roll number (each student) for today's date
insert_query = """
INSERT IGNORE INTO attendance_attendora (roll_no, date)
VALUES (%s, CURDATE());
"""

for student in students:
    cursor.execute(insert_query, (student[0],))
    connection.commit()

print("✔ Attendance entries for today created for all students.")

# -------------------------------------
# 4. SHOW SAMPLE OUTPUT
# -------------------------------------
cursor.execute("""
SELECT roll_no, date, period1, period2 
FROM attendance_attendora 
WHERE date = CURDATE()
LIMIT 5;
""")

result = cursor.fetchall()

print("\n📌 Sample Attendance Rows Created:")
for row in result:
    print(row)

cursor.close()
connection.close()

print("\n🎉 Setup Complete!")