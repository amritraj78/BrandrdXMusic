
import asyncio
import time
from pyrogram import filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from BrandrdXMusic import YouTube, app
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import SUDOERS, db
from BrandrdXMusic.utils.database import (
    get_active_chats,
    get_lang,
    get_loop,
    get_upvote_count,
    is_active_chat,
    is_music_playing,
    is_nonadmin_chat,
    music_off,
    music_on,
    set_loop,
)
from BrandrdXMusic.utils.decorators.language import languageCB
from BrandrdXMusic.utils.formatters import seconds_to_min
from BrandrdXMusic.utils.inline import (
    close_markup,
    filter_markup,
    stream_markup,
    stream_markup_timer,
    stream_markup_timer2,
)
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb
from config import (
    BANNED_USERS,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
)
from strings import get_string

checker = {}
upvoters = {}
current_volume = {}
wrong = {}
last_timer_edit = {}


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention
    if command == "UpVote":
        if chat_id not in votemode:
            votemode[chat_id] = {}
        if chat_id not in upvoters:
            upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters:
            upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote:
            votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] += 1
        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])
        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
            except:
                return await CallbackQuery.edit_message_text(f"ғᴀɪʟᴇᴅ.")
            try:
                if current["vidid"] != exists["vidid"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
                if current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
            except:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except:
                pass
            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"
        else:
            if (
                CallbackQuery.from_user.id
                in upvoters[chat_id][CallbackQuery.message.id]
            ):
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"👍 {get_upvotes}",
                            callback_data=f"ADMIN  UpVote|{chat_id}_{counter}",
                        )
                    ]
                ]
            )
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
                if not admins:
                    try:
                        admins = []
                        async for m in app.get_chat_administrators(CallbackQuery.message.chat.id):
                            if m.user:
                                admins.append(m.user.id)
                        adminlist[CallbackQuery.message.chat.id] = admins
                    except Exception:
                        pass
                if not admins:
                    return await CallbackQuery.answer(_["admin_13"], show_alert=True)
                else:
                    if CallbackQuery.from_user.id not in admins:
                        return await CallbackQuery.answer(
                            _["admin_14"], show_alert=True
                        )
    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await Hotty.pause_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_2"].format(mention), reply_markup=close_markup(_)
        )
    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await Hotty.resume_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_4"].format(mention), reply_markup=close_markup(_)
        )
    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await Hotty.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        if chat_id in wrong:
            wrong.pop(chat_id, None)
        await CallbackQuery.message.reply_text(
            _["admin_5"].format(mention), reply_markup=close_markup(_)
        )
        await CallbackQuery.message.delete()
    elif command == "VolUp" or command == "VolDown":
        vol = current_volume.get(chat_id, 100)
        vol = min(200, vol + 15) if command == "VolUp" else max(10, vol - 15)
        current_volume[chat_id] = vol
        await Hotty.set_volume(chat_id, vol)
        return await CallbackQuery.answer(f"🔊 Volume set to: {vol}%", show_alert=False)
    elif command == "Vol100":
        current_volume[chat_id] = 100
        await Hotty.set_volume(chat_id, 100)
        return await CallbackQuery.answer("🔊 Volume reset to 100%", show_alert=False)
    elif command == "ToggleDJ":
        from BrandrdXMusic.utils.database import get_playtype, set_playtype
        cur = await get_playtype(chat_id)
        new_mode = "Everyone" if cur == "Admin" else "Admin"
        await set_playtype(chat_id, new_mode)
        status_str = "Enabled (Admins/Auth Only)" if new_mode == "Admin" else "Disabled (Everyone)"
        return await CallbackQuery.answer(f"🎧 DJ Mode: {status_str}", show_alert=True)
    elif command == "Shuffle":
        check = db.get(chat_id)
        if not check or len(check) <= 1:
            return await CallbackQuery.answer("Queue has too few tracks to shuffle.", show_alert=True)
        first = check.pop(0)
        import random
        random.shuffle(check)
        check.insert(0, first)
        return await CallbackQuery.answer("🔀 Queue shuffled successfully!", show_alert=False)
    elif command == "Loop":
        loop = await get_loop(chat_id)
        new_loop = 3 if loop == 0 else 0
        await set_loop(chat_id, new_loop)
        txt = "🔁 Loop enabled (3x)" if new_loop > 0 else "🔁 Loop disabled"
        return await CallbackQuery.answer(txt, show_alert=False)
    elif command == "FilterMenu":
        wrong.setdefault(chat_id, {})[CallbackQuery.message.id] = False
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(filter_markup(chat_id))
        )
    elif command == "BackToPlayer":
        wrong.setdefault(chat_id, {})[CallbackQuery.message.id] = True
        check = db.get(chat_id)
        vidid = check[0]["vidid"] if check else ""
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(stream_markup(_, vidid, chat_id))
        )
    elif command.startswith("Filter_"):
        ftype = command.split("_", 1)[1]
        check = db.get(chat_id)
        if not check:
            return await CallbackQuery.answer("Nothing is currently playing.", show_alert=True)
        file_path = check[0]["file"]
        await CallbackQuery.answer(f"Applying filter: {ftype.title()}...", show_alert=False)
        try:
            await Hotty.apply_audio_filter(chat_id, file_path, ftype, check)
            await CallbackQuery.message.reply_text(
                f"🎛️ **Audio Filter Applied**: `{ftype.title()}`\n└ ʙʏ : {mention}",
                reply_markup=close_markup(_),
            )
        except Exception as e:
            return await CallbackQuery.answer(f"Failed to apply filter: {e}", show_alert=True)
        return
    elif command == "Skip" or command == "Replay":
        check = db.get(chat_id)
        if command == "Skip":
            txt = f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
            popped = None
            try:
                popped = check.pop(0)
                if popped:
                    await auto_clean(popped)
                if not check:
                    await CallbackQuery.edit_message_text(
                        f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
                    )
                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    try:
                        return await Hotty.stop_stream(chat_id)
                    except:
                        return
            except:
                try:
                    await CallbackQuery.edit_message_text(
                        f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
                    )
                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    return await Hotty.stop_stream(chat_id)
                except:
                    return
        else:
            txt = f"➻ sᴛʀᴇᴀᴍ ʀᴇ-ᴘʟᴀʏᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
        await CallbackQuery.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        duration = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await CallbackQuery.message.reply_text(
                    text=_["admin_7"].format(title),
                    reply_markup=close_markup(_),
                )
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Hotty.skip_stream(chat_id, link, video=status, image=image)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            button = stream_markup2(_, chat_id)
            img = await get_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
        elif "vid_" in queued:
            mystic = await CallbackQuery.message.reply_text(
                _["call_7"], disable_web_page_preview=True
            )
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=status,
                    title=title,
                    direct_stream=(not status),
                )
            except:
                return await mystic.edit_text(_["call_6"])
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Hotty.skip_stream(chat_id, file_path, video=status, image=image)
            except:
                return await mystic.edit_text(_["call_6"])
            button = stream_markup(_, videoid, chat_id)
            img = await get_thumb(videoid)
            run = await CallbackQuery.message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            try:
                await mystic.delete()
            except Exception:
                pass
            await Hotty.precache_next_track(chat_id)
        elif "index_" in queued:
            try:
                await Hotty.skip_stream(chat_id, videoid, video=status)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            button = stream_markup2(_, chat_id)
            run = await CallbackQuery.message.reply_photo(
                photo=STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
        else:
            if videoid == "telegram":
                image = None
            elif videoid == "soundcloud":
                image = None
            else:
                try:
                    image = await YouTube.thumbnail(videoid, True)
                except:
                    image = None
            try:
                await Hotty.skip_stream(chat_id, queued, video=status, image=image)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            if videoid == "telegram":
                button = stream_markup2(_, chat_id)
                run = await CallbackQuery.message.reply_photo(
                    photo=TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    caption=_["stream_1"].format(
                        config.SUPPORT_CHAT, title[:23], duration, user
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif videoid == "soundcloud":
                button = stream_markup2(_, chat_id)
                run = await CallbackQuery.message.reply_photo(
                    photo=SOUNCLOUD_IMG_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    caption=_["stream_1"].format(
                        config.SUPPORT_CHAT, title[:23], duration, user
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                button = stream_markup(_, videoid, chat_id)
                img = await get_thumb(videoid)
                run = await CallbackQuery.message.reply_photo(
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        duration,
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await Hotty.precache_next_track(chat_id)


async def markup_timer():
    while not await asyncio.sleep(7):
        try:
            active_chats = await get_active_chats()
        except Exception:
            continue
        now = time.time()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration_seconds = int(playing[0].get("seconds", 0))
                if duration_seconds == 0:
                    continue
                mystic = playing[0].get("mystic")
                markup = playing[0].get("markup")
                if not mystic:
                    continue
                if wrong.get(chat_id, {}).get(mystic.id) is False:
                    continue
                if now - last_timer_edit.get(mystic.id, 0) < 6.5:
                    continue
                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except Exception:
                    _ = get_string("en")
                buttons = (
                    stream_markup_timer(
                        _,
                        playing[0].get("vidid"),
                        chat_id,
                        seconds_to_min(playing[0]["played"]),
                        playing[0]["dur"],
                    )
                    if markup == "stream"
                    else stream_markup_timer2(
                        _,
                        chat_id,
                        seconds_to_min(playing[0]["played"]),
                        playing[0]["dur"],
                    )
                )
                await mystic.edit_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                last_timer_edit[mystic.id] = now
            except FloodWait as fw:
                last_timer_edit[mystic.id] = time.time() + fw.value
            except MessageNotModified:
                last_timer_edit[mystic.id] = time.time()
            except Exception:
                continue

        # Prune old cache if oversized
        if len(last_timer_edit) > 200:
            last_timer_edit.clear()


asyncio.create_task(markup_timer())

