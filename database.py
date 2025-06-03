import sqlite3

# Connect to DB (or create it)
conn = sqlite3.connect('adoni.db')
c = conn.cursor()

# Members table
c.execute('''
CREATE TABLE IF NOT EXISTS members (
    user_id INTEGER PRIMARY KEY,
    elo INTEGER DEFAULT 800,
    streak INTEGER DEFAULT 0,
    min_elo INTEGER DEFAULT 100,
    last_read_date TEXT
)
''')

# Book completions (optional for +50 ELO rule)
c.execute('''
CREATE TABLE IF NOT EXISTS books (
    user_id INTEGER,
    book_name TEXT,
    completed INTEGER DEFAULT 0
)
''')

conn.commit()
conn.close()
