from fastapi import FastAPI, HTTPException, Request, Response, Depends
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from redis_handler import RedisHandler
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# 添加 SessionMiddleware，并为其设置加密密钥
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

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

    # 使用 access_token 获取用户信息
    user_info = await oauth.github.get("https://api.github.com/user", token=token)

    if not user_info:
        raise HTTPException(
            status_code=400, detail="Failed to retrieve user information"
        )

    username = user_info.json().get("login")

    # 生成 UID 并存储 session
    uid = await redis_handler.create_user_session(username)

    # 将用户的 UID 存储到会话
    request.session["uid"] = uid

    # 设置 cookie，保存用户的 UID
    response.set_cookie(key="uid", value=uid)

    return {"message": "Login successful", "user": user_info.json(), "uid": uid}


@app.get("/user/profile")
async def get_user_profile(request: Request):
    # 从会话中获取 UID
    uid = request.session.get("uid")

    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_profile = redis_handler.get_user_session(uid)

    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return user_profile
