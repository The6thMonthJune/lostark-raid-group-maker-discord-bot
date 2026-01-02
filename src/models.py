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

    @classmethod
    def determine_default_role(cls, job: str) -> str:
        """
        직업명을 보고 기본 역할을 추측한다.
        """
        support_jobs = ['바드', '도화가', '홀라나이트', '발키리']
        return 'Support' if job in support_jobs else 'DPS'

@dataclass
class GuildMember:
    discord_id: int
    main_char_name: str
    # 캐릭터 이름을 Key로, Character 객체를 Value로
    characters: Dict[str, Character] = field(default_factory=dict)

    def update_role(self, char_name:str, new_role: str):
        if char_name in self.characters:
            self.characters[char_name].user_set_role = new_role

    @classmethod
    def from_api_json(cls, discord_id: int, main_char_name: str, api_data: List[dict]):
        # 로아 API의 Siblings 호출 결과(JSON 리스트)를 받아
        # GuildMember 객체와 그 하위 Character 객체들을 생성한다.
        member = cls(discord_id = discord_id, main_char_name = main_char_name)

        for char_data in api_data:
            name = char_data['CharacterName']
            job = char_data['CharacterClassName']
            level = float(char_data['ItemMaxLevel'].replace(',',''))

            #본캐 여부 판단(입력받은 대표 캐릭터명과 일치하는지)
            is_main = (name == main_char_name)

            # 기본 역할 추측
            default_role = Character.determine_default_role(job)

            # Character 객체 생성 및 추가
            member.characters[name] = Character(
                name = name,
                job = job,
                item_level = level,
                user_set_role = default_role,
                is_main = is_main
            )
        return member
"""
    @classmethod
    def from_api_json(cls, data: dict):
        # API 응답에서 직업군에 따라 딜/서폿 분류 로직 포함
        support_jobs = []
"""