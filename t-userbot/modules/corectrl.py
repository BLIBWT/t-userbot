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

from .. import loader, main, utils
import telethon


def register(cb):
    cb(CoreMod())


@loader.tds
class CoreMod(loader.Module):
    """
    Core :
    -> Control core userbot settings.

    Commands :
     
    """
    strings = {"name": "Settings",
               "alias_args": "<b>You must provide a command and the alias for it.</b>",
               "alias_created": "<b>Alias created. Access it with</b> <code>{}</code>.",
               "alias_removed": "<b>Alias</b> <code>{}</code> <b>removed.",
               "blacklisted": "<b>Chat {} blacklisted from userbot.</b>",
               "delalias_args": "<b>You must provide the alias name.</b>",
               "no_alias": "<b>Alias</b> <code>{}</code> <b>does not exist.</b>",
               "no_command": "<b>Command</b> <code>{}</code> <b>does not exist.</b>",
               "pack_error": "<b>Invalid translation pack specified.</b>",
               "pack_saved": "<b>Translation pack added.</b>",
               "prefix_reseted": "<b>Command prefix reseted.</b>",
               "prefix_set": ("<b>Command prefix updated. Type</b> <code>{}setprefix reset"
                              "</code> <b>to reset the command prefix.</b>"),
               "too_many_args": "<b>Too many args.</b>",
               "unblacklisted": "<b>Chat {} unblacklisted from userbot.</b>",
               "what_pack": "<b>What translation pack should be added ?</b>",
               "what_prefix": "<b>What should the prefix be set to ?</b>"}

    def config_complete(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message):
        args = utils.get_args(message)
        if len(args) > 2:
            await utils.answer(message, self.strings["too_many_args"])
            return
        chatid = None
        module = None
        if len(args) >= 1:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]
        if len(args) == 2:
            module = args[1]
        if chatid is None:
            chatid = utils.get_chat_id(message)
        module = self.allmodules.get_classname(module)
        return str(chatid) + "." + module if module else chatid

    async def blacklistcmd(self, message):
        """.blacklist [id] : Blacklist the bot to operate somewhere.\n """
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats", self._db.get(main.__name__, "blacklist_chats", []) + [chatid])
        await utils.answer(message, self.strings["blacklisted"].format(chatid))

    async def unblacklistcmd(self, message):
        """.unblacklist [id] : Unblacklist the bot to operate somewhere."""
        chatid = await self.blacklistcommon(message)
        self._db.set(main.__name__, "blacklist_chats",
                     list(set(self._db.get(main.__name__, "blacklist_chats", [])) - set([chatid])))
        await utils.answer(message, self.strings["unblacklisted"].format(chatid))

    async def setprefixcmd(self, message):
        """
        .setprefix [prefix] : Set command prefix.
        .setprefix reset : Reset command prefix.
         
        """
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings["what_prefix"])
            return
        if args[0] == "reset":
            self._db.set(main.__name__, "command_prefix", ".")
            await utils.answer(message, self.strings["prefix_reseted"])
            return
        else:
            self._db.set(main.__name__, "command_prefix", args[0])
            await utils.answer(message, self.strings["prefix_set"].format(utils.escape_html(args[0])))

    async def addaliascmd(self, message):
        """Set an alias for a command.\n """
        args = utils.get_args(message)
        if len(args) != 2:
            await utils.answer(message, self.strings["alias_args"])
            return
        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)
        if ret:
            self._db.set(__name__, "aliases", {**self._db.get(__name__, "aliases"), alias: cmd})
            await utils.answer(message, self.strings["alias_created"].format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings["no_command"].format(utils.escape_html(cmd)))

    async def delaliascmd(self, message):
        """Remove an alias for a command.\n """
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings["delalias_args"])
            return
        alias = args[0]
        ret = self.allmodules.remove_alias(alias)
        if ret:
            current = self._db.get(__name__, "aliases")
            del current[alias]
            self._db.set(__name__, "aliases", current)
            await utils.answer(message, self.strings["alias_removed"].format(utils.escape_html(alias)))
        else:
            await utils.answer(message, self.strings["no_alias"].format(utils.escape_html(alias)))

    async def addpackcmd(self, message):
        """
        .addpack [pack] : Add a translation pack.

        Restart is required to apply the changes !
         
        """
        args = utils.get_args(message)
        if len(args) != 1:
            await utils.answer(message, self.strings["what_pack"])
            return
        pack = args[0]
        try:
            pack = int(pack)
        except ValueError:
            pass
        try:
            pack = await self._client.get_entity(pack)
        except ValueError:
            await utils.answer(message, self.strings["pack_error"])
            return
        if isinstance(pack, telethon.tl.types.Channel) and not pack.megagroup:
            self._db.setdefault(main.__name__, {}).setdefault("langpacks", []).append(pack.id)
            self._db.save()
            await utils.answer(message, self.strings["pack_saved"])
        else:
            await utils.answer(message, self.strings["pack_error"])

    async def _client_ready2(self, client, db):
        ret = {}
        for alias, cmd in db.get(__name__, "aliases", {}).items():
            if self.allmodules.add_alias(alias, cmd):
                ret[alias] = cmd
        db.set(__name__, "aliases", ret)
