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
import importlib
import sys
import uuid
import asyncio
import urllib

from importlib.machinery import ModuleSpec
from importlib.abc import SourceLoader

import requests

from .. import loader, utils
from ..compat import uniborg

logger = logging.getLogger(__name__)


def register(cb):  # pylint: disable=C0116
    cb(LoaderMod())


class StringLoader(SourceLoader):  # pylint: disable=W0223 # False positive, implemented in SourceLoader
    """Load a python module/file from a string"""
    def __init__(self, data, origin):
        if isinstance(data, str):
            self.data = data.encode("utf-8")
        else:
            self.data = data
        self.origin = origin

    def get_code(self, fullname):
        source = self.get_source(fullname)
        if source is None:
            return None
        return compile(source, self.origin, "exec", dont_inherit=True)

    def get_filename(self, fullname):
        return self.origin

    def get_data(self, filename):  # pylint: disable=W0221,W0613
        # W0613 is not fixable, we are overriding
        # W0221 is a false positive assuming docs are correct
        return self.data


def unescape_percent(text):
    i = 0
    ln = len(text)
    is_handling_percent = False
    out = ""
    while i < ln:
        char = text[i]
        if char == "%" and not is_handling_percent:
            is_handling_percent = True
            i += 1
            continue
        if char == "d" and is_handling_percent:
            out += "."
            is_handling_percent = False
            i += 1
            continue
        out += char
        is_handling_percent = False
        i += 1
    return out


@loader.tds
class LoaderMod(loader.Module):
    """
    Loader :
    -> Load/Unload your own modules or modules from Official repository.

    Commands :
     
    """
    strings = {"name": "Loader",
               "repo_config_doc": "Fully qualified URL to a module repo",
               "file_error": "<b>File not found.</b>",
               "module_available": "<b>Modules available from Official repository :</b>",
               "module_error": "<b>Module not available in repo.</b>",
               "module_loaded": "<b>Module loaded.</b>",
               "module_load_error": "<b>An error as occured.\nSee logs for more information.</b>",
               "module_load_error_unicode": "<b>Invalid Unicode formatting in module.</b>",
               "module_provide": "<b>Provide a module to load.</b>",
               "module_unload_arg": "<b>Please specify module name you want unload.</b>",
               "module_unloaded": "<b>Module unloaded.</b>",
               "module_unloaded_error": "<b>Module can't be unloaded.</b>",
               "preset_arg": "<b>Arg must be 'none', 'min', 'medium' or 'all' !</b>",
               "preset_current": "<b>Current preset is {}</b>",
               "preset_current_none": "<b>Currently, there isn't preset.</b>",
               "preset_deleted": "<b>Preset deleted.</b>",
               "preset_error": "<b>Preset not found.</b>",
               "preset_loaded": "<b>Preset loaded.</b>"}

    def __init__(self):
        super().__init__()
        self.config = loader.ModuleConfig("MODULES_REPO",
                                          "https://raw.githubusercontent.com/BLIBWT/t-modules/master",
                                          lambda: self.strings["repo_config_doc"])
        self._pending_setup = []

    def config_complete(self):
        self.name = self.strings["name"]

    async def dlmodcmd(self, message):
        """Load a module from the Official module repository.\n """
        args = utils.get_args(message)
        if args:
            if await self.download_and_install(args[0], message):
                self._db.set(__name__, "modules_loaded",
                             list(set(self._db.get(__name__, "modules_loaded", [])).union([args[0]])))
        else:
            text = utils.escape_html("\n".join(await self.get_repo_list("all")))
            await utils.answer(message, "<b>" + self.strings["module_available"] + "</b>\n<code>" + text + "</code>")

    async def dlpresetcmd(self, message):
        """
        .dlpreset : Get current preset.
        .dlpreset none : Reset preset to default.
        .dlpreset min : Get minimal preset (Cleaner, Tag, User Info).
        .dlpreset medium : Minimal preset with Info and Typer in more.
        .dlpreset all : Medium preset with Lydia in more.

        Set/Reset preset will reset loaded & unloaded modules too !
         
        """
        preset_arg = utils.get_args_raw(message)
        if not preset_arg:
            preset_current = self._db.get(__name__, "preset_selected", None)
            if preset_current is None:
                await utils.answer(message, self.strings["preset_current_none"])
            else:    
                await utils.answer(message, self.strings["preset_current"].format(preset_current))
            return
        if preset_arg == "none":
            self._db.set(__name__, "preset_selected", None)
            await utils.answer(message, self.strings["preset_deleted"])
            return
        elif preset_arg == "min" or preset_arg == "medium" or preset_arg == "all":
            try:
                await self.get_repo_list(preset_arg)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    await utils.answer(message, self.strings["preset_error"])
                    return
                else:
                    raise
        else:
            await utils.answer(message, self.strings["preset_arg"])
            return
        self._db.set(__name__, "preset_selected", preset_arg)
        self._db.set(__name__, "modules_loaded", [])
        self._db.set(__name__, "modules_unloaded", [])
        await utils.answer(message, self.strings["preset_loaded"])

    async def _get_modules_to_load(self):
        modules = await self.get_repo_list(self._db.get(__name__, "preset_selected", None))
        if modules is not None:
            modules = modules.difference(self._db.get(__name__, "modules_unloaded", []))
            modules.update()
        else:
            modules = self._db.get(__name__, "modules_loaded", [])
        return modules

    async def get_repo_list(self, preset=None):
        if preset is not None:
            r = await utils.run_sync(requests.get, self.config["MODULES_REPO"] + "/presets/" + preset + ".txt")
            r.raise_for_status()
            return set(filter(lambda x: x, r.text.split("\n")))
        else:
            return None

    async def download_and_install(self, module_name, message=None):
        if urllib.parse.urlparse(module_name).netloc:
            url = module_name
        else:
            url = self.config["MODULES_REPO"] + "/" + module_name + ".py"
        r = await utils.run_sync(requests.get, url)
        if r.status_code == 404:
            if message is not None:
                await utils.answer(message, self.strings["module_error"])
            return False
        r.raise_for_status()
        return await self.load_module(r.content, message, module_name, url)

    async def loadmodcmd(self, message):
        """Load the module file in reply.\n """
        if message.file:
            msg = message
        else:
            msg = (await message.get_reply_message())
        if msg is None or msg.media is None:
            args = utils.get_args(message)
            if args:
                try:
                    path = args[0]
                    with open(path, "rb") as f:
                        doc = f.read()
                except FileNotFoundError:
                    await utils.answer(message, self.strings["file_error"])
                    return
            else:
                await utils.answer(message, self.strings["module_provide"])
                return
        else:
            path = None
            doc = await msg.download_media(bytes)
        logger.debug("Loading external module...")
        try:
            doc = doc.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, self.strings["module_load_error_unicode"])
            return
        if path is not None:
            await self.load_module(doc, message, origin=path)
        else:
            await self.load_module(doc, message)

    async def load_module(self, doc, message, name=None, origin="<string>"):
        if name is None:
            uid = "__extmod_" + str(uuid.uuid4())
        else:
            uid = name.replace("%", "%%").replace(".", "%d")
        module_name = "t-userbot.modules." + uid
        try:
            module = importlib.util.module_from_spec(ModuleSpec(module_name, StringLoader(doc, origin), origin=origin))
            sys.modules[module_name] = module
            module.borg = uniborg.UniborgClient(module_name)
            module._ = _  # noqa: F821
            module.__spec__.loader.exec_module(module)
        except Exception:  # That's okay because it might try to exit or something, who knows.
            logger.exception("Loading external module failed.")
            if message is not None:
                await utils.answer(message, self.strings["module_load_error"])
            return False
        if "register" not in vars(module):
            if message is not None:
                await utils.answer(message, self.strings["module_load_error"])
            logging.error("Module does not have register(), it has " + repr(vars(module)))
            return False
        try:
            try:
                module.register(self.register_and_configure, module_name)
            except TypeError:
                module.register(self.register_and_configure)
            await self._pending_setup.pop()
        except Exception:
            logger.exception("Module threw")
            if message is not None:
                await utils.answer(message, self.strings["module_load_error"])
            return False
        if message is not None:
            await utils.answer(message, self.strings["module_loaded"])
        return True

    def register_and_configure(self, instance):
        self.allmodules.register_module(instance)
        self.allmodules.send_config_one(instance, self._db, self.babel)
        self._pending_setup.append(self.allmodules.send_ready_one(instance, self._client, self._db, self.allclients))

    async def unloadmodcmd(self, message):
        """.unloadmod '[module]' : Unload a module."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["module_unload_arg"])
            return
        clazz = args[0]
        worked = self.allmodules.unload_module(clazz)
        without_prefix = []
        for mod in worked:
            assert mod.startswith("t-userbot.modules."), mod
            without_prefix += [unescape_percent(mod[len("t-userbot.modules."):])]
        it = set(self._db.get(__name__, "modules_loaded", [])).difference(without_prefix)
        self._db.set(__name__, "modules_loaded", list(it))
        it = set(self._db.get(__name__, "modules_unloaded", [])).union(without_prefix)
        self._db.set(__name__, "modules_unloaded", list(it))
        if worked:
            await utils.answer(message, self.strings["module_unloaded"])
        else:
            await utils.answer(message, self.strings["module_unloaded_error"])

    async def _update_modules(self):
        todo = await self._get_modules_to_load()
        await asyncio.gather(*[self.download_and_install(mod) for mod in todo])

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        await self._update_modules()
