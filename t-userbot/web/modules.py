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

import ast

from aiohttp import web
import aiohttp_jinja2


class Web:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.router.add_get("/modules", self.modules)
        self.app.router.add_put("/setModulesSettings", self.set_modules_settings)

    @aiohttp_jinja2.template("modules.jinja2")
    async def modules(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=302, headers={"Location": "/"})  # They gotta sign in.
        return {"modules": self.client_data[uid][0].modules}

    async def set_modules_settings(self, request):
        uid = await self.check_user(request)
        if uid is None:
            return web.Response(status=401)
        data = await request.json()
        mid, key, value = int(data["mid"]), data["key"], data["value"]
        mod = self.client_data[uid][0].modules[mid]
        if value:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                pass
            self.client_data[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key] = value
        else:
            try:
                del self.client_data[uid][2].setdefault(mod.__module__, {}).setdefault("__config__", {})[key]
            except KeyError:
                pass
        self.client_data[uid][0].send_config_one(mod, self.client_data[uid][2], skip_hook=True)
        self.client_data[uid][2].save()
        return web.Response()
