from dataclasses import dataclass
from typing import List, Dict, Union, Optional
import itertools
from models import Character, GuildMember

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

class RaidOptimizer:
    def __init__(self, members, raid_key):
        self.members = members # List[GuildMember]
        self.raid = RAID_DATA[raid_key]
        self.total_slots = self.raid.max_players
        self.required_supps = self.raid.required_supps

    def solve(self):
        # 1. 입장 가능 캐릭터 풀 구성
        pool = self._prepare_character_pool()

        # 2. 결과 저장을 위한 리스트 (1개 파티 구성 예시)
        # 사용된 캐릭터를 제외하며 재괴 호출하거나 순열을 생성한다.

        return self._find_best_party(pool)
    
    def _backtrack_solve(self, pool, current_result):
        # 필요한 파티 수가 모두 찼다면 결과 반환
        needed_parties = 2 if self.raid.max_players == 8 else 1 #예시
        if len(current_result) == needed_parties:
            return current_result
        
        # 조합 탐색
        for combo in itertools.combinations(pool, self.raid.max_players):
            if self._is_valid_party(list(combo)):
                # 사용한 캐릭터를 제외한 새로운 풀 생성
                remaining_pool = [c for c in pool if c not in combo]
                res = self._backtrack_solve(remaining_pool, current_result + [list(combo)])
                if res: return res
        return None # 가능한 조합이 없는 경우
    
    def _prepare_character_pool(self) -> List[Character]:
        pool = []
        for m in self.members:
            for char in m.characters.values():
                if char.item_level >= self.raid.required_level:
                    # 유저 ID를 추적하기 위해 임시 속성 부여(중복 방지용)
                    char.owner_id = m.discord_id
                    pool.append(char)
        return pool
    
    def _find_best_party(self, pool: List[Character]):
        # 최적의 1개 파티를 찾는 백트래킹
        best_party = []

        # 모든 가능한 조합 중 제약 조건을 만족하는 첫 번째 조합 반환
        for combo in itertools.combinations(pool, self.total_slots):
            if self._is_valid_party(list(combo)):
                return list(combo)
        
        # 만약 자리가 남는다면 '공팟'으로 채우는 로직 (Greedy)
        return self._fill_with_public(pool)
    
    def _is_valid_party(self, party: List[Character]) -> bool:
        # 규칙 1: 동일 유저 중복 불가
        owner_ids = [c.owner_id for c in party]
        if len(owner_ids) != len(set(owner_ids)): return False

        # 규칙 2: 서포터 수 확인 (Hybrid 포함)
        potential_supps = [c for c in party if c.user_set_role in ['서폿', '딜폿']]
        if len(potential_supps) < self.required_supps: return False

        # 규칙 3: 본캐 서폿 - 본캐 딜러 짝궁(5인 이상 시)
        main_supps = [c for c in party if c.is_main and c.user_set_role in ['서폿', '딜폿']]
        main_dps = [c for c in party if c.is_main and c.user_set_role == '딜러']

        # 규칙 4: 직업 중복 체크 (역할까지 고려)
        # (직업명, 역할) 튜플을 만들어 중복을 체크한다
        # job_roles = [(c.job, c.user_set_role) for c in party]
        # if len(job_roles) != len(set(job_roles)): return False

        # TODO 규칙 6: 사멸/ 비사별 구분

        if len(self.members) >= 5 and main_supps and not main_dps:
            return False
        
        return True
    
    def _fill_with_public(self, pool: List[Character]):
        # 8인 공대가 아닐 시 공팟 자리를 포함하여 반환하는 로직
        # TODO: 실제 구현시에는 부족한 Role을 계산하여 "공팟(서폿)" 등을 리스트에 추기

        pass

