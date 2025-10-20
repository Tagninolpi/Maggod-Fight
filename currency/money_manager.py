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
            data = self.client.table("money").select("user_id, balance, time, words, player_time").execute()
            return data.data

        data = self.client.table("money").select("balance, time, words, player_time").eq("user_id", user_id).execute()
        if not data.data:
            self.client.table("money").insert({
                "user_id": user_id,
                "balance": 0,
                "time": datetime.now(timezone.utc).isoformat(),
                "words": "none",
                "player_time": ""
            }).execute()
            return {"balance": 0, "time": datetime.now(timezone.utc).isoformat(), "words": "none", "player_time": ""}
        return data.data[0]

    def set_balance(self, user_id, value, words=None):
        update_data = {
            "user_id": user_id,
            "balance": value,
            "time": datetime.now(timezone.utc).isoformat()
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

    # ----------------- WORDS -----------------
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

    # ----------------- PLAYER_TIME -----------------
    def get_player_time(self, user_id):
        """Return the raw 'player_time' string for a given player."""
        data = self.client.table("money").select("player_time").eq("user_id", user_id).execute()
        if data.data and data.data[0].get("player_time"):
            return data.data[0]["player_time"]
        return ""

    def set_player_time(self, user_id, player_time_str: str):
        """Overwrite the entire 'player_time' field with a new string."""
        self.client.table("money").update({
            "player_time": player_time_str,
            "time": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", user_id).execute()

    def add_player_guess_time(self, target_user_id, guesser_id):
        """
        Append a new 'guesser:timestamp' entry to target user's player_time.
        Example: '12345:2025-10-19T15:20:00;67890:2025-10-19T15:22:10'
        """
        current = self.get_player_time(target_user_id)
        now = datetime.now(timezone.utc).isoformat()
        new_entry = f"{guesser_id}:{now}"
        updated = f"{current};{new_entry}" if current else new_entry

        self.client.table("money").update({
            "player_time": updated,
            "time": now
        }).eq("user_id", target_user_id).execute()

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
                "time": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user["user_id"]).execute()
    
    def get_player_times(self, user_id):
        """Return dict of {player_id: datetime} for the given user's word"""
        data = self.client.table("money").select("player_time").eq("user_id", user_id).execute()
        if not data.data or not data.data[0].get("player_time"):
            return {}
        text = data.data[0]["player_time"]
        pairs = [p for p in text.split(";") if p.strip()]
        result = {}
        for pair in pairs:
            try:
                pid, t = pair.split(":")
                result[int(pid)] = datetime.fromisoformat(t)
            except Exception:
                continue
        return result

    def set_player_times(self, user_id, player_times):
        """player_times is a dict {player_id: datetime}"""
        text = ";".join(f"{pid}:{t.isoformat()}" for pid, t in player_times.items())
        self.client.table("money").update({"player_time": text}).eq("user_id", user_id).execute()

    def update_player_time(self, word_owner_id, player_id):
        """Set or update one player's cooldown time"""
        player_times = self.get_player_times(word_owner_id)
        player_times[player_id] = datetime.now(timezone.utc)
        self.set_player_times(word_owner_id, player_times)

    def can_player_guess(self, word_owner_id, player_id, cooldown_minutes=5):
        """Check if a player can guess another player’s word based on cooldown"""
        player_times = self.get_player_times(word_owner_id)
        now = datetime.now(timezone.utc)
        if player_id not in player_times:
            return True, 0
        last_time = player_times[player_id]
        elapsed = (now - last_time).total_seconds() / 60
        if elapsed >= cooldown_minutes:
            return True, 0
        else:
            return False, round(cooldown_minutes - elapsed, 1)
