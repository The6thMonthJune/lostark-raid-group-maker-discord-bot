import sqlite3
import json
import os
from typing import List
from models import GuildMember, Character

_DB_PATH = os.path.join(os.path.dirname(__file__), "guild_bot.db")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(_DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # 유저 테이블 이름  (이름: users)
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS users
                                (discord_id INTEGER PRIMARY KEY, main_char TEXT)"""
            )
            # 캐릭터 테이블 (이름: characters)
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS characters
                                (name TEXT PRIMARY KEY, owner_id INTEGER, job TEXT,
                                level REAL, role TEXT, is_main INTEGER, is_entropy INTEGER)"""
            )
        self.conn.commit()

    def save_member(self, member):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO users VALUES (?, ?)",
                (member.discord_id, member.main_char_name),
            )
            for char in member.characters.values():
                is_ent = 1 if getattr(char, "is_entropy", False) else 0
                self.conn.execute(
                    "INSERT OR REPLACE INTO characters VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        char.name,
                        member.discord_id,
                        char.job,
                        char.item_level,
                        char.user_set_role,
                        int(char.is_main),
                        is_ent,
                    ),
                )


    def load_all_members(self):
        cur = self.conn.cursor()
        self.cursor.execute("SELECT discord_id, main_char FROM users")
        rows = self.cursor.fetchall()

        members_list = []  # 리스트 이름을 확실하게 members_list로 설정
        for row in rows:
            discord_id, main_char_name = row
            # 개별 멤버 객체 생성
            member_obj = GuildMember(discord_id, main_char_name)

            # 해당 멤버의 캐릭터들도 로드하여 객체에 채워줌
            cur.execute(
                "SELECT name, job, level, role, is_main, is_entropy FROM characters WHERE owner_id = ?",
                (discord_id,),
            )
            char_rows = cur.fetchall()
            for c_row in char_rows:
                member_obj.characters[c_row[0]] = Character(
                    name=c_row[0],
                    job=c_row[1],
                    item_level=c_row[2],
                    user_set_role=c_row[3],
                    is_main=bool(c_row[4]),
                    is_entropy=bool(c_row[5]),
                )

            members_list.append(member_obj)  # 리스트에 객체 추가

        return members_list

    def update_character_role(self, discord_id: int, char_name: str, new_role: str):
        with self.conn:
            self.conn.execute(
                """
                        UPDATE characters
                        SET role = ?
                        WHERE owner_id = ? AND name = ?
                          """,
                (new_role, discord_id, char_name),
            )

    def update_character_entropy(
        self, discord_id: int, char_name: str, is_entropy: bool
    ):
        with self.conn:
            self.conn.execute(
                """
                UPDATE characters
                SET is_entropy = ?
                WHERE owner_id = ? AND name =?
                """,
                (int(is_entropy), discord_id, char_name),
            )
