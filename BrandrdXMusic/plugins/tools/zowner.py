import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import add_served_chat, get_assistant


@app.on_message(filters.command(["owner", "developer", "dev"]))
async def owner_info(client: Client, message: Message):
    text = (
        f"👑 <b>ᴏᴡɴᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>\n\n"
        f"👤 <b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{config.OWNER_USERNAME}\n"
        f"🆔 <b>ᴏᴡɴᴇʀ ɪᴅ :</b> <code>{config.OWNER_ID}</code>\n"
        f"💬 <b>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ :</b> <a href=\"{config.SUPPORT_CHAT}\">amrit_feel</a> (<code>{config.SUPPORT_CHAT_ID}</code>)\n"
        f"📢 <b>ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ :</b> <a href=\"{config.SUPPORT_CHANNEL}\">privatethink</a>\n"
        f"📸 <b>ɪɴsᴛᴀɢʀᴀᴍ :</b> <a href=\"{config.OWNER_INSTAGRAM}\">{config.OWNER_USERNAME}</a>\n"
        f"👻 <b>sɴᴀᴘᴄʜᴀᴛ :</b> <a href=\"{config.OWNER_SNAPCHAT}\">{config.OWNER_USERNAME}</a>\n"
    )
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url=f"https://t.me/{config.OWNER_USERNAME}"),
                InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT),
            ],
            [
                InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url=config.SUPPORT_CHANNEL),
            ],
            [
                InlineKeyboardButton("📸 ɪɴsᴛᴀɢʀᴀᴍ", url=config.OWNER_INSTAGRAM),
                InlineKeyboardButton("👻 sɴᴀᴘᴄʜᴀᴛ", url=config.OWNER_SNAPCHAT),
            ],
        ]
    )
    if message.reply_to_message:
        await message.reply_to_message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["repo", "source"]))
async def repo_info(client: Client, message: Message):
    text = (
        f"✨ <b>ʙʀᴀɴᴅʀᴅ x ᴍᴜsɪᴄ ʙᴏᴛ</b>\n\n"
        f"🚀 <b>24×7 Kᴏʏᴇʙ Rᴇᴀᴅʏ & Bᴜɢ-Fʀᴇᴇ</b>\n"
        f"👤 <b>Oᴡɴᴇʀ :</b> @{config.OWNER_USERNAME}\n"
        f"💬 <b>Sᴜᴘᴘᴏʀᴛ :</b> <a href=\"{config.SUPPORT_CHAT}\">amrit_feel</a>\n"
        f"📢 <b>Cʜᴀɴɴᴇʟ :</b> <a href=\"{config.SUPPORT_CHANNEL}\">privatethink</a>\n"
    )
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url=f"https://t.me/{config.OWNER_USERNAME}"),
                InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_CHAT),
            ],
            [
                InlineKeyboardButton("📢 ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ", url=config.SUPPORT_CHANNEL),
            ],
        ]
    )
    await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["clone"]))
async def clones(client: Client, message: Message):
    await message.reply_text(
        f"🙂 <b>Cᴏɴᴛᴀᴄᴛ Oᴡɴᴇʀ @{config.OWNER_USERNAME} ᴛᴏ ʜᴏsᴛ ʏᴏᴜʀ ᴏᴡɴ ᴍᴜsɪᴄ ʙᴏᴛ!</b>",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👤 ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ", url=f"https://t.me/{config.OWNER_USERNAME}"),
                    InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=config.SUPPORT_CHAT),
                ]
            ]
        ),
        parse_mode=ParseMode.HTML,
    )


@app.on_message(
    filters.command(
        ["hi", "hii", "hello", "hui", "good", "gm", "ok", "bye", "welcome", "thanks"],
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"],
    )
    & filters.group
)
async def bot_check(_, message):
    chat_id = message.chat.id
    await add_served_chat(chat_id)


@app.on_message(filters.command("gadd") & (filters.user(config.OWNER_ID) | SUDOERS))
async def add_allbot(client, message):
    command_parts = message.text.split(" ")
    if len(command_parts) != 2:
        return await message.reply(
            f"**⚠️ ɪɴᴠᴀʟɪᴅ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀᴍᴀᴛ. ᴘʟᴇᴀsᴇ ᴜsᴇ ʟɪᴋᴇ » `/gadd @{app.username}`**"
        )

    bot_username = command_parts[1].replace("@", "")
    try:
        userbot = await get_assistant(message.chat.id)
        bot = await app.get_users(bot_username)
        app_id = bot.id
        done = 0
        failed = 0
        lol = await message.reply("🔄 **ᴀᴅᴅɪɴɢ ɢɪᴠᴇɴ ʙᴏᴛ ɪɴ ᴀʟʟ ᴄʜᴀᴛs!**")
        try:
            await userbot.send_message(bot_username, "/start")
        except Exception:
            pass
        async for dialog in userbot.get_dialogs():
            try:
                await userbot.add_chat_members(dialog.chat.id, app_id)
                done += 1
            except Exception:
                failed += 1
            await asyncio.sleep(2)

        await lol.edit(
            f"**➻ @{bot_username} ʙᴏᴛ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ🎉**\n\n"
            f"**➥ ᴀᴅᴅᴇᴅ ɪɴ {done} ᴄʜᴀᴛs ✅**\n"
            f"**➥ ғᴀɪʟᴇᴅ ɪɴ {failed} ᴄʜᴀᴛs ❌**\n\n"
            f"**➲ ᴀᴅᴅᴇᴅ ʙʏ»** @{userbot.username}"
        )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")


__MODULE__ = "Oᴡɴᴇʀ"
__HELP__ = """
## Oᴡɴᴇʀ & Sᴏᴜʀᴄᴇ Mᴏᴅᴜʟᴇ

### Cᴏᴍᴍᴀɴᴅs:
- `/owner`: Gᴇᴛ ᴛʜᴇ ᴏᴡɴᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ (Username, ID, Group, Channel, Instagram, Snapchat).
- `/repo` ᴏʀ `/source`: Gᴇᴛ ᴛʜᴇ ʙᴏᴛ's ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀɴᴅ sᴜᴘᴘᴏʀᴛ ʟɪɴᴋs.
"""
