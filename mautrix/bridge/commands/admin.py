# Copyright (c) 2020 Tulir Asokan
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from mautrix.types import EventID
from mautrix.errors import MatrixRequestError, IntentError, MForbidden

from .handler import (command_handler, CommandEvent, SECTION_ADMIN)


@command_handler(needs_admin=True, needs_auth=False, name="set-pl",
                 help_section=SECTION_ADMIN, help_args="<_level_> [_mxid_]",
                 help_text="Set a temporary power level without affecting the remote platform.")
async def set_power_level(evt: CommandEvent) -> EventID:
    try:
        level = int(evt.args[0])
    except (KeyError, IndexError):
        return await evt.reply("**Usage:** `$cmdprefix+sp set-pl <level> [mxid]`")
    except ValueError:
        return await evt.reply("The level must be an integer.")
    mxid = evt.args[1] if len(evt.args) > 1 else evt.sender.mxid
    levels = await evt.main_intent.get_power_levels(evt.room_id, ignore_cache=True)
    levels.users[mxid] = level
    try:
        return await evt.main_intent.set_power_levels(evt.room_id, levels)
    except MForbidden as e:
        await evt.reply(f"I don't seem to have permission to update power levels: {e.message}")
    except (MatrixRequestError, IntentError):
        evt.log.exception("Failed to update power levels")
        return await evt.reply("Failed to update power levels (see logs for more details)")

@command_handler(needs_admin=True, needs_auth=False, name="set-avatar",
                 help_section=SECTION_ADMIN, help_args="<_mxc_uri_> [_mxid_]",
                 help_text="Sets an avatar for a ghost user.")
async def set_ghost_avatar(evt: CommandEvent) -> EventID:
    try:
        mxc_uri = evt.args[0]
    except (KeyError, IndexError):
        return await evt.reply("**Usage:** `$cmdprefix+sp set-avatar <mxc_uri> [mxid]`")
    if not mxc_uri.startswith("mxc://"):
        return await evt.reply("The URI has to start with mxc://.")
    if len(evt.args) > 1:
        puppet = await evt.processor.bridge.get_puppet(evt.args[1])
        if puppet is None:
            return await evt.reply("The given mxid was not a valid ghost user.")
        intent = puppet.intent
    elif evt.is_portal:
        portal = await evt.processor.bridge.get_portal(evt.room_id)
        intent = portal.main_intent
    else:
        return await evt.reply("No mxid given and not in a portal.")
    try:
        return await intent.set_avatar_url(mxc_uri)
    except (MatrixRequestError, IntentError):
        evt.log.exception("Failed to set avatar.")
        return await evt.reply("Failed to set avatar (see logs for more details).")

@command_handler(needs_admin=True, needs_auth=False, name="remove-avatar",
                 help_section=SECTION_ADMIN, help_args="[_mxid_]",
                 help_text="Removes an avatar for a ghost user.")
async def remove_ghost_avatar(evt: CommandEvent) -> EventID:
    if len(evt.args) > 0:
        puppet = await evt.processor.bridge.get_puppet(evt.args[0])
        if puppet is None:
            return await evt.reply("The given mxid was not a valid ghost user.")
        intent = puppet.intent
    elif evt.is_portal:
        portal = await evt.processor.bridge.get_portal(evt.room_id)
        intent = portal.main_intent
    else:
        return await evt.reply("No mxid given and not in a portal.")
    try:
        return await intent.set_avatar_url("")
    except (MatrixRequestError, IntentError):
        evt.log.exception("Failed to remove avatar.")
        return await evt.reply("Failed to remove avatar (see logs for more details).")
