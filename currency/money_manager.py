import sqlite3
from pathlib import Path

class MoneyManager:
    def __init__(self):
        # Path to the database file inside the money folder
        self.db_path = Path(__file__).parent / "money" / "money.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def create_database(self):
        """Create the money table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS money (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 1000
            )
        """)
        self.conn.commit()

    def delete_database(self):
        """Delete all user data from the money table."""
        self.cursor.execute("DELETE FROM money")
        self.conn.commit()

    def reset_currency(self):
        """Reset all balances to 1000."""
        self.cursor.execute("UPDATE money SET balance = 1000")
        self.conn.commit()

    def get_balance(self, user_id=None, all=False):
        """
        Get the balance of a specific user or all users.
        - user_id: Discord user ID
        - all: if True, returns list of tuples (user_id, balance) for all users
        """
        if all:
            self.cursor.execute("SELECT user_id, balance FROM money")
            return self.cursor.fetchall()
        
        # Check if user exists, if not add them with default balance 1000
        self.cursor.execute("SELECT balance FROM money WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result is None:
            self.cursor.execute("INSERT INTO money(user_id, balance) VALUES(?, ?)", (user_id, 1000))
            self.conn.commit()
            return 1000
        return result[0]

    def set_balance(self, user_id, value):
        """Set the balance for a user. Create user if they don't exist."""
        # Ensure the user exists
        self.cursor.execute("INSERT OR IGNORE INTO money(user_id, balance) VALUES(?, ?)", (user_id, 1000))
        # Update the balance
        self.cursor.execute("UPDATE money SET balance = ? WHERE user_id = ?", (value, user_id))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
