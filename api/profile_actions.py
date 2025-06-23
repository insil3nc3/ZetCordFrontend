import os

import httpx
from api.auth import refresh_tokens
from api.common import token_manager, URL, timeout
from pathlib import Path

API_URL = URL + "user"

async def edit_unique_name(unique_name: str):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url=f"{API_URL}/edit_unique_name",
            params={"name": unique_name},
            headers=headers
        )
        if response.status_code == 200:
            return {"detail": "unique name updated"}
        elif response.status_code == 401:
            await refresh_tokens()
            headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
            response = await client.post(
                url=f"{API_URL}/edit_unique_name",
                params={"name": unique_name},
                headers=headers
            )
            if response.status_code == 200:
                return {"detail": "unique name updated"}
        return {"error": f"code: {response.status_code}, detail: {response.text}"}

async def edit_nickname(nickname: str):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url=f"{API_URL}/edit_nickname",
            params={"nickname": nickname},
            headers=headers
        )
        if response.status_code == 200:
            return {"detail": "Name updated"}
        elif response.status_code == 401:
            await refresh_tokens()
            headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
            response = await client.post(
                url=f"{API_URL}/edit_nickname",
                params={"nickname": nickname},
                headers=headers
            )
            if response.status_code == 200:
                return {"detail": "Name updated"}
        return {"error": f"code: {response.status_code}, detail: {response.text}"}

async def upload_avatar(filepath: str):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }

    with open(filepath, "rb") as f:
        files = {"file": ("avatar.jpg", f, "image/jpeg")}
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url=f"{API_URL}/upload_avatar",
                headers=headers,
                files=files
            )
            if response.status_code == 200:
                return {"detail": "Avatar uploaded"}
            elif response.status_code == 401:
                await refresh_tokens()
                headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
                with open(filepath, "rb") as f_retry:
                    files = {"file": ("avatar.jpg", f_retry, "image/jpeg")}
                    response = await client.post(
                        url=f"{API_URL}/upload_avatar",
                        headers=headers,
                        files=files
                    )
                    if response.status_code == 200:
                        return {"detail": "Avatar uploaded"}
            return {"error": response.text}

def get_avatar_path(user_profile_id: int):
    cache_dir = "avatar"
    avatar_path = os.path.join(cache_dir ,f"{user_profile_id}.jpg")
    if os.path.exists(avatar_path):
        print("ава уже есть вот путь", avatar_path)
        return avatar_path
    else:
        return 1

async def download_avatar(user_profile_id: int) -> str | None:
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }

    avatar_path = get_avatar_path(user_profile_id)
    if avatar_path != 1:
        return avatar_path
    print("иду дальше чем вызов get_avatar_path")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                url=f"{API_URL}/avatar/{str(user_profile_id)}",
                headers=headers,
                timeout=1
            )
            if response.status_code == 200:
                with open(avatar_path, "wb") as f:
                    f.write(response.content)
                return avatar_path
            elif response.status_code == 401:
                await refresh_tokens()
                headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
                response = await client.get(
                    url=f"{API_URL}/avatar/{user_profile_id}",
                    headers=headers
                )
                if response.status_code == 200:
                    with open(avatar_path, "wb") as f:
                        f.write(response.content)
                    return avatar_path
            return None
        except Exception as e:
            print(f"Ошибка при загрузке аватара: {e}")
            return None

async def get_current_user():
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url=f"{API_URL}/me", headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            await refresh_tokens()
            headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
            response = await client.get(url=f"{API_URL}/me", headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                return {"request error": "Unauthorized even after token refresh"}
        else:
            return {"request error": response.text}

async def get_user_info(user_id: int):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url=f"{API_URL}/get_user_info", headers=headers, params={"user_id": user_id})

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            return {"request error": "user not in this chat"}
        elif response.status_code == 401:
            await refresh_tokens()
            headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
            response = await client.get(url=f"{API_URL}/get_user_info", headers=headers, params={"user_id": user_id})
            if response.status_code == 200:
                return response.json()
            else:
                return {"request error": "Unauthorized even after token refresh"}
        else:
            return {"request error": response.text}

async def search_user(unique_name: str):
    headers = {
        "Authorization": f"Bearer {token_manager.get_access_token()}"
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url=f"{API_URL}/get_user/{unique_name}", headers=headers, params={"user_unique_name": unique_name})
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"request error": "User not found"}
        elif response.status_code == 401:
            await refresh_tokens()
            headers["Authorization"] = f"Bearer {token_manager.get_access_token()}"
            response = await client.get(url=f"{API_URL}/get_user/{unique_name}", headers=headers,
                                        params={"user_unique_name": unique_name})
            if response.status_code == 200:
                return response.json()
            else:
                return {"request error": "Unauthorized even after token refresh"}
        else:
            return {"request error": response.text}