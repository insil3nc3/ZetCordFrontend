import httpx

from .token_manager import TokenManager
# localhost:8000
URL = "https://00b3-185-65-202-122.ngrok-free.app/"
timeout = httpx.Timeout(30.0, read=20.0)
#

token_manager = TokenManager()