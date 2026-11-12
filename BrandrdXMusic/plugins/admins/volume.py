from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from BrandrdXMusic import app
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import db
from BrandrdXMusic.plugins.admins.callback import current_volume
from BrandrdXMusic.utils.database import is_active_chat
from BrandrdXMusic.utils.decorators import AdminRightsCheck
from config import BANNED_USERS


@app.on_message(
    filters.command(["volume", "vol"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def volume_cmd(client, message: Message, _):
    chat_id = message.chat.id
    if not await is_active_chat(chat_id):
        return await message.reply_text(_["general_5"])

    if len(message.command) == 1:
        vol = current_volume.get(chat_id, 100)
        buttons = [
            [
                InlineKeyboardButton(text="🔉 -15%", callback_data=f"ADMIN VolDown|{chat_id}"),
                InlineKeyboardButton(text="🔊 +15%", callback_data=f"ADMIN VolUp|{chat_id}"),
            ],
            [
                InlineKeyboardButton(text="🔄 Reset to 100%", callback_data=f"ADMIN Vol100|{chat_id}"),
                InlineKeyboardButton(text="❌ Close", callback_data="close"),
            ],
        ]
        return await message.reply_text(
            f"🔊 **Volume Controller**\n\n"
            f"Current stream volume: **{vol}%**\n"
            f"Use `/volume <1-200>` or click buttons below:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    try:
        vol = int(message.text.split(None, 1)[1].strip())
    except Exception:
        return await message.reply_text("❗ **Invalid format.** Use: `/volume 120` (range 1-200).")

    if vol < 1 or vol > 200:
        return await message.reply_text("❗ **Volume must be between 1 and 200.**")

    current_volume[chat_id] = vol
    ok = await Hotty.set_volume(chat_id, vol)
    if ok:
        await message.reply_text(f"🔊 **Volume set to {vol}%**\n└ ʙʏ : {message.from_user.mention}")
    else:
        await message.reply_text(f"🔊 **Volume updated to {vol}%** (will apply to subsequent stream segments).")
