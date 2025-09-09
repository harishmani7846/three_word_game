import sqlite3

conn = sqlite3.connect("stories.db")
cursor = conn.cursor()

# Drop old tables if they exist
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS stories")

# Create fresh users table
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Create fresh stories table with ROUND column
cursor.execute("""
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    story TEXT NOT NULL,
    round INTEGER NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ Database reset complete!")
