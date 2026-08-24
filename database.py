import sqlite3

DB_NAME = "vigilpay.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        customer_id TEXT,
        amount REAL,
        payee TEXT,
        new_payee INTEGER,
        destination_type TEXT,
        recent_transfers INTEGER,
        purpose TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT,
        speaker TEXT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT,
        event TEXT,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def log_conversation(transaction_id, speaker, message):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
"""
    INSERT INTO conversation_log (
        transaction_id,
        speaker,
        message
    )
    VALUES (?, ?, ?)
    """, (
        transaction_id,
        speaker,
        message
    ))

    conn.commit()
    conn.close()


def get_conversation(transaction_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT speaker, message, created_at
    FROM conversation_log
    WHERE transaction_id = ?
    ORDER BY id
    """, (transaction_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "speaker": row[0],
            "message": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]


def log_audit(transaction_id, event, details):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO audit_log (
        transaction_id,
        event,
        details
    )
    VALUES (?, ?, ?)
    """, (
        transaction_id,
        event,
        details
    ))

    conn.commit()
    conn.close()

def get_audit_log(transaction_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT event, details, created_at
    FROM audit_log
    WHERE transaction_id = ?
    ORDER BY id
    """, (transaction_id,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "event": row[0],
            "details": row[1],
            "created_at": row[2]
        }
        for row in rows
    ]

def reset_case(transaction_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM conversation_log
    WHERE transaction_id = ?
    """, (transaction_id,))

    cur.execute("""
    DELETE FROM audit_log
    WHERE transaction_id = ?
    """, (transaction_id,))

    conn.commit()
    conn.close()
