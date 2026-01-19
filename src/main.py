import discord
from discord import app_commands
from optimizer import RAID_DATA
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


@bot.tree.command(name="품앗이매칭", description="참여 인원을 선택하여 레이드 파티를 구성합니다.")
@app_commands.choices(raid=[
    app_commands.Choice(name = v.name, value = k) for k, v in RAID_DATA.items()
])
@app_commands.describe(판수 = "진행할 총 판수를 입력하세요 (예: 3)")

async def match(interaction: discord.Interaction, raid: app_commands.Choice[str], 판수: int):
    # 드롭다운은 선택하는 사람에게만 보이고 채널을 더럽히지 않도록 ephemaral = True 추천
    # 하지만 결과는 모두가 봐야 하므로 일단 defer만 한다.
    
    await interaction.response.defer(ephemeral=True)
    
    # 1. [중요] DB에서 저장된 모든 맴버 로드
    all_members = db.load_all_members()

    if not all_members:
        await interaction.followup.send("❌ 등록된 길드원이 없습니다. /등록을 먼저 해주세요.")
        return
    
    # 참여자 선택을 위한 View 생성
    # view.py MemberSelectView 클래스를 정의해야 한다.
    from views import MemberSelectView
    view = MemberSelectView(all_members, raid, 판수, db)
    
    await interaction.followup.send(
        f"✅ **{raid.name} ({판수}판)** 매칭 참여자를 선택해주세요.",
        view = view
    )

  

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

    tier_4_chars = [c for c in member.characters.values() if c.item_level >= 1640]

    from views import RoleSetupView
    view = RoleSetupView(member, db)
    
    await interaction.followup.send(
        f"✅ {대표캐릭명}님의 캐릭터 {len(tier_4_chars)}개가 매칭 대상으로 등록되었습니다.\n 아래 버튼을 눌러 역할을 설정하세요!",
        view=view
    )

bot.run(os.getenv('DISCORD_TOKEN'))