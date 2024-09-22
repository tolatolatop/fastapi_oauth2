from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from redis_handler import RedisHandler
import os

load_dotenv()

app = FastAPI()

# Redis handler
redis_handler = RedisHandler()

# OAuth2 配置
oauth = OAuth()
oauth.register(
    name="github",
    client_id=os.getenv("OAUTH2_CLIENT_ID"),
    client_secret=os.getenv("OAUTH2_CLIENT_SECRET"),
    authorize_url=f'{os.getenv("OAUTH2_PROVIDER_URL")}/authorize',
    access_token_url=f'{os.getenv("OAUTH2_PROVIDER_URL")}/access_token',
    client_kwargs={"scope": "user:email"},
)


@app.get("/login")
async def login(request: Request):
    redirect_uri = os.getenv("OAUTH2_REDIRECT_URI")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request, response: Response):
    # 获取 OAuth2 token
    token = await oauth.github.authorize_access_token(request)
    user_info = await oauth.github.parse_id_token(request, token)

    if not user_info:
        raise HTTPException(
            status_code=400, detail="Failed to retrieve user information"
        )

    username = user_info.get("login")

    # 生成 UID 并存储 session
    uid = redis_handler.create_user_session(username)

    # 设置 cookie，保存用户的 UID
    response.set_cookie(key="uid", value=uid)

    return {"message": "Login successful", "user": user_info, "uid": uid}


@app.get("/user/profile")
async def get_user_profile(request: Request):
    uid = request.cookies.get("uid")

    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_profile = redis_handler.get_user_session(uid)

    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return user_profile
