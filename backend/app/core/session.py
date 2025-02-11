import json
import typing
from base64 import b64decode, b64encode
from uuid import uuid4

import itsdangerous
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from starlette.datastructures import MutableHeaders, Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.core.cache import RedisCache


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret_key: typing.Union[str, Secret],
        session_cookie: str = "session",
        max_age: int = 14 * 24 * 60 * 60,  # 14 days, in seconds
        same_site: str = "lax",
        https_only: bool = False,
    ) -> None:
        self.app = app
        self.signer = itsdangerous.TimestampSigner(str(secret_key))
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.security_flags = "httponly;"
        if same_site:  # pragma: no cover
            self.security_flags += "; samesite=" + same_site
        if https_only:  # Secure flag can be used with HTTPS only  # pragma: no cover
            self.security_flags += "; secure"

        self._cookie_session_id_field = "_dssid"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        initial_session_was_empty = True

        scope["session"] = {}
        if self.session_cookie in connection.cookies:
            data = connection.cookies[self.session_cookie].encode("utf-8")
            try:
                data = self.signer.unsign(data, max_age=self.max_age)
                session_key = json.loads(b64decode(data)).get(self._cookie_session_id_field)
                if session_key:  # pragma: no cover
                    cookie_data = await RedisCache.get(session_key)
                    if cookie_data:  # pragma: no cover
                        scope["session"] = json.loads(cookie_data)
                        scope["__session_key"] = session_key
                        initial_session_was_empty = False
            except (BadTimeSignature, SignatureExpired):  # pragma: no cover
                pass

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                session_key = scope.pop("__session_key", str(uuid4()))

                if scope["session"]:
                    # We have session data to persist.
                    cookie_data = json.dumps(scope["session"]).encode("utf-8")
                    await RedisCache.set(session_key, cookie_data, ex=self.max_age)
                    session_data = {self._cookie_session_id_field: session_key}
                    data = b64encode(json.dumps(session_data).encode("utf-8"))
                    data = self.signer.sign(data)

                    headers = MutableHeaders(scope=message)
                    header_value = "%s=%s; path=/; Max-Age=%d; %s" % (
                        self.session_cookie,
                        data.decode("utf-8"),
                        self.max_age,
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                elif not initial_session_was_empty:
                    # The session has been cleared.
                    headers = MutableHeaders(scope=message)
                    header_value = "{}={}; {}".format(
                        self.session_cookie,
                        "null; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT;",
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
            await send(message)

        await self.app(scope, receive, send_wrapper)
