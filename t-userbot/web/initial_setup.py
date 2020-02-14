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

from aiohttp import web
import aiohttp_jinja2
import asyncio
import collections
import os
import re
import secrets
import string
import telethon

from .. import utils


class Web:
    def __init__(self, **kwargs):
        self.heroku_api_key = os.environ.get("heroku_api_key")
        self.telegram_api = kwargs.pop("telegram_api")
        self.redirect_url = None
        super().__init__(**kwargs)
        self.app.router.add_get("/initialSetup", self.initial_setup)
        self.app.router.add_post("/setConfiguration", self.set_configuration)
        self.app.router.add_post("/verifyTelegramCode", self.verify_telegram_code)
        self.app.router.add_post("/verifyTelegramPassword", self.verify_telegram_password)
        self.app.router.add_post("/deploy", self.deploy)
        self.api_set = asyncio.Event()
        self.sign_in_clients = {}
        self.clients = []
        self.clients_set = asyncio.Event()
        self.root_redirected = asyncio.Event()
        self._pending_secret_to_uid = {}

    async def root(self, request):
        if self.clients_set.is_set():
            await self.ready.wait()
        if self.redirect_url:
            self.root_redirected.set()
            return web.Response(status=302, headers={"Location": self.redirect_url})
        if self.client_data:
            return await super().root(request)
        return await self.initial_setup(request)

    @aiohttp_jinja2.template("initial_root.jinja2")
    async def initial_setup(self, request):
        if self.client_data and await self.check_user(request) is None and \
           self.telegram_apki is not None and self.heroku_api_key is not None:
            return web.Response(status=302, headers={"Location": "/"})  # User not connected.
        return {}

    async def set_configuration(self, request):
        if self.client_data and await self.check_user(request) is None:
            return web.Response(status=302, headers={"Location": "/"})  # User not connected.
        # Get data
        data = await request.text()
        if len(data) < 56:
            return web.Response(status=400)
        split = data.split("\n", 3)
        if len(split) != 4:
            return web.Response(status=400)
        api_id = split[0]
        api_hash = split[1]
        phone = telethon.utils.parse_phone(split[2])
        api_key = split[3]
        # Check phone
        if not phone:
            return web.Response(status=400)
        # Check Heroku API Key
        if not re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", api_key):
            return web.Response(status=400)
        self.heroku_api_key = api_key
        # Set api
        if any(c not in string.hexdigits for c in api_hash) or any(c not in string.digits for c in api_id):
            return web.Response(status=400)
        with open(os.path.join(utils.get_base_dir(), "telegram_api.py"), "w") as f:
            f.write("HASH = \"" + api_hash + "\"\nID = \"" + api_id + "\"\n")
        self.telegram_api = collections.namedtuple("telegram_api", ("ID", "HASH"))(api_id, api_hash)
        self.api_set.set()
        # Send code
        client = telethon.TelegramClient(telethon.sessions.MemorySession(),
                                         self.telegram_api.ID,
                                         self.telegram_api.HASH)
        await client.connect()
        try:
            await client.send_code_request(phone)
        except telethon.errors.FloodWaitError as e:
            return web.Response(status=421, text=str(e.seconds))
        self.sign_in_clients[phone] = client
        return web.Response()

    async def verify_telegram_code(self, request):
        if self.client_data and await self.check_user(request) is None:
            return web.Response(status=302, headers={"Location": "/"})  # User not connected.
        text = await request.text()
        if len(text) < 6:
            return web.Response(status=4010)
        split = text.split("\n", 1)
        if len(split) not in (1, 2):
            return web.Response(status=400)
        code = split[0]
        phone = telethon.utils.parse_phone(split[1])
        if (len(code) != 5) or any(c not in string.digits for c in code) or not phone:
            return web.Response(status=400)
        client = self.sign_in_clients[phone]
        try:
            user = await client.sign_in(phone, code=code)
        except telethon.errors.SessionPasswordNeededError:
            return web.Response(status=401)  # 2FA
        except telethon.errors.PhoneCodeExpiredError:
            return web.Response(status=404)  # Code expired
        except telethon.errors.PhoneCodeInvalidError:
            return web.Response(status=403)  # Code invalid
        except telethon.errors.FloodWaitError as e:
            return web.Response(status=421, text=str(e.seconds))  # Flood
        del self.sign_in_clients[phone]
        client.phone = "+" + user.phone
        self.clients.append(client)
        secret = secrets.token_urlsafe()
        self._pending_secret_to_uid[secret] = user.id
        return web.Response(text=secret)

    async def verify_telegram_password(self, request):
        if self.client_data and await self.check_user(request) is None:
            return web.Response(status=302, headers={"Location": "/"})  # User not connected.
        text = await request.text()
        if len(text) < 6:
            return web.Response(status=400)
        split = text.split("\n", 2)
        if len(split) not in (1, 2):
            return web.Response(status=400)
        password = split[0]
        phone = telethon.utils.parse_phone(split[1])
        if not password or not phone:
            return web.Response(status=400)
        client = self.sign_in_clients[phone]
        try:
            user = await client.sign_in(phone, password=password)
        except telethon.errors.PasswordHashInvalidError:
            return web.Response(status=403)  # Password invalid
        except telethon.errors.FloodWaitError as e:
            return web.Response(status=421, text=str(e.seconds))  # Flood
        del self.sign_in_clients[phone]
        client.phone = "+" + user.phone
        self.clients.append(client)
        secret = secrets.token_urlsafe()
        self._pending_secret_to_uid[secret] = user.id
        return web.Response(text=secret)

    async def deploy(self, request):
        if not self.clients:
            return web.Response(status=400)
        text = await request.text()
        if text == "deploy":
            self._secret_to_uid.update(self._pending_secret_to_uid)
            self.clients_set.set()
        else:
            return web.Response(status=404)
        return web.Response()

    def wait_for_telegram_api_setup(self):
        return self.api_set.wait()

    def wait_for_clients_setup(self):
        return self.clients_set.wait()
