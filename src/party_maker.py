class PartyMaker:
    def __init__(self, participants):
        self.participants = participants 
    
    def generate_main_alt_parties(self, raid_level):
        """
        입력된 유저들의 캐릭터 중 raid_level을 만족하는 캐릭터를 선별하여 본캐 딜러 1~2명이 부캐 버스를 태우는 형태의 최적 순환 파티 조합 반환
        
        # TODO: 알고리즘 구현 (Greedy 혹은 셔플링 기반 최적화)
        """