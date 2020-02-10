# -*- coding: future_fstrings -*-

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

import logging
import time

from io import BytesIO

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(TestMod())


@loader.tds
class TestMod(loader.Module):
    """Test :
    -> Test commands.

    Commands :
     
    """
    strings = {"name": "Test",
               "bad_loglevel": ("<b>Invalid loglevel. Please refer to </b>"
                                "<a href='https://docs.python.org/3/library/logging.html#logging-levels'>"
                                "the docs</a><b>.</b>"),
               "logs_caption": "t-userbot logs with verbosity {}.",
               "logs_filename": "t-userbot-logs.txt",
               "no_logs": "<b>You don't have any logs at verbosity {}.</b>",
               "pong": "Pong",
               "set_loglevel": "<b>Please specify verbosity as an integer or string.</b>",
               "suspend_invalid_time": "<b>Invalid time to suspend.</b>",
               "uploading_logs": "<b>Uploading logs...</b>"}

    def config_complete(self):
        self.name = self.strings["name"]

    async def dumpcmd(self, message):
        """Use in reply to get a dump of a message.\n """
        if not message.is_reply:
            return
        await utils.answer(message, "<code>"
                           + utils.escape_html((await message.get_reply_message()).stringify()) + "</code>")

    async def logscmd(self, message):
        """
        .logs [number] : Dumps logs with at specified verbosity.
        Loglevels below WARNING may contain personal info !
         
        """
        args = utils.get_args(message)
        if not len(args) == 1:
            await message.edit(self.strings["set_loglevel"])
            return
        try:
            lvl = int(args[0])
        except ValueError:
            # It's not an int. Maybe it's a loglevel
            lvl = getattr(logging, args[0].upper(), None)
        if lvl is None:
            await message.edit(self.strings["bad_loglevel"])
            return
        await message.edit(self.strings["uploading_logs"])
        [handler] = logging.getLogger().handlers
        logs = ("\n".join(handler.dumps(lvl))).encode("utf-8")
        if not len(logs) > 0:
            await message.edit(self.strings["no_logs"].format(lvl))
            return
        logs = BytesIO(logs)
        logs.name = self.strings["logs_filename"]
        await message.client.send_file(message.to_id, logs, caption=self.strings["logs_caption"].format(lvl))
        await message.delete()

    async def pingcmd(self, message):
        """Ping to Pong.\n """
        await message.edit(self.strings["pong"])

    async def suspendcmd(self, message):
        """.suspend [number] : Suspends the bot for X seconds."""
        # Blocks asyncio event loop, preventing ANYTHING happening (except multithread ops,
        # but they will be blocked on return).
        try:
            time.sleep(int(utils.get_args_raw(message)))
        except ValueError:
            await message.edit(self.strings["suspend_invalid_time"])

    async def client_ready(self, client, db):
        self.client = client
