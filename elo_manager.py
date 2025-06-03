import sqlite3
from datetime import datetime

DB_NAME = 'adoni.db'

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO members (user_id) VALUES (?)", (user_id,))
        conn.commit()
        c.execute("SELECT * FROM members WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return user

def update_elo(user_id, delta):
    user = get_user(user_id)
    new_elo = max(user[2] + delta, user[4])  # max(current + delta, min_elo)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE members SET elo = ? WHERE user_id = ?", (new_elo, user_id))
    conn.commit()
    conn.close()

def set_min_elo(user_id, new_min_elo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE members SET min_elo = ? WHERE user_id = ?", (new_min_elo, user_id))
    conn.commit()
    conn.close()
