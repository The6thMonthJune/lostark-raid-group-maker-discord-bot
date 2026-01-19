from dataclasses import dataclass

MIN_ITEM_LEVEL = 1640.0

ROLE_EMOJIS ={
    'DPS_HITMASTER': '🏹', # 타대/비사멸 딜러
    'DPS_ENTROPY':'⚔️', # 사멸 딜러
    'SUPPORT': '✨'
}
# 사멸/비사멸 공유 직업: 브레이커, 가디언나이트, 데모닉
ENTROPY_CLASS = ['디스트로이어', '워로드', '슬레이어', '스트라이커', 
                 '배틀마스터', '인파이터', '창술사', '데빌헌터', 
                 '블레이드','리퍼',]

FLEXIBLE_ENTROPY_CLASS = ['브레이커', '가디언나이트']

ENTROPY_SYNERGY_CLASS = ['워로드', '블레이드']

@dataclass
class RaidInfo:
    name: str
    required_level: float
    max_players: int

    @property
    def required_supps(self) -> int:
        # 인원수에 따른 서포터 수를 반환 (4인 1명, 8인 2명)
        return self.max_players // 4
    
#관리데이터
RAID_DATA = {
    "세르카 나메": RaidInfo("세르카 나메", 1740.00, 4),
    "세르카 하드": RaidInfo("세르카 하드", 1730.00, 4),
    "세르카 노말": RaidInfo("세르카 노말", 1710.00, 4),
    "종막 하드": RaidInfo("카제로스 하드", 1730.00, 8),
    "종막 노말": RaidInfo("카제로스 노말", 1710.00, 8),
    "4막 하드": RaidInfo("아르모체 하드", 1720.00, 8),
    "4막 노말": RaidInfo("아르모체 노말", 1700.00, 8),
    "3막 하드": RaidInfo("모르둠 하드", 1700.00, 8),
    "3막 노말": RaidInfo("모르둠 노말", 1680.00, 8),
    "2막 하드": RaidInfo("아브 하드", 1690.00, 8),
    "2막 노말": RaidInfo("아브 노말", 1670.00, 8),
    "베히모스": RaidInfo("베히모스", 1640.00, 16),    
}