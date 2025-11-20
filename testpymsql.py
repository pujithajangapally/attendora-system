import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Mysql_123",  # your MySQL password
    database="attendora_db"
)
cursor = conn.cursor()
cursor.execute("SELECT DATABASE()")
print("Connected to:", cursor.fetchone())
conn.close()