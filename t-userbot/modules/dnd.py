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

from .. import loader, utils

import logging
import datetime
import time

from telethon import functions, types
logger = logging.getLogger(__name__)


def register(cb):
    cb(DoNotDisturbMod())


@loader.tds
class DoNotDisturbMod(loader.Module):
    """
    DND (Do Not Disturb) :
    -> Prevents people sending you unsolicited private messages.
    -> Prevents disturbing when you are unavailable.\n
    Commands :
     
    """
    strings = {"name": "DND",
               "afk": "<b>I'm AFK right now (since</b> <i>{}</i> <b>ago).</b>",
               "afk_back": "<b>I'm now BACK !</b>",
               "afk_grp_off": "<b>AFK status message disabled for group chats.</b>",
               "afk_grp_on": "<b>AFK status message enabled for group chats.</b>",
               "afk_notif_off": "<b>Notifications are now disabled during AFK time.</b>",
               "afk_notif_on": "<b>Notifications are now enabled during AFK time.</b>",
               "afk_now": "<b>I'm now AFK !</b>",
               "afk_pm_off": "<b>AFK status message disabled for PMs.</b>",
               "afk_pm_on": "<b>AFK status message enabled for PMs.</b>",
               "afk_rate_limit_off": "<b>AFK status message rate limit disabled.</b>",
               "afk_rate_limit_on": ("<b>AFK status message rate limit enabled.</b>"
                                     "\n\n<b>One AFK status message max will be sent per chat.</b>"),
               "afk_with_reason": ("<b>I'm AFK right now (since</b> <i>{}</i> <b>ago).</b>"
                                   "\n\n<b>Reason :</b> <i>{}</i>"),
               "arg_on_off": "<b>Argument must be 'off' or 'on' !</b>",
               "conf": "<b>Current DND Module configuration :</b>",
               "conf_afk": "\n\n<b>AFK :</b>",
               "conf_afk_current": "\n• <b>Currently AFK :</b> <i>{}</i>.",
               "conf_afk_duration": "\n• <b>AFK time :</b> <i>{}</i>.",
               "conf_afk_grp": "\n• <b>AFK status message for group chats :</b> <i>{}</i>.",
               "conf_afk_notif": "\n• <b>Notifications during AFK time :</b> <i>{}</i>.",
               "conf_afk_pm": "\n• <b>AFK status message for PMs :</b> <i>{}</i>.",
               "conf_afk_rate_limit": "\n• <b>AFK rate limit :</b> <i>{}</i>.",
               "conf_afk_reason": "\n• <b>AFK reason :</b> <i>{}</i>.",
               "conf_pm": "\n\n<b>PMs :</b>",
               "conf_pm_auto": "\n• <b>Automatic answer for denied PMs :</b> <i>{}</i>.",
               "conf_pm_limit": "\n• <b>Automatic user blocking :</b> <i>{}</i>.",
               "conf_pm_notif": "\n• <b>Notifications from denied PMs :</b> <i>{}</i>.",
               "conf_pm_limit_max": "\n• <b>Max number of PMs before automatically block not allowed user :</b> <i>{}</i>.",
               "pm_auto_off": ("<b>Automatic answer for denied PMs disabled."
                               "\n\nUsers are now free to PM !</b>"),
               "pm_auto_on": "<b>An automatic answer is now sent for denied PMs.</b>",
               "pm_allowed": "<b>I have allowed</b> <a href='tg://user?id={}'>you</a> <b>to PM now.</b>",
               "pm_blocked": ("<b>I don't want any PM from</b> <a href='tg://user?id={}'>you</a>, "
                              "<b>so you have been blocked !</b>"),
               "pm_denied": "<b>I have denied</b> <a href='tg://user?id={}'>you</a> <b>to PM now.</b>",
               "pm_go_away": ("Hey there! Unfortunately, I don't accept private messages from strangers."
                              "\n\nPlease contact me in a group, or <b>wait</b> for me to approve you."),
               "pm_reported": "<b>You just got reported to spam !</b>",
               "pm_limit_arg": "<b>Argument must be 'off', 'on' or a number between 10 and 1000 !</b>",
               "pm_limit_off": "<b>Not allowed users are now free to PM without be automatically blocked.</b>",
               "pm_limit_on": "<b>Not allowed users are now blocked after {} PMs.</b>",
               "pm_limit_current": "<b>Current limit is {}.</b>",
               "pm_limit_current_no": "<b>Automatic user blocking is currently disabled.</b>",
               "pm_limit_reset": "<b>Limit reseted to {}.</b>",
               "pm_limit_set": "<b>Limit set to {}.</b>",
               "pm_notif_off": "<b>Notifications from denied PMs are now disabled.</b>",
               "pm_notif_on": "<b>Notifications from denied PMs are now enabled.</b>",
               "pm_triggered": ("Hey! I don't appreciate you barging into my PM like this !"
                                "\nDid you even ask me for approving you to PM ? No ?"
                                "\nGoodbye then."
                                "\n\nPS: You've been reported as spam."),
               "pm_unblocked": ("<b>Alright fine! I'll forgive them this time. PM has been unblocked for</b> "
                                "<a href='tg://user?id={}'>this user</a>."),
               "unknow": "An unknow problem as occured.",
               "who_to_allow": "<b>Who shall I allow to PM ?</b>",
               "who_to_block": "<b>Specify who to block.</b>",
               "who_to_deny": "<b>Who shall I deny to PM ?</b>",
               "who_to_report": "<b>Who shall I report ?</b>",
               "who_to_unblock": "<b>Specify who to unblock.</b>"}

    def __init__(self):
        self._me = None
        self.default_pm_limit = 50

    def config_complete(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me(True)

    async def afkcmd(self, message):
        """
        .afk : Enable AFK status.
        .afk [message] : Enable AFK status with a reason.
         
        """
        if utils.get_args_raw(message):
            self._db.set(__name__, "afk_reason", utils.get_args_raw(message))
        self._db.set(__name__, "afk", True)
        afk_time =  self._db.get(__name__, "afk_time")
        if afk_time is None or afk_time is False:
            self._db.set(__name__, "afk_time", time.time())
        self._db.set(__name__, "afk_rate", [])
        await utils.answer(message, self.strings["afk_now"])

    async def afkbcmd(self, message):
        """Delete AFK status.\n """
        self._db.set(__name__, "afk", False)
        self._db.set(__name__, "afk_reason", False)
        self._db.set(__name__, "afk_time", False)
        self._db.set(__name__, "afk_rate", [])
        await utils.answer(message, self.strings["afk_back"])

    async def afkgrpcmd(self, message):
        """
        .afkgrp : Disable/Enable AFK status message for group chats.
        .afkgrp off : Disable AFK status message for group chats.
        .afkgrp on : Enable AFK status message for group chats.
         
        """
        afkgrp_arg = utils.get_args_raw(message)
        afkgrp_current = self._db.get(__name__, "afk_grp")
        if (afkgrp_arg and afkgrp_arg == "off") or \
        (not afkgrp_arg and (afkgrp_current is None or afkgrp_current is False)):
            self._db.set(__name__, "afk_grp", True)
            await utils.answer(message, self.strings["afk_grp_off"])
        elif (afkgrp_arg and afkgrp_arg == "on") or (not afkgrp_arg and afkgrp_current is True):
            self._db.set(__name__, "afk_grp", False)
            await utils.answer(message, self.strings["afk_grp_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def afknotifcmd(self, message):
        """
        .afknotif : Disable/Enable the notifications during AFK time.
        .afknotif off : Disable the notifications during AFK time.
        .afknotif on : Enable the notifications during AFK time.
         
        """
        afknotif_arg = utils.get_args_raw(message)
        afknotif_current = self._db.get(__name__, "afk_notif")
        if (afknotif_arg and afknotif_arg == "off") or (not afknotif_arg and afknotif_current is True):
            self._db.set(__name__, "afk_notif", False)
            await utils.answer(message, self.strings["afk_notif_off"])
        elif (afknotif_arg and afknotif_arg == "on") or \
        (not afknotif_arg and (afknotif_current is None or afknotif_current is False)):
            self._db.set(__name__, "afk_notif", True)
            await utils.answer(message, self.strings["afk_notif_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def afkpmcmd(self, message):
        """
        .afkpm : Disable/Enable AFK status message for PMs.
        .afkpm off : Disable AFK status message for PMs.
        .afkpm on : Enable AFK status message for PMs.
         
        """
        afkpm_arg = utils.get_args_raw(message)
        afkpm_current = self._db.get(__name__, "afk_pm")
        if (afkpm_arg and afkpm_arg == "off") or \
        (not afkpm_arg and (afkpm_current is None or afkpm_current is False)):
            self._db.set(__name__, "afk_pm", True)
            await utils.answer(message, self.strings["afk_pm_off"])
        elif (afkpm_arg and afkpm_arg == "on") or (not afkpm_arg and afkpm_current is True):
            self._db.set(__name__, "afk_pm", False)
            await utils.answer(message, self.strings["afk_pm_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def afkratecmd(self, message):
        """
        .afkrate : Disable/Enable AFK rate limit.
        .afkrate off : Disable AFK rate limit.
        .afkrate on : Enable AFK rate limit. One AFK status message max will be sent per chat.
         
        """
        afkrate_arg = utils.get_args_raw(message)
        afkrate_current = self._db.get(__name__, "afk_rate_limit")
        if (afkrate_arg and afkrate_arg == "off") or (not afkrate_arg and afkrate_current is True):
            self._db.set(__name__, "afk_rate_limit", False)
            await utils.answer(message, self.strings["afk_rate_limit_off"])
        elif (afkrate_arg and afkrate_arg == "on") or \
        (not afkrate_arg and (afkrate_current is None or afkrate_current is False)):
            self._db.set(__name__, "afk_rate_limit", True)
            await utils.answer(message, self.strings["afk_rate_limit_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def allowcmd(self, message):
        """Allow this user to PM.\n """
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_allow"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).union({user})))
        await utils.answer(message, self.strings["pm_allowed"].format(user))

    async def blockcmd(self, message):
        """Block this user to PM without being warned.\n """
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_block"])
            return
        await message.client(functions.contacts.BlockRequest(user))
        await utils.answer(message, self.strings["pm_blocked"].format(user))

    async def confcmd(self, message):
        """Know current module configuration.\n """
        rep = self.strings["conf"]
        # AFK
        rep += self.strings["conf_afk"]
        afk = self._db.get(__name__, "afk")
        rep += self.strings["conf_afk_current"].format(self.get_yesno(afk, 0))
        if afk is True:
            afk_reason = self._db.get(__name__, "afk_reason")
            if afk_reason is not None and afk_reason is not False:
                rep += self.strings["conf_afk_reason"].format(afk_reason)
            rep += self.strings["conf_afk_duration"].format(self.get_afk_duration())
            afk_rate_limit = self._db.get(__name__, "afk_rate_limit")
            rep += self.strings["conf_afk_rate_limit"].format(self.get_onoff(afk_rate_limit, 0))
        afk_grp = self._db.get(__name__, "afk_grp")
        rep += self.strings["conf_afk_grp"].format(self.get_onoff(afk_grp, 1))
        afk_pm = self._db.get(__name__, "afk_pm")
        rep += self.strings["conf_afk_pm"].format(self.get_onoff(afk_pm, 1))
        afk_notif = self._db.get(__name__, "afk_notif")
        rep += self.strings["conf_afk_notif"].format(self.get_onoff(afk_notif, 0))
        # PMs
        rep += "\n\n<b>PMs :</b>"
        pm_auto = self._db.get(__name__, "pm_auto")
        rep += self.strings["conf_pm_auto"].format(self.get_onoff(pm_auto, 1))
        if pm_auto is None or pm_auto is False:
            pm_limit = self._db.get(__name__, "pm_limit")
            rep += self.strings["conf_pm_limit"].format(self.get_onoff(pm_limit, 0))
            if pm_limit is True:
                pm_limit_max = self._db.get(__name__, "pm_limit_max")
                rep += self.strings["conf_pm_limit_max"].format(pm_limit_max)
            pm_notif = self._db.get(__name__, "pm_notif")
            rep += self.strings["conf_pm_notif"].format(self.get_onoff(pm_notif, 0))
        await utils.answer(message, rep)

    async def denycmd(self, message):
        """Deny this user to PM without being warned.\n """
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_deny"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        await utils.answer(message, self.strings["pm_denied"].format(user))

    async def pmautocmd(self, message):
        """
        .pmauto : Disable/Enable automatic answer for denied PMs.
        .pmauto off : Disable automatic answer for denied PMs.
        .pmauto on : Enable automatic answer for denied PMs.
         
        """
        pmauto_arg = utils.get_args_raw(message)
        pmauto_current = self._db.get(__name__, "pm_auto")
        if (pmauto_arg and pmauto_arg == "off") or \
        (not pmauto_arg and (pmauto_current is None or pmauto_current is False)):
            self._db.set(__name__, "pm_auto", True)
            await utils.answer(message, self.strings["pm_auto_off"])
        elif (pmauto_arg and pmauto_arg == "on") or (not pmauto_arg and pmauto_current is True):
            self._db.set(__name__, "pm_auto", False)
            await utils.answer(message, self.strings["pm_auto_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def pmlimitcmd(self, message):
        """
        .pmlimit : Get current max number of PMs before automatically block not allowed user.
        .pmlimit off : Disable automatic user blocking.
        .pmlimit on : Enable automatic user blocking.
        .pmlimit reset : Reset max number of PMs before automatically block not allowed user.
        .pmlimit [number] : Modify max number of PMs before automatically block not allowed user.
         
        """
        if utils.get_args_raw(message):
            pmlimit_arg = utils.get_args_raw(message)
            if pmlimit_arg == "off":
                self._db.set(__name__, "pm_limit", False)
                await utils.answer(message, self.strings["pm_limit_off"])
                return
            elif pmlimit_arg == "on":
                self._db.set(__name__, "pm_limit", True)
                pmlimit_on = self.strings["pm_limit_on"].format(self.get_current_pm_limit())
                await utils.answer(message, pmlimit_on)
                return
            elif pmlimit_arg == "reset":
                self._db.set(__name__, "pm_limit_max", self.default_pm_limit)
                pmlimit_reset = self.strings["pm_limit_reset"].format(self.get_current_pm_limit())
                await utils.answer(message, pmlimit_reset)
                return
            else:
                try:
                    pmlimit_number = int(pmlimit_arg)
                    if pmlimit_number >= 10 and pmlimit_number <= 1000:
                        self._db.set(__name__, "pm_limit_max", pmlimit_number)
                        pmlimit_new = self.strings["pm_limit_set"].format(self.get_current_pm_limit())
                        await utils.answer(message, pmlimit_new)
                        return
                    else:
                        await utils.answer(message, self.strings["pm_limit_arg"])
                        return
                except ValueError:
                    await utils.answer(message, self.strings["pm_limit_arg"])
                    return
            await utils.answer(message, self.strings["limit_arg"])
        else:
            pmlimit = self._db.get(__name__, "pm_limit")
            if pmlimit is None or pmlimit is False:
                pmlimit_current = self.strings["pm_limit_current_no"]
            elif pmlimit is True:
                pmlimit_current = self.strings["pm_limit_current"].format(self.get_current_pm_limit())
            else:
                await utils.answer(message, self.strings["unknow"])
                return
            await utils.answer(message, pmlimit_current)

    async def pmnotifcmd(self, message):
        """
        .pmnotif : Disable/Enable the notifications from denied PMs.
        .pmnotif off : Disable the notifications from denied PMs.
        .pmnotif on : Enable the notifications from denied PMs.
         
        """
        pmnotif_arg = utils.get_args_raw(message)
        pmnotif_current = self._db.get(__name__, "pm_notif")
        if (pmnotif_arg and pmnotif_arg == "off") or (not pmnotif_arg and pmnotif_current is True):
            self._db.set(__name__, "pm_notif", False)
            await utils.answer(message, self.strings["pm_notif_off"])
        elif (pmnotif_arg and pmnotif_arg == "on") or \
        (not pmnotif_arg and (pmnotif_current is None or pmnotif_current is False)):
            self._db.set(__name__, "pm_notif", True)
            await utils.answer(message, self.strings["pm_notif_on"])
        else:
            await utils.answer(message, self.strings["unknow"])

    async def reportcmd(self, message):
        """Report the user to spam. Use only in PM.\n """
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_report"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        if message.is_reply and isinstance(message.to_id, types.PeerChannel):
            await message.client(functions.messages.ReportRequest(peer=message.chat_id,
                                                                  id=[message.reply_to_msg_id],
                                                                  reason=types.InputReportReasonSpam()))
        else:
            await message.client(functions.messages.ReportSpamRequest(peer=message.to_id))
        await utils.answer(message, self.strings["pm_reported"])

    async def unblockcmd(self, message):
        """Unblock this user to PM."""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_unblock"])
            return
        await message.client(functions.contacts.UnblockRequest(user))
        await utils.answer(message, self.strings["pm_unblocked"].format(user))

    async def watcher(self, message):
        user = await utils.get_user(message)
        pm_auto = self._db.get(__name__, "pm_auto")
        afk = self._db.get(__name__, "afk")
        # PM
        if getattr(message.to_id, "user_id", None) == self._me.user_id and (pm_auto is None or pm_auto is False) and \
        not user.is_self and not user.bot and not user.verified and not self.get_allowed(message.from_id):
            pm_notif = self._db.get(__name__, "pm_notif")
            await utils.answer(message, self.strings["pm_go_away"])
            if self._db.get(__name__, "pm_limit") is True:
                pms = self._db.get(__name__, "pms", {})
                pm_limit = self._db.get(__name__, "pm_limit_max")
                pm_user = pms.get(message.from_id, 0)
                if isinstance(pm_limit, int) and pm_limit >= 10 and pm_limit <= 1000 and pm_user >= pm_limit:
                    await utils.answer(message, self.strings["pm_triggered"])
                    await message.client(functions.contacts.BlockRequest(message.from_id))
                    await message.client(functions.messages.ReportSpamRequest(peer=message.from_id))
                    del pms[message.from_id]
                    self._db.set(__name__, "pms", pms)
                else:
                    self._db.set(__name__, "pms", {**pms, message.from_id: pms.get(message.from_id, 0) + 1})
            # PM Notif
            if pm_notif is None or pm_notif is False:
                await message.client.send_read_acknowledge(message.chat_id)
        # AFK
        elif afk is True:
            afk_notif = self._db.get(__name__, "afk_notif")
            if message.mentioned or getattr(message.to_id, "user_id", None) == self._me.user_id:
                afk_grp = self._db.get(__name__, "afk_grp")
                afk_pm = self._db.get(__name__, "afk_pm")
                if user.is_self or user.bot or user.verified or afk is False or \
                (message.mentioned and (afk_grp is True)) or \
                (getattr(message.to_id, "user_id", None) == self._me.user_id and (afk_pm is True)):
                    # AFK Notif
                    if afk_notif is None or afk_notif is False:
                        await message.client.send_read_acknowledge(message.chat_id)
                    return
                afk_rate_limit = self._db.get(__name__, "afk_rate_limit")
                if afk_rate_limit is True:
                    afk_rate = self._db.get(__name__, "afk_rate", [])
                    if utils.get_chat_id(message) in afk_rate:
                        # AFK Notif
                        if afk_notif is None or afk_notif is False:
                            await message.client.send_read_acknowledge(message.chat_id)
                        return
                    else:
                        self._db.setdefault(__name__, {}).setdefault("afk_rate", []).append(utils.get_chat_id(message))
                        self._db.save()
                afk_duration = self.get_afk_duration()
                afk_reason = self._db.get(__name__, "afk_reason")
                if afk_reason is not None and afk_reason is not False:
                    afk_message = self.strings["afk_with_reason"].format(afk_duration, afk_reason)
                else:
                    afk_message = self.strings["afk"].format(afk_duration)
                await utils.answer(message, afk_message)
            # AFK Notif
            if afk_notif is None or afk_notif is False:
                await message.client.send_read_acknowledge(message.chat_id)

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])

    def get_current_pm_limit(self):
        pm_limit = self._db.get(__name__, "pm_limit_max")
        if not isinstance(pm_limit, int) or pm_limit < 10 or pm_limit > 1000:
            pm_limit = self.default_pm_limit
            self._db.set(__name__, "pm_limit_max", pm_limit)
        return pm_limit

    def get_afk_duration(self):
        now = datetime.datetime.now().replace(microsecond=0)
        afk_time = datetime.datetime.fromtimestamp(self._db.get(__name__, "afk_time")).replace(microsecond=0)
        afk_duration = now - afk_time
        return afk_duration

    def get_onoff(self, value, type):
        if value is None or value is False:
            rep = "Off" if type == 0 else "On"
        elif value is True:
            rep = "On" if type == 0 else "Off"
        else:
            rep = "Unknow"
        return rep

    def get_yesno(self, value, type):
        if value is None or value is False:
            rep = "No" if type == 0 else "Yes"
        elif value is True:
            rep = "Yes" if type == 0 else "No"
        else:
            rep = "Unknow"
        return rep
