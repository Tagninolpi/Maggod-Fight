"""
Erstellen ungefähr in Zeile
Update game_save ungefähr in Zeile 540
Löschen ungefähr in Zeile
"""
import time

SAVE_TABLE_NAME = "saves"

import os
import sqlite3

from utils.abilities_tag import *
from utils.gameplay_tag import God, Effect
from utils.game_test_on_discord import gods

effects = [
    "posi_shield",
    "hep_shield",
    "ares_do_more_dmg",
    "aphro_charm",
    "zeus_stun",
    "athena_more_max_hp",
    "hades_ow_do_more_dmg",
    "cerberus_more_max_hp_per_visible_ally",
    "charon_invisible_duration",
    "hades_uw_shield",
    "tisi_freeze_timer",
    "alecto_get_more_dmg",
    "mega_do_less_dmg"
]


class Match_Loaded:
    """Represents a single Maggod Fight match."""
    def __init__(self, player1_id=None, player2_id=None):
        self.player1_id = player1_id    # str
        self.player1_name = "Player 1"  # str
        self.player2_id = player2_id    # str
        self.player2_name = "Player 2"  # str
        self.started = False            # bool?
        self.teams = {}                 # list in dict (player_id: team)
        self.gods = {}                  # unnecessary
        self.available_gods = []        # unnecessary
        self.next_picker = None         # unnecessary
        self.current_turn_player = None # str?
        self.turn_number = 0            # int
        self.teams_initialized = False  # bool (necessary?)
        self.game_phase = "Waiting for first player"  # Waiting for second player,ready, building, playing, finished
                                        # str

        self.current_attacking_team = None  # datatype: ???
        self.turn_state = {
            "current_player": None,
            "turn_number": 1
        }
        self.solo_mode = False              # bool
        self.turn_in_progress = False       # bool?


class DB_Manager:
    def __init__(self, db_name: str = "save", db_extension: str = "db", folder_path: str = "database/database"):
        self.db_file_name = f"{db_name}.{db_extension}"
        self.folder_path = folder_path
        self.conn = None
        self.cursor = None

        self.init()

    def init(self):
        if not os.path.exists(self.folder_path):
            os.mkdir(self.folder_path)

        self.conn = sqlite3.connect(f"{self.folder_path}/{self.db_file_name}")
        self.cursor = self.conn.cursor()

        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {SAVE_TABLE_NAME} (
                channel STRING PRIMARY KEY,
                player1 STRING,
                player1_team STRING,
                player2 STRING,
                player2_team STRING,
                current_turn_player_id STRING,
                turn_nr INTEGER,
                game_phase STRING,
                solo_mode BOOLEAN
            );
        """)

    def encrypt_team(self, player_team):
        encrypted_player_team = []

        encrypted_god = "a"
        gods_number = list(gods.keys())

        for god in player_team:
            encrypted_god += str(gods_number.index(god.name)).zfill(2)
            encrypted_god += str(god.hp).zfill(2)
            encrypted_god += str(god.max_hp).zfill(2)
            encrypted_god += str(god.dmg).zfill(2)
            encrypted_god += str(int(god.visible))
            encrypted_god += str(int(god.alive))

            effects_ = []
            for effect in god.effects.keys():
                effect_str = str(effects.index(effect))
                effect_str += "|"
                effect_str += str(god.effects[effect].value)
                effect_str += "|"
                effect_str += str(god.effects[effect].duration)
                effects_.append(effect_str)
            encrypted_god += "-".join(effects_)

            encrypted_player_team.append(encrypted_god)

        return ".".join(encrypted_player_team)

    def decrypt_team(self, team_string: str):
        team = []

        team_string = str(team_string)
        team_string = team_string.split(".")

        for god_string in team_string:
            god_string = god_string.removeprefix("a")
            god = gods[list(gods.keys())[int(god_string[:2])]]
            god.hp = int(god_string[2:4])
            god.max_hp = int(god_string[4:6])
            god.dmg = int(god_string[6:8])
            god.visible = bool(int(god_string[8]))
            god.alive = bool(int(god_string[9]))

            effects_ = god_string[10:]
            if effects_ != "":
                effects_ = effects_.split("-")

                for effect in effects_:
                    effect = effect.split("|")
                    name = effects[int(effect[0])]
                    value = int(effect[1])
                    duration = int(effect[2])

                    god.add_effect(name, value, duration)

            team.append(god)

        return team

    def create_game_save(self, channel, match):
        player1_id = match.player1_id
        player2_id = match.player2_id
        player1_team = match.teams[player1_id]
        player2_team = match.teams[player2_id]
        current_turn_player_id = match.turn_state["current_player"]
        turn_nr = match.turn_number
        game_phase = match.game_phase
        solo_mode = match.solo_mode

        player1_team_string = self.encrypt_team(player1_team)
        player2_team_string = self.encrypt_team(player2_team)

        self.cursor.execute(f"""
            INSERT INTO {SAVE_TABLE_NAME}(channel, player1, player1_team, player2, player2_team, current_turn_player_id, turn_nr, game_phase, solo_mode) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [channel, player1_id, player1_team_string, player2_id, player2_team_string, current_turn_player_id, turn_nr, game_phase, solo_mode])

        self.conn.commit()

    def update_game_save(self, channel, match):
        player1_id = match.player1_id
        player2_id = match.player2_id
        player1_team = match.teams[player1_id]
        player2_team = match.teams[player2_id]
        current_turn_player_id = match.turn_state["current_player"]
        turn_nr = match.turn_number

        player1_team_string = self.encrypt_team(player1_team)
        player2_team_string = self.encrypt_team(player2_team)

        self.cursor.execute(f"""
            UPDATE {SAVE_TABLE_NAME} SET player1_team=? WHERE channel=? AND player1=? AND player2=?
        """, [player1_team_string, channel, player1_id, player2_id])
        self.cursor.execute(f"""
            UPDATE {SAVE_TABLE_NAME} SET player2_team=? WHERE channel=? AND player1=? AND player2=?
        """, [player2_team_string, channel, player1_id, player2_id])
        self.cursor.execute(f"""
            UPDATE {SAVE_TABLE_NAME} SET current_turn_player_id=? WHERE channel=? AND player1=? AND player2=?
        """, [current_turn_player_id, channel, player1_id, player2_id])
        self.cursor.execute(f"""
            UPDATE {SAVE_TABLE_NAME} SET turn_nr=? WHERE channel=? AND player1=? AND player2=?
        """, [turn_nr, channel, player1_id, player2_id])

        self.conn.commit()

    def delete_game_save(self, channel, match):
        player1_id = match.player1_id
        player2_id = match.player2_id

        self.cursor.execute(f"""
            DELETE FROM {SAVE_TABLE_NAME} WHERE channel=? AND player1=? AND player2=?
        """, [channel, player1_id, player2_id])

        self.conn.commit()

    def load_all(self):
        data = self.cursor.execute(f"""
            SELECT * FROM {SAVE_TABLE_NAME}
        """)

        matches = {}

        for game in data:
            channel = game[0]
            player_1_id = game[1]
            player_1_team = self.decrypt_team(game[2])
            player_2_id = game[3]
            player_2_team = self.decrypt_team(game[4])
            current_turn_player_id = game[5]

            turn_nr = game[6]
            game_phase = game[7]
            solo_mode = game[8]
            turn_in_progress = False

            match = Match_Loaded(player_1_id, player_2_id)
            match.started = True
            match.teams = {player_1_id: player_1_team, player_2_id: player_2_team}
            match.turn_number = turn_nr
            match.game_phase = game_phase

            match.turn_state = {"current_player": current_turn_player_id, "turn_number": turn_nr}
            match.solo_mode = solo_mode
            match.turn_in_progress = turn_in_progress

            matches[channel] = match

        return matches

    def close(self):
        self.conn.close()

db_manager = DB_Manager()
