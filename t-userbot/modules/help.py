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
import inspect

from .. import loader, utils, main

logger = logging.getLogger(__name__)


def register(cb):
    cb(HelpMod())


@loader.tds
class HelpMod(loader.Module):
    """
    Help :
    -> Get help about T-UserBot and modules commands.

    Commands :
     
    """
    strings = {"name": "Help",
               "command": "\n• <code><u>{}</u></code>\n",
               "footer" : ("<i>The monospace text are the commands. "
                           " To use a command, type :\n"
                           "<code>.<i>command</i></code>"),
               "header": ("<b>Help for T-UserBot</b>\n\n"
                              "For more help on how to use commands of a module, type :\n"
                              "<code>.help <i>module_name</i></code>\n\n"
                              "<b>Available Modules:</b>"),
               "header_module": ("<b>Help for</b> <u>{}</u>:\n"
                                 "Note that the monospace text are the commands "
                                 "and they can be run with <code>{}&lt;command&gt;</code>"),
               "module": "\n\n• <b>{}</b>",
               "module_command": ", {}",
               "module_command_end": ":</code>",
               "module_command_start": ": <code>{}",
               "module_no_help": "There is no help for this module",
               "module_unknow": "<b>Invalid module name specified</b>")

    def config_complete(self):
        self.name = self.strings["name"]

    async def helpcmd(self, message):
        """
        .help : get help about T-UserBot.
        .help [module] : Get help about command of a module.
         
        """
        args = utils.get_args_raw(message)
        if args:
            module = None
            for mod in self.allmodules.modules:
                if mod.name.lower() == args.lower():
                    module = mod
            if module is None:
                await utils.answer(message, self.strings["module_unknow"])
                return
            # Translate the format specification and the module separately
            reply = self.strings["header_module"].format(utils.escape_html(module.name),
                                                             utils.escape_html(self.db.get(main.__name__,
                                                                                           "command_prefix",
                                                                                           False) or "."))
            if module.__doc__:
                reply += "\n" + "\n".join("  " + t for t in utils.escape_html(inspect.getdoc(module)).split("\n"))
            else:
                logger.warning("Module %s is missing docstring!", module)
            for name, content in module.commands.items():
                reply += self.strings["command"].format(name)
                if content.__doc__:
                    reply += utils.escape_html("\n".join("  " + t for t in inspect.getdoc(content).split("\n")))
                else:
                    reply += self.strings["module_no_help"]
        else:
            reply = self.strings["header"]
            for mod in self.allmodules.modules:
                reply += self.strings["module"].format(mod.name)
                first = True
                for cmd in mod.commands:
                    if first:
                        reply += self.strings["module_command_start"].format(cmd)
                        first = False
                    else:
                        reply += self.strings["module_command"].format(cmd)
                reply += self.strings["module_command_end"]
            reply += self.strings["footer"]
        await utils.answer(message, reply)

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
