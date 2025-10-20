from supabase import create_client
from datetime import datetime, timezone
import os

class MoneyManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client = create_client(url, key)

    def get_balance(self, user_id=None, all=False):
        if all:
            data = self.client.table("money").select("user_id, balance, time, words").execute()
            return data.data

        # Fetch specific user
        data = self.client.table("money").select("balance, time, words").eq("user_id", user_id).execute()
        if not data.data:
            # Create new user entry if not exists
            self.client.table("money").insert({
                "user_id": user_id,
                "balance": 0,
                "time": datetime.now(timezone.utc).isoformat(),
                "words": "none"
            }).execute()
            return 0
        return data.data[0]

    def set_balance(self, user_id, value, words=None):
        # Update time and optionally words
        update_data = {
            "user_id": user_id,
            "balance": value,
            "time": datetime.now(timezone.utc).isoformat()
        }
        if words:
            update_data["words"] = words

        self.client.table("money").upsert(update_data).execute()

    def update_balance(self, user_id, amount, words=None):
        # Fetch current balance
        current_data = self.get_balance(user_id)
        current_balance = current_data["balance"] if isinstance(current_data, dict) else current_data
        new_balance = current_balance + amount

        # Update balance, time, and optional word
        self.set_balance(user_id, new_balance, words=words)
        return new_balance

    def get_words(self, user_id):
        data = self.client.table("money").select("words").eq("user_id", user_id).execute()
        if data.data:
            return data.data[0]["words"]
        return None

    def set_words(self, user_id, words):
        self.client.table("money").update({
            "words": words,
            "time": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", user_id).execute()

    def delete_database(self):
        self.client.table("money").delete().neq("user_id", 0).execute()

    def reset_currency(self):
        all_users = self.get_balance(all=True)
        for user in all_users:
            self.set_balance(user["user_id"], 0, words="reset")
