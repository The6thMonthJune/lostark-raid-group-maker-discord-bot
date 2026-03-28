"""
테스트용 길드원 DB 등록 스크립트
사용법: src 폴더에서 실행
  python seed_members.py
"""

from api import LostArkAPI
from database import Database
from models import GuildMember

# ✏️ 테스트할 서버의 Discord 길드 ID를 입력하세요
# (Discord 서버 우클릭 → 서버 ID 복사, 개발자 모드 활성화 필요)
TEST_GUILD_ID = 123456789012345678

# ✏️ 여기에 등록할 대표 캐릭터명 목록을 입력하세요
MAIN_CHARS = [
    "이코옹",
    "파슬이",
    "민트키리모찌",
]

def seed():
    db = Database()
    success, fail = 0, 0

    for idx, char_name in enumerate(MAIN_CHARS):
        fake_discord_id = 900000 + idx  # 테스트용 임시 Discord ID
        print(f"[{idx+1}/{len(MAIN_CHARS)}] {char_name} 등록 중...", end=" ")

        api_data = LostArkAPI.get_siblings(char_name)
        if not api_data:
            print("❌ API 실패 (캐릭터명 확인 필요)")
            fail += 1
            continue

        member = GuildMember.from_api_json(fake_discord_id, char_name, api_data)
        tier4 = [c for c in member.characters.values() if c.item_level >= 1640]
        db.save_member(member, TEST_GUILD_ID)

        print(f"✅ 완료 (티어4 캐릭터 {len(tier4)}개)")
        success += 1

    print(f"\n등록 완료: {success}명 성공 / {fail}명 실패")

if __name__ == "__main__":
    seed()
