import psycopg2
import os

class MoneyManager:
    def __init__(self):
        # Connect to your Supabase Postgres database
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.cursor = self.conn.cursor()

    def create_database(self):
        """Create the money table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS money (
                user_id BIGINT PRIMARY KEY,
                balance INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    def delete_database(self):
        """Delete all user data from the money table."""
        self.cursor.execute("DELETE FROM money")
        self.conn.commit()

    def reset_currency(self):
        """Reset all balances to 0."""
        self.cursor.execute("UPDATE money SET balance = 0")
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
        
        # Check if user exists, if not add them with default balance 0
        self.cursor.execute("SELECT balance FROM money WHERE user_id = %s", (user_id,))
        result = self.cursor.fetchone()
        if result is None:
            self.cursor.execute(
                "INSERT INTO money(user_id, balance) VALUES(%s, %s)", 
                (user_id, 0)
            )
            self.conn.commit()
            return 0
        return result[0]

    def set_balance(self, user_id, value):
        """Set the balance for a user. Create user if they don't exist."""
        # Ensure the user exists
        self.cursor.execute(
            "INSERT INTO money(user_id, balance) VALUES(%s, %s) ON CONFLICT(user_id) DO NOTHING", 
            (user_id, 0)
        )
        # Update the balance
        self.cursor.execute(
            "UPDATE money SET balance = %s WHERE user_id = %s", 
            (value, user_id)
        )
        self.conn.commit()

    def update_balance(self, user_id, amount: int):
        """
        Add or subtract from a user's balance.
        - user_id: Discord user ID
        - amount: positive to add, negative to subtract
        """
        # Ensure the user exists
        self.cursor.execute(
            "INSERT INTO money(user_id, balance) VALUES(%s, %s) ON CONFLICT(user_id) DO NOTHING", 
            (user_id, 0)
        )
        
        # Update balance by adding amount
        self.cursor.execute(
            "UPDATE money SET balance = balance + %s WHERE user_id = %s", 
            (amount, user_id)
        )
        self.conn.commit()

        # Return the new balance
        self.cursor.execute("SELECT balance FROM money WHERE user_id = %s", (user_id,))
        return self.cursor.fetchone()[0]

    def close(self):
        """Close the database connection."""
        self.conn.close()
