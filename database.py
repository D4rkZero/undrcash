import sqlite3
from config import DB_FILE

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Users table
c.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    balance REAL DEFAULT 0
)""")

# Deposits table
c.execute("""CREATE TABLE IF NOT EXISTS deposits (
    txid TEXT PRIMARY KEY,
    user_id TEXT,
    amount REAL,
    confirmed INTEGER
)""")

# Withdraws table
c.execute("""CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    amount REAL,
    currency TEXT,
    status TEXT DEFAULT 'pending'
)""")

# Stats table for leaderboard
c.execute("""CREATE TABLE IF NOT EXISTS stats (
    user_id TEXT PRIMARY KEY,
    total_bet REAL DEFAULT 0,
    total_won REAL DEFAULT 0,
    biggest_win REAL DEFAULT 0
)""")

conn.commit()

def get_user(user_id):
    c.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (str(user_id), 0))
        conn.commit()
        return {"user_id": str(user_id), "balance": 0}
    return {"user_id": user[0], "balance": user[1]}

def update_balance(user_id, amount):
    user = get_user(user_id)
    new_balance = user["balance"] + amount
    c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, str(user_id)))
    conn.commit()
    return new_balance

def update_stats(user_id, bet=0, won=0):
    c.execute("SELECT * FROM stats WHERE user_id=?", (str(user_id),))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO stats (user_id, total_bet, total_won, biggest_win) VALUES (?, ?, ?, ?)",
                  (str(user_id), bet, won, won))
    else:
        total_bet = row[1] + bet
        total_won = row[2] + won
        biggest_win = max(row[3], won)
        c.execute("UPDATE stats SET total_bet=?, total_won=?, biggest_win=? WHERE user_id=?",
                  (total_bet, total_won, biggest_win, str(user_id)))
    conn.commit()
