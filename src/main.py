import discord
from discord import app_commands
from optimizer import RaidOptimizer, RAID_DATA
from database import Database
import os
from dotenv import load_dotenv
from api import LostArkAPI
from database import GuildMember

load_dotenv()
db = Database()

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 명령어 동기화
        await self.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료")

bot = MyBot()


@bot.tree.command(name="품앗이매칭", description="레이드 파티를 구성합니다.")
@app_commands.choices(raid=[
    app_commands.Choice(name = v.name, value = k) for k, v in RAID_DATA.items()
])

async def match(interaction: discord.Interaction, raid: app_commands.Choice[str]):
    await interaction.response.defer()
    # [중요] DB에서 저장된 모든 맴버 로드
    # (주의: database.py에 load_all_members 메서드가 구현되어 있어야 함)
    members = db.load_all_members()

    if not members:
        await interaction.followup.send("❌ 등록된 길드원이 없습니다. /등록을 먼저 해주세요.")

    optimizer = RaidOptimizer(members, raid.value)
    result = optimizer.solve()

    if not result:
        await interaction.response.send_message("❌ 조건에 맞는 조합을 찾을 수 없습니다. (레벨 부족 등)")
        return
    
    # TODO: 결과를 예쁘게 포매팅하는 로직 (아래 3번 참고)
    await interaction.response.send_message(f"✅ {raid.name} 파티 구성 완료!")

@bot.tree.command(name="등록", description = "내 캐릭터 정보를 등록합니다.")

async def register(interaction: discord.Interaction, 대표캐릭명: str):
    await interaction.response.defer() # API 호출 시간이 걸리므로 응답 대기

    api_data = LostArkAPI.get_siblings(대표캐릭명)
    print(f"DEBUG API DATA: {api_data}")

    if not api_data:
        await interaction.followup.send("❌ 캐릭터 정보를 가져오지 못했습니다. 닉네임을 확인하세요.")
        return
    
    member = GuildMember.from_api_json(interaction.user.id, 대표캐릭명, api_data)
    db.save_member(member) # DB 저장

    from views import RoleSetupView
    await interaction.followup.send(
        f"✅ {대표캐릭명}님의 캐릭터 {len(member.characters)}개가 등록되었습니다. 아래 버튼을 눌러 역할을 설정하세요!",
        view=RoleSetupView(member)
    )

bot.run(os.getenv('DISCORD_TOKEN'))