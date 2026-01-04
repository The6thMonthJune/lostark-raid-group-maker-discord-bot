import requests
import os
from dotenv import load_dotenv

load_dotenv()

class LostArkAPI:
    BASE_URL = "https://developer-lostark.game.onstove.com"
    HEADERS = {
        'accept' : 'application/json',
        'authorization' : f"bearer {os.getenv('LOSTARK_API_KEY')}"
    }

    @classmethod
    def get_siblings(cls, character_name):
        url = f"{cls.BASE_URL}/characters/{character_name}/siblings/"
        response = requests.get(url, headers=cls.HEADERS)
        return response.json() if response.status_code == 200 else None