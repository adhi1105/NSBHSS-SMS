import sqlite3
import os

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# List of tables to remove (The Exam Module)
tables = ['exam_result', 'exam_exam', 'exam_gradingscale']

print("--- STARTING CLEANUP ---")
for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
        print(f"✅ Successfully deleted table: {table}")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Could not delete {table}: {e}")

# Also clear Django's memory of the exam migrations
try:
    cursor.execute("DELETE FROM django_migrations WHERE app='exam';")
    print("✅ Successfully reset migration history for 'exam'")
except Exception as e:
    print(f"⚠️ Could not reset migrations: {e}")

conn.commit()
conn.close()
print("--- CLEANUP COMPLETE ---")
print("Now run: python manage.py makemigrations exam")
print("Then run: python manage.py migrate exam")