from supabase import create_client
import os

class MoneyManager:
    def __init__(self):
        # Connect to Supabase using your environment variables
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client = create_client(url, key)

    def create_database(self):
        """
        Supabase tables are usually created in the dashboard.
        If you want, you can ensure the table exists via SQL:
        """
        self.client.rpc("sql", {"q": """
            CREATE TABLE IF NOT EXISTS money (
                user_id BIGINT PRIMARY KEY,
                balance INTEGER DEFAULT 0
            );
        """})

    def get_balance(self, user_id=None, all=False):
        if all:
            data = self.client.table("money").select("user_id, balance").execute()
            return data.data
        # Fetch specific user
        data = self.client.table("money").select("balance").eq("user_id", user_id).execute()
        if not data.data:
            # Insert new user with 0 balance
            self.client.table("money").insert({"user_id": user_id, "balance": 0}).execute()
            return 0
        return data.data[0]["balance"]

    def set_balance(self, user_id, value):
        # Upsert user balance
        self.client.table("money").upsert({"user_id": user_id, "balance": value}).execute()

    def update_balance(self, user_id, amount):
        # Fetch current balance
        current = self.get_balance(user_id)
        new_balance = current + amount
        self.set_balance(user_id, new_balance)
        return new_balance

    def delete_database(self):
        # Deletes all rows
        self.client.table("money").delete().neq("user_id", 0).execute()

    def reset_currency(self):
        # Reset all balances to 0
        all_users = self.get_balance(all=True)
        for user in all_users:
            self.set_balance(user["user_id"], 0)
