import discord
from models import GuildMember
from database import Database
from config import MIN_ITEM_LEVEL, ENTROPY_CLASS, ROLE_EMOJIS, FLEXIBLE_ENTROPY_CLASS


class RoleSetupView(discord.ui.View):
    def __init__(self, member: GuildMember, db: Database):
        super().__init__(timeout=None)
        self.db = db
        self.member = member
        self.create_buttons()

    def create_buttons(self):
        # 유효한 캐릭터만 먼저 추출
        valid_chars = [
            (name, info) for name, info in self.member.characters.items() 
            if info.item_level >= MIN_ITEM_LEVEL
        ]

        # 캐릭터당 버튼이 1개일 수도 있고(타 직업), 2개일 수도 있음(브레이커 등)
        # 디스코드 한 줄(row)은 5칸의 point를 가짐. 이를 계산해서 row를 배치.
        current_row = 0
        current_width = 0

        for char_name, char_info in valid_chars:
            # 이 캐릭터가 차지할 너비 계산 (역할 버튼 1 + 사멸 버튼이 필요한 경우 1)
            needed_width = 2 if char_info.job in FLEXIBLE_ENTROPY_CLASS else 1
            
            # 현재 줄에 자리가 없으면 다음 줄로 넘김
            if current_width + needed_width > 5:
                current_row += 1
                current_width = 0
            
            if current_row > 4: break # 최대 5줄 제한 도달 시 중단

            # 1. 역할 변경 버튼
            btn_role = discord.ui.Button(
                label=f"{char_name}({char_info.user_set_role})",
                custom_id=f"role_{char_name}",
                style=discord.ButtonStyle.secondary,
                row=current_row
            )
            btn_role.callback = self.make_callback(char_name)
            self.add_item(btn_role)
            current_width += 1

            # 2. 사멸 선택 버튼 (FLEXIBLE 직업군만)
            if char_info.job in FLEXIBLE_ENTROPY_CLASS:
                is_ent = getattr(char_info, 'is_entropy', False)
                btn_entropy = discord.ui.Button(
                    label=f"└ {'사멸' if is_ent else '비사멸'}",
                    custom_id=f"entropy_{char_name}",
                    style=discord.ButtonStyle.primary if is_ent else discord.ButtonStyle.gray,
                    row=current_row
                )
                btn_entropy.callback = self.make_entropy_callback(char_name)
                self.add_item(btn_entropy)
                current_width += 1

    def make_callback(self, char_name):
        async def callback(interaction: discord.Interaction):
            # DPS -> Support -> Hybrid -> DPS 순환 구조
            char = self.member.characters[char_name]
            current = char.user_set_role

            role_map = {"딜러": "서폿", "서폿": "딜폿", "딜폿": "딜러"}
            # 현재 값이 map에 없으면 기본값 '딜러'로 시작
            next_role = role_map.get(current, "딜러")

            # 자동 사멸 판정 로직 (홀리나이트)
            # 딜러 혹은 딜폿을 선택했는데, 해당 직업이 딜러 일 때 사멸인 직업인 경우
            auto_entropy_classes = ['홀리나이트']
            is_entropy = getattr(char, 'is_entropy', False)

            if char.job in auto_entropy_classes:
                is_entropy = True if next_role in ["딜러", "딜폿"] else False # 홀나 딜러/ 딜폿은 무조건 사멸

            # 데이터 모델 업데이트
            self.member.update_role(char_name, next_role)
            char.is_entropy = is_entropy 
            
            # DB파일 업데이트
            self.db.update_character_role(interaction.user.id, char_name, next_role)

            # 사멸 여부도 함께 업데이트
            self.db.update_character_entropy(interaction.user.id, char_name, is_entropy)

            # UI 버튼 라벨 업데이트 후 메세지 수정
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.custom_id == f"role_{char_name}":
                        item.label = f"{char_name}({next_role})"

                    # 만약 브레이커/가나처럼 수동 사멸 선택 버튼이 따로 있다면 상태 업데이트
                    if item.custom_id == f"entropy_{char_name}":
                        # 홀리나이트 같은 경우 사멸 버튼의 가동성을 위해 자동 업데이트
                        entropy_label = "사멸" if is_entropy else "비사멸"
                        item.label = f"└ {entropy_label}"
                        item.style = discord.ButtonStyle.primary if is_entropy else discord.ButtonStyle.gray


            await interaction.response.edit_message(view=self)

        return callback
    
    def make_entropy_callback(self, char_name):
        async def callback(interaction: discord.Interaction):
            char = self.member.characters[char_name]
            new_status = not getattr(char, 'is_entropy', False)

            char.is_entropy = new_status
            self.db.update_character_entropy(interaction.user.id, char_name, new_status)

            for item in self.children:
                if isinstance(item, discord.ui.Button) and item.custom_id == f"entropy_{char_name}":
                    item.label = f"└ {'사멸' if new_status else '비사멸'}"
                    item.style = discord.ButtonStyle.primary if new_status else discord.ButtonStyle.gray

            await interaction.response.edit_message(view=self)
        return callback

class MemberSelectView(discord.ui.View):
    def __init__(self, all_members, raid, rounds, db):
        super().__init__(timeout=300)
        self.all_members = all_members
        self.raid = raid
        self.rounds = rounds
        self.db = db
        
        # 유저 선택 드롭다운 (ID와 본캐명을 매칭)
        options = [
            discord.SelectOption(
                label = m.main_char_name,
                value = str(m.discord_id)
            ) for m in all_members
        ]
        
        # 다중 선택 메뉴 (최대 참여 가능 인원 설정)
        self.select = discord.ui.Select(
            placeholder= "이번 품앗이에 참여할 본캐들을 선택하세요",
            min_values = 1,
            max_values = len(options),
            options = options
        )
        self.select.callback = self.select_callback
        self.add_item(self.select)
        
    async def select_callback(self, interaction: discord.Interaction):
        # 메세지를 보낸 사람만 조작 가능하게 하거나, 모두에게 공개된 채널에 결과 전송
        await interaction.response.defer()
        
        selected_ids = [int(v) for v in self.select.values]
        participating_members = [m for m in self.all_members if m.discord_id in selected_ids]
        
        # 3. 드디어 여기서 RaidOptimizer 호출
        from optimizer import RaidOptimizer
        optimizer = RaidOptimizer(participating_members, self.raid.value, total_rounds = self.rounds)
        result_rounds = optimizer.solve()
        
        if not result_rounds:
            await interaction.followup.send("❌ 조건에 맞는 조합을 찾을 수 없습니다. (캐릭터 부족 또는 레벨 미달)")
            return

        # 4. 결과 Embed 생성 
        embed = discord.Embed(
            title = f"🗡️ {self.raid.name} ({self.rounds}판) 매칭 완료",
            color = 0x2f3136
        )
        
        for r_idx, round_parties in enumerate(result_rounds, 1):
            for p_idx, party in enumerate(round_parties, 1):
                party_text = ""
                for char in party:
                    # 이모지 판정 로직 (config 활용)
                    if char.user_set_role == '서폿':
                        emoji = ROLE_EMOJIS['SUPPORT']
                    elif getattr(char, 'is_entropy', False) or any(e == char.job for e in ENTROPY_CLASS):
                        # DB의 is_entropy가 True이거나, 고정 사멸 직업군인 경우
                        emoji = ROLE_EMOJIS['DPS_ENTROPY']
                    else:
                        emoji = ROLE_EMOJIS['DPS_HITMASTER']
                        
                    party_text += f"{emoji} **{char.name}** | {char.job} ({char.item_level:.1f})\n"
                
                embed.add_field(
                    name = f"Round {r_idx} - {p_idx}번 파티",
                    value = party_text,
                    inline = False
                )
        # 결과는 ephermeral = False로 보내서 모두가 볼 수 있게 함
        await interaction.channel.send(embed = embed)