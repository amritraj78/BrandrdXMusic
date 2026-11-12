import os
import re
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
    Message,
)

from config import (
    BANNED_USERS,
    SONG_DOWNLOAD_DURATION,
    SONG_DOWNLOAD_DURATION_LIMIT,
)
from BrandrdXMusic import YouTube, app
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.formatters import convert_bytes
from BrandrdXMusic.utils.inline.song import song_markup

# Song Module

@app.on_message(filters.command(["song"]))
@language
async def song_commad_private(client, message: Message, _):
    await message.delete()
    url = await YouTube.url(message)
    if url:
        if not await YouTube.exists(url):
            return await message.reply_text(_["song_5"])
        mystic = await message.reply_text(_["play_1"])
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(url)
        if str(duration_min) == "None":
            return await mystic.edit_text(_["song_3"])
        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_4"].format(
                    SONG_DOWNLOAD_DURATION, duration_min
                )
            )
        buttons = song_markup(_, vidid)
        await mystic.delete()
        await message.reply_photo(
            thumbnail,
            caption=_["song_4"].format(title),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["song_2"])
    mystic = await message.reply_text(_["play_1"])
    query = message.text.split(None, 1)[1]
    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(query)
    except:
        return await mystic.edit_text(_["play_3"])
    if str(duration_min) == "None":
        return await mystic.edit_text(_["song_3"])
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            _["play_6"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )
    buttons = song_markup(_, vidid)
    await mystic.delete()
    await message.reply_photo(
        thumbnail,
        caption=_["song_4"].format(title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex(pattern=r"song_back") & ~BANNED_USERS)
@languageCB
async def songs_back_helper(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup(_, vidid)
    await callback_query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(pattern=r"song_helper") & ~BANNED_USERS)
@languageCB
async def song_helper_cb(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    try:
        await callback_query.answer(_["song_6"], show_alert=True)
    except:
        pass
    if stype == "audio":
        try:
            formats_available, link = await YouTube.formats(
                vidid, True
            )
        except Exception as e:
            LOGGER(__name__).error("formats error: %s", e)
            return await callback_query.edit_message_text(_["song_7"])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = []
        for x in formats_available:
            check = x.get("format", "")
            if "audio" in check or "mp3" in check:
                form = str(x.get("format_note", "Standard")).title()
                if form not in done:
                    done.append(form)
                else:
                    continue
                sz = convert_bytes(x["filesize"]) if x.get("filesize") else "Audio"
                fom = x.get("format_id", "bestaudio")
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"{form} Quality Audio = {sz}",
                            callback_data=f"song_download {stype}|{fom}|{vidid}",
                        ),
                    ]
                )
        if not keyboard.inline_keyboard:
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Download Audio (MP3)",
                        callback_data=f"song_download {stype}|bestaudio|{vidid}",
                    ),
                ]
            )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"song_back {stype}|{vidid}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data=f"close"
                ),
            ]
        )
        await callback_query.edit_message_reply_markup(
            reply_markup=keyboard
        )
    else:
        try:
            formats_available, link = await YouTube.formats(
                vidid, True
            )
        except Exception as e:
            LOGGER(__name__).error("formats video error: %s", e)
            return await callback_query.edit_message_text(_["song_7"])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266, 18, 22]
        for x in formats_available:
            check = x.get("format", "")
            fid = x.get("format_id", "")
            try:
                if int(fid) not in done:
                    continue
            except (ValueError, TypeError):
                pass
            sz = convert_bytes(x["filesize"]) if x.get("filesize") else "Video"
            ap = check.split("-")[1] if "-" in check else x.get("format_note", "MP4")
            to = f"{ap} = {sz}"
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=to,
                        callback_data=f"song_download {stype}|{fid}|{vidid}",
                    ),
                ]
            )
        if not keyboard.inline_keyboard:
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Download Video (MP4)",
                        callback_data=f"song_download {stype}|best|{vidid}",
                    ),
                ]
            )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"song_back {stype}|{vidid}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data=f"close"
                ),
            ]
        )
        await callback_query.edit_message_reply_markup(
            reply_markup=keyboard
        )

# Downloading Songs Here

@app.on_callback_query(
    filters.regex(pattern=r"song_download") & ~BANNED_USERS
)
@languageCB
async def song_download_cb(client, callback_query: CallbackQuery, _) :
    try:
        await callback_query.answer("ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...")
    except:
        pass
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")
    mystic = await callback_query.edit_message_text(_["song_8"])
    yturl = f"https://www.youtube.com/watch?v={vidid}"
    try:
        title, duration_min, duration_sec, thumbnail, vid_res = await YouTube.details(vidid, True)
    except Exception:
        title = "Track"
        duration_sec = 0
    title = re.sub(r"\W+", " ", title)
    try:
        thumb_image_path = await callback_query.message.download()
    except Exception:
        thumb_image_path = None
    duration = duration_sec
    if stype == "video":
        width = getattr(callback_query.message.photo, "width", 1280) if callback_query.message.photo else 1280
        height = getattr(callback_query.message.photo, "height", 720) if callback_query.message.photo else 720
        try:
            download_res = await YouTube.download(
                yturl,
                mystic,
                video=True,
                format_id=format_id,
                title=title,
            )
            file_path = download_res[0] if isinstance(download_res, tuple) else download_res
            if not file_path:
                return await mystic.edit_text(_["song_9"].format("Download failed"))
        except Exception as e:
            return await mystic.edit_text(_["song_9"].format(e))
        med = InputMediaVideo(
            media=file_path,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=title,
            supports_streaming=True,
        )
        await mystic.edit_text(_["song_11"])
        await app.send_chat_action(
            chat_id=callback_query.message.chat.id,
            action="upload_video",
        )
        try:
            await callback_query.edit_message_media(media=med)
        except Exception as e:
            LOGGER(__name__).error("upload video error: %s", e)
            return await mystic.edit_text(_["song_10"])
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    elif stype == "audio":
        try:
            download_res = await YouTube.download(
                yturl,
                mystic,
                video=False,
                format_id=format_id,
                title=title,
            )
            filename = download_res[0] if isinstance(download_res, tuple) else download_res
            if not filename:
                return await mystic.edit_text(_["song_9"].format("Download failed"))
        except Exception as e:
            return await mystic.edit_text(_["song_9"].format(e))
        med = InputMediaAudio(
            media=filename,
            caption=title,
            thumb=thumb_image_path,
            title=title,
            performer="BrandrdXMusic",
        )
        await mystic.edit_text(_["song_11"])
        await app.send_chat_action(
            chat_id=callback_query.message.chat.id,
            action="upload_audio",
        )
        try:
            await callback_query.edit_message_media(media=med)
        except Exception as e:
            LOGGER(__name__).error("upload audio error: %s", e)
            return await mystic.edit_text(_["song_10"])
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass
