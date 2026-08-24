from database import get_connection

def get_transaction(transaction_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT
        transaction_id,
        customer_id,
        amount,
        payee,
        new_payee,
        destination_type,
        recent_transfers,
        purpose
    FROM transactions
    WHERE transaction_id = ?
    """, (transaction_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "transaction_id": row[0],
        "customer_id": row[1],
        "amount": row[2],
        "payee": row[3],
        "new_payee": bool(row[4]),
        "destination_type": row[5],
        "recent_transfers": row[6],
        "purpose": row[7]
    }
