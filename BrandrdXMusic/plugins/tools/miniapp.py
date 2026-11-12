from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

import config
from BrandrdXMusic import app
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import is_active_chat


@app.on_message(filters.command(["miniapp", "app", "web"]) & ~config.BANNED_USERS)
async def miniapp_command(cli, message: Message):
    chat_id = message.chat.id
    web_app_url = getattr(
        config,
        "WEB_APP_URL",
        "https://brandrd-music-animeworlds-b77dd182.apps.mistral.run",
    )

    if message.chat.type.name in ["GROUP", "SUPERGROUP"]:
        is_active = await is_active_chat(chat_id) and bool(db.get(chat_id))
        status_txt = "🟢 <b>sᴛʀᴇᴀᴍɪɴɢ ɪɴ ᴠᴄ</b>" if is_active else "⚪ <b>ɴᴏ ᴀᴄᴛɪᴠᴇ sᴛʀᴇᴀᴍ</b>"

        buttons = [
            [
                InlineKeyboardButton(
                    text="📱 ᴏᴘᴇɴ ᴍᴜsɪᴄ ᴍɪɴɪ ᴀᴘᴘ",
                    web_app=WebAppInfo(url=f"{web_app_url}/webapp?chat_id={chat_id}"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗳️ ᴠᴏᴛᴇ ᴛᴏ sᴋɪᴘ",
                    callback_data=f"VoteSkip|{chat_id}",
                ),
                InlineKeyboardButton(
                    text="🗑️ ᴄʟᴏsᴇ",
                    callback_data="close",
                ),
            ],
        ]

        text = (
            f"📱 <b>ʙʀᴀɴᴅʀᴅx ᴍᴜsɪᴄ ᴍɪɴɪ ᴀᴘᴘ</b>\n\n"
            f"» <b>ɢʀᴏᴜᴘ :</b> {message.chat.title}\n"
            f"» <b>sᴛᴀᴛᴜs :</b> {status_txt}\n\n"
            f"⚡ <b>ғᴇᴀᴛᴜʀᴇs :</b>\n"
            f"• 📋 <b>ʟɪᴠᴇ ǫᴜᴇᴜᴇ :</b> Real-time now-playing player & queue tracker.\n"
            f"• 🔍 <b>sᴇᴀʀᴄʜ & ǫᴜᴇᴜᴇ :</b> Search songs & add to VC with 1-click.\n"
            f"• 🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ :</b> Fair democratic skipping for group members."
        )
        return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    else:
        # Private chat
        buttons = [
            [
                InlineKeyboardButton(
                    text="📱 ᴏᴘᴇɴ ᴡᴇʙ ᴘʟᴀʏᴇʀ",
                    web_app=WebAppInfo(url=f"{web_app_url}/webapp"),
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
        ]
        text = (
            f"📱 <b>ʙʀᴀɴᴅʀᴅx ᴍᴜsɪᴄ ᴍɪɴɪ ᴀᴘᴘ</b>\n\n"
            f"» Open the Mini App to search music, browse queues, and interact with the player.\n"
            f"» To use all interactive group features (live queue & vote-to-skip), add me to your group!"
        )
        return await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
