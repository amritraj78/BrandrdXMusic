from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

import config
from BrandrdXMusic import app, LOGGER
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import is_active_chat, group_assistant
from BrandrdXMusic.utils.web import vote_skip_pool

VOTES_NEEDED = 2


@app.on_message(filters.command(["voteskip", "skipvote"]) & filters.group & ~config.BANNED_USERS)
async def vote_skip_command(cli, message: Message):
    chat_id = message.chat.id
    if not await is_active_chat(chat_id) or not db.get(chat_id):
        return await message.reply_text("» ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʀɪɢʜᴛ ɴᴏᴡ.")

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    current_track = db[chat_id][0]
    title = current_track.get("title", "Track")

    if chat_id not in vote_skip_pool:
        vote_skip_pool[chat_id] = {}

    votes = vote_skip_pool[chat_id]

    if user_id in votes:
        return await message.reply_text(
            f"🗳️ <b>ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴠᴏᴛᴇᴅ ᴛᴏ sᴋɪᴘ!</b>\n\n» <b>ᴛʀᴀᴄᴋ :</b> {title[:30]}\n» <b>ᴠᴏᴛᴇs :</b> {len(votes)}/{VOTES_NEEDED} ɴᴇᴇᴅᴇᴅ."
        )

    votes[user_id] = user_name
    count = len(votes)

    if count >= VOTES_NEEDED:
        vote_skip_pool[chat_id] = {}
        try:
            assistant = await group_assistant(Hotty, chat_id)
            await Hotty.change_stream(assistant, chat_id)
            await message.reply_text(
                f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ ᴘᴀssᴇᴅ!</b>\n\n» {VOTES_NEEDED}/{VOTES_NEEDED} ᴠᴏᴛᴇs ʀᴇᴀᴄʜᴇᴅ ʙʏ ᴍᴇᴍʙᴇʀs.\n» ɴᴏᴡ ᴘʟᴀʏɪɴɢ ɴᴇxᴛ ᴛʀᴀᴄᴋ!"
            )
        except Exception as e:
            LOGGER(__name__).error(f"vote_skip_command error: {e}")
            await message.reply_text("» ғᴀɪʟᴇᴅ ᴛᴏ sᴋɪᴘ ᴛʀᴀᴄᴋ.")
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"🗳️ ᴠᴏᴛᴇ ᴛᴏ sᴋɪᴘ ({count}/{VOTES_NEEDED})",
                    callback_data=f"VoteSkip|{chat_id}",
                )
            ]
        ]
        await message.reply_text(
            f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ ɪɴɪᴛɪᴀᴛᴇᴅ!</b>\n\n» <b>ᴠᴏᴛᴇᴅ ʙʏ :</b> {message.from_user.mention}\n» <b>ᴛʀᴀᴄᴋ :</b> {title[:30]}\n» <b>ᴠᴏᴛᴇs :</b> {count}/{VOTES_NEEDED} ɴᴇᴇᴅᴇᴅ ᴛᴏ sᴋɪᴘ.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@app.on_callback_query(filters.regex(r"^VoteSkip\|(-?\d+)$"))
async def vote_skip_callback(cli, callback_query: CallbackQuery):
    chat_id = int(callback_query.data.split("|")[1])
    if not await is_active_chat(chat_id) or not db.get(chat_id):
        return await callback_query.answer("Nothing is playing in voice chat right now.", show_alert=True)

    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name
    current_track = db[chat_id][0]
    title = current_track.get("title", "Track")

    if chat_id not in vote_skip_pool:
        vote_skip_pool[chat_id] = {}

    votes = vote_skip_pool[chat_id]

    if user_id in votes:
        return await callback_query.answer(
            f"You have already voted! ({len(votes)}/{VOTES_NEEDED} votes)",
            show_alert=True,
        )

    votes[user_id] = user_name
    count = len(votes)

    if count >= VOTES_NEEDED:
        vote_skip_pool[chat_id] = {}
        await callback_query.answer("Vote passed! Skipping to next song...", show_alert=True)
        try:
            assistant = await group_assistant(Hotty, chat_id)
            await Hotty.change_stream(assistant, chat_id)
            await callback_query.message.edit_text(
                f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ ᴘᴀssᴇᴅ!</b>\n\n» {VOTES_NEEDED}/{VOTES_NEEDED} ᴠᴏᴛᴇs ʀᴇᴀᴄʜᴇᴅ ʙʏ ᴍᴇᴍʙᴇʀs.\n» ɴᴏᴡ ᴘʟᴀʏɪɴɢ ɴᴇxᴛ ᴛʀᴀᴄᴋ!"
            )
        except Exception as e:
            LOGGER(__name__).error(f"vote_skip_callback error: {e}")
    else:
        await callback_query.answer(f"Vote counted! ({count}/{VOTES_NEEDED})", show_alert=False)
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"🗳️ ᴠᴏᴛᴇ ᴛᴏ sᴋɪᴘ ({count}/{VOTES_NEEDED})",
                    callback_data=f"VoteSkip|{chat_id}",
                )
            ]
        ]
        try:
            await callback_query.message.edit_text(
                f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ ɪɴ ᴘʀᴏɢʀᴇss!</b>\n\n» <b>ʟᴀsᴛ ᴠᴏᴛᴇ :</b> {callback_query.from_user.mention}\n» <b>ᴛʀᴀᴄᴋ :</b> {title[:30]}\n» <b>ᴠᴏᴛᴇs :</b> {count}/{VOTES_NEEDED} ɴᴇᴇᴅᴇᴅ ᴛᴏ sᴋɪᴘ.",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        except Exception:
            pass
