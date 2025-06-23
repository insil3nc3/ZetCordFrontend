import httpx

from .token_manager import TokenManager
#
URL = "http://localhost:8000/"
timeout = httpx.Timeout(30.0, read=20.0)
#

token_manager = TokenManager()