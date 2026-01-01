from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Character:
    name: str
    job: str
    item_level: float
    user_set_role: str
    """
    사용자가 설정한 역할: DPS, Support, Hybrid
    초기값은 API 기반으로 추측하되, 사용자가 수정한 값을 우선시함.
    """
    is_main: bool = False # 본캐 여부

@dataclass
class GuildMember:
    discord_id: int
    main_char_name: str
    # 캐릭터 이름을 Key로, Character 객체를 Value로
    characters: Dict[str, Character] = field(default_factory=dict)

    def update_role(self, char_name:str, new_role: str):
        if char_name in self.characters:
            self.characters[char_name].user_set_role = new_role

"""
    @classmethod
    def from_api_json(cls, data: dict):
        # API 응답에서 직업군에 따라 딜/서폿 분류 로직 포함
        support_jobs = []
"""