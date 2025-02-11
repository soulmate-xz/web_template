#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import jwt
from fastapi import APIRouter, Depends, Request
from fastapi.openapi.models import OAuthFlowPassword
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from passlib.context import CryptContext
from pydantic import ValidationError
from typing_extensions import TypedDict

from backend.app.core.cache import RedisCache
from backend.app.core.config import settings
from backend.app.core.errors import (
    UserAuthFailed,
    UserLoginFailed,
    UserTokenWasExpired,
    UserWasAlreadyDisabled,
)
from backend.app.core.models.user import User as UserORM
from backend.app.core.schemas.api.request import LoginRequest

backendAuthRouter = APIRouter()
PasswordContext = CryptContext(schemes=[settings.CRYPT_SCHEMA], deprecated="auto")
logger = logging.getLogger("Auth")


class TokenInfo(TypedDict):
    access_token: Union[str, bytes]
    token_type: str


class Response(TypedDict):
    code: int
    message: str
    data: Union[Dict[str, Any], TokenInfo]


async def judge_user_activated(user: UserORM) -> bool:
    if user.activated is False:
        return False
    return True


class backendServerOAuth(OAuth2):
    def __init__(
        self,
        token_url: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[dict] = None,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl=token_url, scopes=scopes))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=True)

    async def __call__(self, request: Request) -> Optional[UserORM]:
        authorization: Optional[str] = request.headers.get("Authorization")
        if not authorization:
            raise UserLoginFailed
        scheme, param = get_authorization_scheme_param(authorization)
        try:
            payload = jwt.decode(param, str(settings.SECRET_KEY), algorithms=[settings.TOKEN_ALGORITHM])
            username = payload["sub"]
            if not username:
                raise UserTokenWasExpired

            user = await UserORM.get_by(username=username)
            token_expire = datetime.fromtimestamp(payload["exp"])
        except (jwt.PyJWTError, ValidationError):
            raise UserTokenWasExpired

        if not user:
            raise UserTokenWasExpired

        if not await judge_user_activated(user):
            raise UserWasAlreadyDisabled

        if token_expire and token_expire <= datetime.now():
            raise UserTokenWasExpired

        return user


if settings.DEBUG or settings.TESTING:  # pragma: no cover

    @backendAuthRouter.post(settings.TOKEN_URL, name="用户登录(Form)")
    async def login_form(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenInfo:
        # async with db.transaction():
        user = await UserORM.get_by(username=form_data.username)

        if not user:
            raise UserAuthFailed
        result = await judge_user_activated(user)
        if result:
            now = datetime.now()
            expire = now + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
            if PasswordContext.verify(form_data.password, user.password):
                access_token = create_access_token(data={"sub": user.username}, expire=expire)
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise UserAuthFailed
        raise UserWasAlreadyDisabled


@backendAuthRouter.post("/api/login", name="用户登录(json)")
async def login_json(login_data: LoginRequest, request: Request) -> Response:
    ip = request.client.host  # type: ignore[union-attr]

    attempts_limit = 6

    attempts = int(await RedisCache.get(f"backend:login:{ip}:{login_data.username}") or 0)
    attempts += 1

    if attempts == attempts_limit:
        expire = 60 * 2
    else:
        expire = 60

    await RedisCache.set(f"backend:login:{ip}:{login_data.username}", attempts, ex=expire)

    user = await UserORM.get_by(username=login_data.username)

    if not user:
        raise UserAuthFailed

    if not await judge_user_activated(user):
        raise UserWasAlreadyDisabled
    if not PasswordContext.verify(login_data.password, user.password):
        raise UserAuthFailed

    code = 200
    message = "获取认证成功"
    now = datetime.now()
    expired_at = now + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expire=expired_at)

    await RedisCache.delete(f"backend:login:{ip}:{login_data.username}")

    return {
        "code": code,
        "message": message,
        "data": {"access_token": access_token, "token_type": "bearer"},
    }


async def get_current_user(user: UserORM = Depends(backendServerOAuth(token_url=settings.TOKEN_URL))) -> UserORM:
    ...
    return user


def create_access_token(*, data: Dict[str, Any], expire: datetime) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, str(settings.SECRET_KEY), algorithm=settings.TOKEN_ALGORITHM)
    return encoded_jwt
