import discord
from models import GuildMember
from database import Database
from config import MIN_ITEM_LEVEL, ENTROPY_CLASS, ROLE_EMOJIS, FLEXIBLE_ENTROPY_CLASS, SUPPORT_CLASSES


class RoleSetupView(discord.ui.View):
    def __init__(self, member: GuildMember, db: Database):
        super().__init__(timeout=None)
        self.db = db
        self.member = member
        self.create_buttons()


    def create_buttons(self):
            valid_chars = [
                (name, info) for name, info in self.member.characters.items() 
                if info.item_level >= MIN_ITEM_LEVEL
            ]

            current_row = 0
            current_width = 0
        
            for char_name, char_info in valid_chars:
                is_support_class = char_info.job in SUPPORT_CLASSES
                is_flexible = char_info.job in FLEXIBLE_ENTROPY_CLASS
                is_holy_knight = char_info.job == '홀리나이트'

                # --- CASE 1: 사멸/비사멸 선택 캐릭터 (항상 새로운 줄 시작) ---
                if is_flexible:
                    # 현재 줄에 이미 버튼이 있다면 줄 바꿈
                    if current_width > 0:
                        current_row += 1

                    if current_row > 4: break # 디스코드 최대 5행 제한

                    # [캐릭터명 버튼]
                    self.add_item(discord.ui.Button(
                        label=char_name,
                        custom_id=f"role_{char_name}",
                        style=discord.ButtonStyle.secondary,
                        row=current_row,
                        disabled=True
                    ))

                    # [└ 사멸/비사멸 버튼]
                    is_ent = getattr(char_info, 'is_entropy', False)
                    btn_entropy = discord.ui.Button(
                        label=f"└ {'사멸' if is_ent else '비사멸'}",
                        custom_id=f"entropy_{char_name}",
                        style=discord.ButtonStyle.primary if is_ent else discord.ButtonStyle.secondary,
                        row=current_row
                    )
                    btn_entropy.callback = self.make_entropy_callback(char_name)
                    self.add_item(btn_entropy)

                    # 사멸 캐릭터는 한 줄을 점유하므로 강제 줄 바꿈 설정
                    current_row += 1
                    current_width = 0
                    continue # 다음 캐릭터로 이동 (아래의 else 로직을 타지 않게 함)

                # --- CASE 1.5: 홀리나이트 (역할 버튼 + 사멸/비사멸 버튼) ---
                elif is_holy_knight:
                    if current_width + 2 > 5:
                        current_row += 1
                        current_width = 0

                    if current_row > 4: break

                    is_in_dps_mode = char_info.user_set_role in ['딜러', '딜폿']
                    is_ent = getattr(char_info, 'is_entropy', False)

                    btn_role = discord.ui.Button(
                        label=f"{char_name}({char_info.user_set_role})",
                        custom_id=f"role_{char_name}",
                        style=discord.ButtonStyle.secondary,
                        row=current_row,
                    )
                    btn_role.callback = self.make_callback(char_name)
                    self.add_item(btn_role)

                    btn_entropy = discord.ui.Button(
                        label=f"└ {'사멸' if (is_in_dps_mode and is_ent) else '비사멸'}",
                        custom_id=f"entropy_{char_name}",
                        style=discord.ButtonStyle.primary if (is_in_dps_mode and is_ent) else discord.ButtonStyle.secondary,
                        row=current_row,
                        disabled=not is_in_dps_mode
                    )
                    btn_entropy.callback = self.make_entropy_callback(char_name)
                    self.add_item(btn_entropy)

                    current_width += 2
                    continue

                # --- CASE 2: 일반 캐릭터 (한 줄에 최대한 많이 배치) ---
                else:
                    if current_width + 1 > 5:
                        current_row += 1
                        current_width = 0
                    
                    if current_row > 4: break
                
                    display_label = f"{char_name}({char_info.user_set_role})" if is_support_class else char_name
                    btn_role = discord.ui.Button(
                        label=display_label,
                        custom_id=f"role_{char_name}",
                        style=discord.ButtonStyle.secondary,
                        row=current_row,
                        disabled=not is_support_class
                    )
                    if is_support_class:
                        btn_role.callback = self.make_callback(char_name)
                    
                    self.add_item(btn_role)
                    current_width += 1
            
            # --- 완료 버튼 배치 ---
            # 공간이 남으면 같은 줄에, 없으면 다음 줄에 (최대 4행)
            if current_width + 1 > 5:
                current_row += 1
            
            target_row = min(current_row, 4)

            done_btn = discord.ui.Button(
                label="설정 완료",
                style=discord.ButtonStyle.success,
                row=target_row,
                custom_id="setup_done"
            )

            async def done_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(
                    content="✅ 모든 설정이 DB에 저장되었습니다!",
                    view=None
                )
            
            done_btn.callback = done_callback
            self.add_item(done_btn)

    def make_callback(self, char_name):
        async def callback(interaction: discord.Interaction):
            char = self.member.characters[char_name]
            current = char.user_set_role

            if char.job in SUPPORT_CLASSES:
                role_map = {"딜러": "서폿", "서폿": "딜폿", "딜폿": "딜러"}
                next_role = role_map.get(current, "딜러")
            else:
                return

            is_entropy = getattr(char, 'is_entropy', False)
            # 홀리나이트가 서폿으로 전환되면 사멸 상태 초기화
            if char.job == '홀리나이트' and next_role == '서폿':
                is_entropy = False

            self.member.update_role(char_name, next_role)
            char.is_entropy = is_entropy
            self.db.update_character_role(interaction.user.id, char_name, next_role)
            self.db.update_character_entropy(interaction.user.id, char_name, is_entropy)

            # UI 즉시 업데이트
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    if item.custom_id == f"role_{char_name}":
                        item.label = f"{char_name}({next_role})"
                    if item.custom_id == f"entropy_{char_name}":
                        in_dps_mode = next_role in ['딜러', '딜폿']
                        item.disabled = not in_dps_mode
                        item.label = f"└ {'사멸' if is_entropy else '비사멸'}"
                        item.style = discord.ButtonStyle.primary if is_entropy else discord.ButtonStyle.secondary

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
                    item.style = discord.ButtonStyle.primary if new_status else discord.ButtonStyle.secondary

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
                description =f"ID: {m.discord_id}",
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
            description= f"선택된 인원: {len(participating_members)}명\n구성된 파티: {len(result_rounds[0])}개",
            color = 0x2f3136
        )
        
        for r_idx, round_parties in enumerate(result_rounds, 1):
            round_text = ""
            for p_idx, party in enumerate(round_parties, 1):
                party_line = [f"**[파티 {p_idx}]**"]
                for char in party:
                    # 이모지 판정 로직 (config 활용)
                    if char.user_set_role == '서폿':
                        emoji = ROLE_EMOJIS['SUPPORT']
                    elif getattr(char, 'is_entropy', False) or any(e == char.job for e in ENTROPY_CLASS):
                        # DB의 is_entropy가 True이거나, 고정 사멸 직업군인 경우
                        emoji = ROLE_EMOJIS['DPS_ENTROPY']
                    else:
                        emoji = ROLE_EMOJIS['DPS_HITMASTER']

                    party_line.append(f"{emoji} {char.name}")

                round_text += " | ".join(party_line) + "\n"

            embed.add_field(
                name = f"━━ Round {r_idx} ━━",
                value = round_text,
                inline = False
            )
        embed.set_footer(text= "💡 매칭이 마음에 들지 않으면 다시 시도해 주세요.")
        # 결과는 ephermeral = False로 보내서 모두가 볼 수 있게 함
        await interaction.channel.send(content = f"{interaction.user.mention} 님이 매칭을 완료했습니다!", embed= embed)