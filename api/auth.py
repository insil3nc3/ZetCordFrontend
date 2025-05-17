import asyncio

import httpx
from api.common import token_manager, URL, timeout

API_URL = URL+"auth"

async def request_code(email: str):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url=f"{API_URL}/request_code", params={"email": email})
            if response.status_code == 200:
                response_data = response.json()
                return response_data
            else:
                return {"request error": f"Ошибка запроса кода: {response.status_code}, {response.text}"}
        except httpx.RequestError as e:
            return {"request error": f"error while requesting the code: {e}"}

async def register(email: str, password: str, code: int):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url=f"{API_URL}/register",
                json={"email": email, "password": password},
                params={"code": code}
            )

            if response.status_code == 201:
                data = response.json()
                token_manager.set_access_token(data.get("access_token"))
                token_manager.set_refresh_token(response.cookies.get("refresh_token"))
                return {"detail": "Successfully registered!"}
            else:
                return {"request error": f"Ошибка регистрации: {response.status_code}, {response.text}"}
        except httpx.RequestError as e:
            return {"request error": f"error while requesting the code: {e}"}

async def login(email: str, password: str):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url=f"{API_URL}/login",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                token_manager.set_access_token(data.get("access_token"))
                token_manager.set_refresh_token(response.cookies.get("refresh_token"))
                return {"detail": "Successfully login!"}
            elif response.status_code == 401:
                return {{"request error": f"Ошибка авторизации: неверный пароль"}}
            else:
                return {"request error": f"Ошибка авторизации: {response.status_code}, {response.text}"}
        except httpx.RequestError as e:
            return {"request error": f"error while requesting the code: {e}"}

async def refresh_tokens():
    refresh_token = token_manager.get_refresh_token()
    if not refresh_token:
        return {"request error": "No refresh token stored"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url = f"{API_URL}/refresh",
                cookies={"refresh_token": refresh_token}
            )

            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                new_refresh_token = response.cookies.get("refresh_token")

                if new_access_token and new_refresh_token:
                    token_manager.set_access_token(new_access_token)
                    token_manager.set_refresh_token(new_refresh_token)
                    return {"detail": "Tokens are updated"}
                else:
                    return {"error": "Error tokens updating"}
            else:
                return {"error": f"Ошибка авторизации: {response.status_code}, {response.text}"}
        except httpx.RequestError as e:
            return {"request error": f"error while requesting the code: {e}"}

async def check_refresh_token_expired():
    refresh_token = token_manager.get_refresh_token()
    if not refresh_token:
        return {"request error": "No refresh token stored"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                url = f"{API_URL}/check_refresh_token",
                cookies={"refresh_token": refresh_token}
            )

            if response.status_code == 200:
                data = response.json()
                token_manager.set_access_token(data.get("access_token"))
                return {"detail": "login success"}
            elif response.status_code == 407:
                return {"request error": "refresh token is expired"}
            else:
                return {"request error": f"{response.status_code} {response.text}"}
        except httpx.RequestError as e:
            return {"request error": f"error while requesting the code: {e}"}