import asyncio
import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

from BrandrdXMusic import app
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import is_active_chat
from BrandrdXMusic.utils.decorators import AdminRightsCheck
from BrandrdXMusic.utils.inline import close_markup, filter_markup
from config import BANNED_USERS


@app.on_message(
    filters.command(["filter", "filters"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def open_filters_menu(client, message: Message, _, chat_id):
    if not await is_active_chat(chat_id):
        return await message.reply_text(_["general_5"])
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["admin_1"])

    current_filter = check[0].get("filter", "Normal").title()
    await message.reply_text(
        f"🎛️ **Audio Filters Control Panel**\n\n"
        f"🎵 **Now Playing:** `{check[0]['title'][:25]}`\n"
        f"⚡ **Active Filter:** `{current_filter}`\n\n"
        f"Choose an audio filter preset below to apply:",
        reply_markup=InlineKeyboardMarkup(filter_markup(chat_id)),
    )


@app.on_message(
    filters.command(["bass", "bassboost", "slowed", "reverb", "nightcore", "8d", "eightd", "vaporwave", "resetfilter", "clearfilter"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def quick_filter_cmd(client, message: Message, _, chat_id):
    if not await is_active_chat(chat_id):
        return await message.reply_text(_["general_5"])
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["admin_1"])

    cmd = message.command[0].lower()
    mapping = {
        "bass": "bass",
        "bassboost": "bassboost",
        "slowed": "slowed",
        "reverb": "slowed",
        "nightcore": "nightcore",
        "8d": "8d",
        "eightd": "8d",
        "vaporwave": "vaporwave",
        "resetfilter": "reset",
        "clearfilter": "reset",
    }
    ftype = mapping.get(cmd, "reset")
    file_path = check[0]["file"]
    status_msg = await message.reply_text(f"⏳ **Applying `{ftype.title()}` filter... Please wait.**")
    try:
        await Hotty.apply_audio_filter(chat_id, file_path, ftype, check)
        await status_msg.edit_text(
            f"🎛️ **Audio Filter Applied**: `{ftype.title()}`\n└ ʙʏ : {message.from_user.mention}",
            reply_markup=close_markup(_),
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ **Failed to apply filter**: `{e}`")
