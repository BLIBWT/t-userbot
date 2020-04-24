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

"""Handles heroku uploads"""

import logging
import json
import os

from git import Repo
from git.exc import InvalidGitRepositoryError
from telethon.sessions import StringSession
import heroku3

from . import utils


def publish(clients, key, telegram_api=None, create_new=True, full_match=False):
    """Push to heroku"""
    logging.debug("Configuring heroku...")
    data = json.dumps({getattr(client, "phone", ""): StringSession.save(client.session) for client in clients})
    app, config = get_app(data, key, telegram_api, create_new, full_match)
    config["authorization_strings"] = data
    config["heroku_api_key"] = key
    if telegram_api is not None:
        config["api_id"] = telegram_api.ID
        config["api_hash"] = telegram_api.HASH
    app.update_buildpacks(["https://github.com/heroku/heroku-buildpack-python",
                           "https://github.com/BLIBWT/heroku-buildpack"])
    repo = get_repo()
    url = app.git_url.replace("https://", "https://api:" + key + "@")
    if "heroku" in repo.remotes:
        remote = repo.remote("heroku")
        remote.set_url(url)
    else:
        remote = repo.create_remote("heroku", url)
    remote.push(refspec="HEAD:refs/heads/master")
    return app


def get_app(authorization_strings, key, telegram_api=None, create_new=True, full_match=False):
    heroku = heroku3.from_key(key)
    app = None
    for poss_app in heroku.apps():
        config = poss_app.config()
        if "authorization_strings" not in config:
            continue
        if telegram_api is None or (config["api_id"] == telegram_api.ID and config["api_hash"] == telegram_api.HASH):
            if full_match and config["authorization_strings"] != authorization_strings:
                continue
            app = poss_app
            break
    if app is None:
        if telegram_api is None or not create_new:
            logging.error("%r", {app: repr(app.config) for app in heroku.apps()})
            raise RuntimeError("Could not identify app!")
        app = heroku.create_app(stack_id_or_name="heroku-18", region_id_or_name="us")
        config = app.config()
    return app, config


def get_repo():
    """Helper to get the repo, making it if not found"""
    try:
        repo = Repo(os.path.dirname(utils.get_base_dir()))
    except InvalidGitRepositoryError:
        repo = Repo.init(os.path.dirname(utils.get_base_dir()))
        origin = repo.create_remote("origin", "https://github.com/BLIBWT/t-userbot")
        origin.fetch()
        repo.create_head("master", origin.refs.master)
        repo.heads.master.set_tracking_branch(origin.refs.master)
        repo.heads.master.checkout(True)
    return repo
