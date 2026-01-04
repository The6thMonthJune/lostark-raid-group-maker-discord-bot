import sqlite3
import json
from typing import List
from models import GuildMember, Character

def load_all_members(self) -> List[GuildMember]:
    members = []
    with self.conn:
        # 1. 모든 유저 가져오기
        user_rows = self.conn.execute("SELECT discord_id, main_char FROM users").fetchall()

        for u_id, main_char in user_rows:
            member = GuildMember(discord_id=u_id, main_char_name=main_char)

            # 2. 해당 유저의 캐릭터들 가져오기
            char_rows = self.conn.execute(
                "SELECT name, job, level, role, is_main FROM characters WHERE"
            ).fetchall()

            for name, job, level, role, is_main in char_rows:
                member.characters[name] = Character(
                    name = name, job = job, item_level = level,
                    user_set_role = role, is_main = bool(is_main)
                )
            member.append(member)
        return members


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('quild_bot.db')
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS users
                                (discord_id INTEGER PRIMARY KEY, main_char TEXT)''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS characters
                                (name TEXT PRIMARY KEY, owner_id INTEGER, job TEXT,
                                level REAL, role TEXT, is_main INTEGER)''')
        
    def save_member(self, member):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?)",
                              (member.discord_id, member.main_char_name))
            for char in member.characters.values():
                self.conn.execute("INSERT OR REPLACE INTO characters VALUES (?, ?, ?, ?, ?, ?)",
                                  (char.name, member.discord_id, char.job,
                                   char.item_level, char.user_set_role, int(char.is_main)))