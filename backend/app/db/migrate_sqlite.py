import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cardwise.db")

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def get_columns(table):
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    cc_cols = get_columns("credit_cards")
    print("credit_cards cols:", cc_cols)

    if "category" not in cc_cols:
        cursor.execute("ALTER TABLE credit_cards ADD COLUMN category VARCHAR(80)")
        print("Added category to credit_cards")

    if "verification_status" not in cc_cols:
        cursor.execute("ALTER TABLE credit_cards ADD COLUMN verification_status VARCHAR(80) DEFAULT 'Imported — needs verification'")
        print("Added verification_status to credit_cards")

    if "notes" not in cc_cols:
        cursor.execute("ALTER TABLE credit_cards ADD COLUMN notes VARCHAR(255)")
        print("Added notes to credit_cards")

    stmt_cols = get_columns("statements")
    print("statements cols:", stmt_cols)

    if "is_credit_balance" not in stmt_cols:
        cursor.execute("ALTER TABLE statements ADD COLUMN is_credit_balance BOOLEAN DEFAULT 0")
        print("Added is_credit_balance to statements")

    if "is_historical" not in stmt_cols:
        cursor.execute("ALTER TABLE statements ADD COLUMN is_historical BOOLEAN DEFAULT 0")
        print("Added is_historical to statements")

    if "notes" not in stmt_cols:
        cursor.execute("ALTER TABLE statements ADD COLUMN notes VARCHAR(255)")
        print("Added notes to statements")

    conn.commit()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    migrate()
