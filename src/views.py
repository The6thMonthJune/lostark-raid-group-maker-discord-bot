import discord
from models import GuildMember

class RoleSetupView(discord.ui.View):
    def __init__(self, member: GuildMember):
        super().__init__(timeout = None)
        self.member = member
        self.create_buttons()

    def create_buttons(self):
        # 캐릭터별로 현재 상태를 보여주는 버튼 생성 (예시로 1개만 표현)
        for char_name, char_info in self.member.characters.items():
            if char_info.item_level >= 1690: # 2막 하드 이상 캐릭터만 노출
                button = discord.ui.Button(
                    label = f"{char_name}({char_info.user_set_role})",
                    custom_id=f"role_{char_name}",
                    style=discord.ButtonStyle.secondary
                )
                button.callback = self.make_callback(char_name)
                self.add_item(button)
    
    def make_callback(self, char_name):
        async def callback(interaction: discord.Interaction):
            # DPS -> Support -> Hybrid -> DPS 순환 구조
            current = self.member.characters[char_name].user_set_role
            next_role = {'딜러':'서폿', '서폿':'딜폿', '딜폿':'딜러'}[current]
            self.member.update_role(char_name, next_role)

            # 버튼 라벨 업데이트 후 메세지 수정
            for item in self.children:
                if item.custom_id == f"role_{char_name}":
                    item.label = f"{char_name}({next_role})"
            
            await interaction.response.edit_message(view=self)
        return callback