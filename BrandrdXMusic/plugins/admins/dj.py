from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from BrandrdXMusic import app
from BrandrdXMusic.utils.database import get_playtype, set_playtype
from BrandrdXMusic.utils.decorators import AdminActual
from config import BANNED_USERS


@app.on_message(
    filters.command(["dj", "djmode"])
    & filters.group
    & ~BANNED_USERS
)
@AdminActual
async def dj_mode_cmd(client, message: Message, _):
    chat_id = message.chat.id
    current_mode = await get_playtype(chat_id)

    if len(message.command) == 1:
        status_text = "🔒 **Enabled (Admins/Auth Only)**" if current_mode == "Admin" else "🔓 **Disabled (Everyone)**"
        button = [
            [
                InlineKeyboardButton(
                    text="🎧 Toggle DJ Mode",
                    callback_data=f"ADMIN ToggleDJ|{chat_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Close",
                    callback_data="close",
                ),
            ],
        ]
        return await message.reply_text(
            f"🎧 **DJ Mode Settings**\n\n"
            f"Current DJ Mode: {status_text}\n\n"
            f"• When **Enabled**: Only Group Admins and Authorized users can play and control music.\n"
            f"• When **Disabled**: Anyone in the group can play songs.\n\n"
            f"Use `/dj on` or `/dj off` or tap the button below:",
            reply_markup=InlineKeyboardMarkup(button),
        )

    arg = message.command[1].lower()
    if arg in ("on", "enable", "admin"):
        await set_playtype(chat_id, "Admin")
        await message.reply_text(
            "🎧 **DJ Mode Enabled!**\n\n"
            "Now only **Group Admins** and **Authorized Users** can play and manage music.\n"
            f"└ ʙʏ : {message.from_user.mention}"
        )
    elif arg in ("off", "disable", "everyone"):
        await set_playtype(chat_id, "Everyone")
        await message.reply_text(
            "👥 **DJ Mode Disabled!**\n\n"
            "Now **everyone** in this group can play songs.\n"
            f"└ ʙʏ : {message.from_user.mention}"
        )
    else:
        await message.reply_text("❗ **Usage:** `/dj on` or `/dj off`")
