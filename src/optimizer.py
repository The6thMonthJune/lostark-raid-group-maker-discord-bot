import itertools
from typing import List, Dict, Optional
from models import Character, GuildMember
from config import RAID_DATA, ENTROPY_CLASS, ENTROPY_SYNERGY_CLASS

class RaidOptimizer:
    def __init__(self, members: List[GuildMember], raid_key: str, total_rounds: int):
        self.members = members
        self.raid = RAID_DATA[raid_key]
        self.total_rounds = total_rounds

    def solve(self):
        """전체 라운드 매칭을 시도하는 메인 함수"""
        pool = self._prepare_character_pool()
        return self._backtrack_rounds(pool, 0, [])

    def _prepare_character_pool(self) -> List[Character]:
        pool = []
        for m in self.members:
            for char in m.characters.values():
                if char.item_level >= self.raid.required_level:
                    char.owner_id = m.discord_id  # 매칭용 owner_id 주입
                    pool.append(char)
        return pool

    def _backtrack_rounds(self, pool: List[Character], current_round: int, result_so_far: List):
        if current_round == self.total_rounds:
            return result_so_far

        # 이번 라운드에 참여할 max_players 명을 뽑는 조합 탐색
        for combo in itertools.combinations(pool, self.raid.max_players):
            # 8인/16인 등을 파티(4인 단위)로 최적 분할 시도
            raid_structure = self._optimize_raid_structure(list(combo))
            
            if raid_structure:
                remaining_pool = [c for c in pool if c not in combo]
                res = self._backtrack_rounds(remaining_pool, current_round + 1, result_so_far + [raid_structure])
                if res: return res
        return None

    def _optimize_raid_structure(self, chars: List[Character]) -> Optional[List[List[Character]]]:
        """선택된 인원을 규칙에 맞게 4인 파티들로 쪼개고 시너지를 최적화함"""
        # 규칙 1: 동일 유저 중복 불가 (공격대 전체 기준)
        owner_ids = [c.owner_id for c in chars]
        if len(owner_ids) != len(set(owner_ids)): return None

        # 4인 레이드일 경우
        if self.raid.max_players == 4:
            return [chars] if self._is_valid_party(chars) else None

        # 8인 레이드일 경우 (최적 시너지 분할 탐색)
        elif self.raid.max_players == 8:
            best_split = None
            max_score = -1
            
            for combo in itertools.combinations(chars, 4):
                p1 = list(combo)
                p2 = [c for c in chars if c not in combo]
                
                if self._is_valid_party(p1) and self._is_valid_party(p2):
                    score = self._calculate_synergy_score(p1) + self._calculate_synergy_score(p2)
                    if score > max_score:
                        max_score = score
                        best_split = [p1, p2]
            return best_split

        # 16인(베히모스) 등은 연산량 관계상 단순 분배 (그리디)
        else:
            return self._simple_split(chars)

    def _is_valid_party(self, party: List[Character]) -> bool:
        # 규칙 2: 최소 서폿 1명 (딜폿 포함)
        if not any(c.user_set_role in ['서폿', '딜폿'] for c in party): return False

        # 규칙 4: 직업 중복 체크 (직업명 + 역할 튜플로 딜러/서폿 발키리 허용)
        job_roles = [(c.job, c.user_set_role) for c in party]
        if len(job_roles) != len(set(job_roles)): return False

        # 규칙 3: 본캐 서폿-딜러 짝궁 (5인 이상 시)
        if len(self.members) >= 5:
            main_supps = [c for c in party if c.is_main and c.user_set_role in ['서폿', '딜폿']]
            main_dps = [c for c in party if c.is_main and c.user_set_role == '딜러']
            if main_supps and not main_dps: return False

        return True

    def _calculate_synergy_score(self, party: List[Character]) -> int:
        """사멸 시너지(워로드, 블레이드) 배정 점수 계산"""
        score = 0
        has_synergy = any(c.job in ENTROPY_SYNERGY_CLASS for c in party)
        entropy_dps = [c for c in party if self._is_entropy_candidate(c)]
        
        if has_synergy:
            score += len(entropy_dps) * 10  # 사멸 딜러당 10점
            # 규칙 5: 본캐 사멸 딜러에게 시너지 몰아주기 가점
            score += sum(5 for c in entropy_dps if c.is_main)
            
        return score

    def _is_entropy_candidate(self, char: Character) -> bool:
        # DB 저장된 is_entropy 값 우선, 없으면 config의 고정 직업군 확인
        if getattr(char, 'is_entropy', False): return True
        return char.job in ENTROPY_CLASS and char.user_set_role in ["딜러", "딜폿"]

    def _simple_split(self, chars: List[Character]):
        # 16인용 간단 분할 로직 (서폿 우선 분배)
        supps = [c for c in chars if c.user_set_role in ['서폿', '딜폿']]
        dps = [c for c in chars if c.user_set_role not in ['서폿', '딜폿']]
        
        if len(supps) < self.raid.required_supps: return None
        
        parties = [[] for _ in range(self.raid.max_players // 4)]
        for i, s in enumerate(supps[:len(parties)]):
            parties[i].append(s)
        
        all_dps = supps[len(parties):] + dps
        for i, d in enumerate(all_dps):
            parties[i % len(parties)].append(d)
        return parties