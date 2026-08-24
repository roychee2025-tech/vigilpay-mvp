from database import init_db, get_connection

init_db()

conn = get_connection()
cur = conn.cursor()

cur.execute("""
INSERT OR REPLACE INTO transactions (
    transaction_id,
    customer_id,
    amount,
    payee,
    new_payee,
    destination_type,
    recent_transfers,
    purpose
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "TX001",
    "CUST001",
    25000,
    "NEXUS DIGITAL ASSETS PTE LTD",
    1,
    "Digital asset / crypto",
    3,
    "Investment opportunity introduced by an online friend. "
    "Returns are guaranteed and payment must be made today."
))

conn.commit()
conn.close()

print("Synthetic bank transaction created.")
