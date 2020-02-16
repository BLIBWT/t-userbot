#    Copyright (C) 2020 BLIBWT

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
from aiohttp import web
import aiohttp_jinja2
import hashlib
import secrets

from base64 import b64encode


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._uid_to_code = {}
        self._secret_to_uid = {}
        self.app.router.add_get("/auth", self.auth)
        self.app.router.add_post("/sendAuthTelegramCode", self.send_auth_telegram_code)
        self.app.router.add_post("/verifyAuthTelegramCode", self.verify_auth_telegram_code)
        self.app.router.add_get("/logOut", self.log_out)

    @aiohttp_jinja2.template("auth.jinja2")
    async def auth(self, request):
        if await self.check_user(request) is not None:
            return web.Response(status=302, headers={"Location": "/"})  # Already authenticated
        return {"users": self.client_data.keys(), "clients": bool(self.client_data)}

    async def send_auth_telegram_code(self, request):
        uid = int(await request.text())
        if uid in self._uid_to_code.keys():
            return web.Response()
        code = secrets.randbelow(100000)
        asyncio.ensure_future(asyncio.shield(self._clear_code(uid)))
        self._uid_to_code[uid] = b64encode(hashlib.scrypt((str(code).zfill(5) + str(uid)).encode("utf-8"),
                                                          salt="tuserbot".encode("utf-8"),
                                                          n=16384, r=8, p=1, dklen=64)).decode("utf-8")
        await self.client_data[uid][1].send_message("me", "<b>Login code:</b> <code>{:05d}</code>. Do <b>not</b> "
                                                          "give this code to anyone, even is they say they are "
                                                          "from <b>T-UserBot</b> or <b>Telegram</b>.\n\n"
                                                          "This code can be used to log in to your T-UserBot "
                                                          "account. We never ask it for anything else.\n\nIf you "
                                                          "didn't requested this code by trying to log in on your "
                                                          "T-Userbot account, sipmly ignore this message.\n\n"
                                                          "The code will expire in <b>2</b> minutes.".format(code))
        return web.Response()

    async def _clear_code(self, uid):
        await asyncio.sleep(120)  # Codes last 2 minutes, or whenever they are used
        try:
            del self._uid_to_code[uid]
        except KeyError:
            pass  # Maybe the code has already been used

    async def verify_auth_telegram_code(self, request):
        code, uid = (await request.text()).split("\n")
        uid = int(uid)
        if uid not in self._uid_to_code:
            return web.Response(status=404)
        if self._uid_to_code[uid] == code:
            del self._uid_to_code[uid]
            secret = secrets.token_urlsafe()
            asyncio.ensure_future(asyncio.shield(self._clear_secret(secret)))
            self._secret_to_uid[secret] = uid  # If they just signed in, they automatically are authenticated
            return web.Response(text=secret)
        else:
            return web.Response(status=401)

    async def _clear_secret(self, secret):
        await asyncio.sleep(60 * 60 * 6)  # You must authenticate once per 6 hours
        try:
            del self._secret_to_uid[secret]
        except KeyError:
            pass  # Meh.

    async def check_user(self, request):
        await asyncio.sleep(0.5)
        return self._secret_to_uid.get(request.cookies.get("secret", None), None)

    async def log_out(self, request):
        try:
            del self._secret_to_uid[request.cookies["secret"]]
        except KeyError:
            pass
        return web.Response(status=302, headers={"Location": "/"})
