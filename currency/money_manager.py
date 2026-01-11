from supabase import create_client
from datetime import datetime, timezone
import os


class MoneyManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client = create_client(url, key)

    # ----------------- BALANCE -----------------
    def get_balance(self, user_id=None, all=False):
        if all:
            data = self.client.table("money").select("user_id, balance, words, player_time").execute()
            return data.data

        data = self.client.table("money").select("balance, words, player_time").eq("user_id", user_id).execute()
        if not data.data:
            self.client.table("money").insert({
                "user_id": user_id,
                "balance": 0,
                "words": "none",
                "player_time": ""
            }).execute()
            return {"balance": 0, "words": "none", "player_time": ""}
        return data.data[0]

    def set_balance(self, user_id, value, words=None):
        update_data = {
            "user_id": user_id,
            "balance": value,
        }
        if words is not None:
            update_data["words"] = words

        self.client.table("money").upsert(update_data).execute()

    def update_balance(self, user_id, amount, words=None):
        current_data = self.get_balance(user_id)
        current_balance = current_data["balance"] if isinstance(current_data, dict) else current_data
        new_balance = current_balance + amount
        self.set_balance(user_id, new_balance, words=words)
        return new_balance
        # ----------------- ADMIN -----------------
    def delete_database(self):
        self.client.table("money").delete().neq("user_id", 0).execute()

    def reset_currency(self):
        all_users = self.get_balance(all=True)
        for user in all_users:
            self.client.table("money").update({
                "balance": 0,
                "words": "reset",
                "player_time": "",
            }).eq("user_id", user["user_id"]).execute()
    # ----------------- WORDS -----------------



    # ----------------- PLAYER_TIME (rate limit) -----------------

    def get_player_times(self, user_id):
        data = self.client.table("money").select("player_time").eq("user_id", user_id).execute()
        if not data.data or not data.data[0].get("player_time"):
            return []

        times = []
        for t in data.data[0]["player_time"].split("!"):
            try:
                times.append(datetime.fromisoformat(t))
            except Exception:
                continue
        return times


    def add_player_guess_time(self, user_id):
        times = self.get_player_times(user_id)
        times.append(datetime.now(timezone.utc))
        self.set_player_times(user_id, times)


    def check_guess_rate_limit(self, user_id, max_guesses=10, window_seconds=600):
        """
        Returns:
        (can_play: bool, wait_seconds: int)
        """
        now = datetime.now(timezone.utc)
        times = self.get_player_times(user_id)

        # Remove old timestamps
        valid_times = [
            t for t in times
            if (now - t).total_seconds() <= window_seconds
        ]

        # Save cleaned list
        self.set_player_times(user_id, valid_times)

        if len(valid_times) >= max_guesses:
            oldest = min(valid_times)
            wait_seconds = int(
                window_seconds - (now - oldest).total_seconds()
            )
            return False, max(wait_seconds, 1)

        return True, 0
