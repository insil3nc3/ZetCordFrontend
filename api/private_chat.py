import asyncio

import httpx
from api.common import URL, token_manager, timeout
from api.auth import refresh_tokens

API_URL = URL + "chats"


async def create_chat(user_unique_name: str):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{API_URL}/private",
                params={"user2_unique_name": user_unique_name},
                headers=headers
            )

            if response.status_code == 200 or response.status_code == 400:
                return response.json()
            elif response.status_code == 401:  # Токен просрочен
                await refresh_tokens()  # Обновление токенов
                headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"

                # Повторный запрос с обновлённым токеном
                response = await client.post(
                    f"{API_URL}/private",
                    json={"user2_unique_name": user_unique_name},
                    headers=headers
                )

                if response.status_code == 200 or response.status_code == 400:
                    return response.json()
                else:
                    return {
                        "error": f"Unauthorized even after token refresh. Code: {response.status_code}, Detail: {response.text}"}
            else:
                return {"error": f"HTTP error: {response.status_code}, Detail: {response.text}"}
        except httpx.RequestError as e:
            return {"error": f"{e}"}

