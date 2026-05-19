import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import sqlite3
from datetime import datetime
from web_functions import hash_password

ADMIN_USERNAME = "Admin"
ADMIN_EMAIL = "admin@mentra.local"
ADMIN_PASSWORD = "Admin@123"
ADMIN_ROLE = "admin"

hashed_password = hash_password(ADMIN_PASSWORD)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "database", "mentra.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("""
        INSERT INTO users (username, email, password, role, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ADMIN_USERNAME,
        ADMIN_EMAIL,
        hashed_password,
        ADMIN_ROLE,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    print("✅ Admin user created successfully.")

except sqlite3.IntegrityError:
    cursor.execute(
        "UPDATE users SET email = ?, password = ?, role = ? WHERE username = ?",
        (ADMIN_EMAIL, hashed_password, ADMIN_ROLE, ADMIN_USERNAME),
    )
    conn.commit()
    print("⚠️ Admin user already exists. Updated email/password/role.")

finally:
    conn.close()
