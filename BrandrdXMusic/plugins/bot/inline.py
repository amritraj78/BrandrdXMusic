from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
)
from py_yt import VideosSearch

from BrandrdXMusic import app
from BrandrdXMusic.utils.inlinequery import answer
from config import BANNED_USERS


@app.on_inline_query(~BANNED_USERS)
async def inline_query_handler(client, query):
    text = query.query.strip().lower()
    answers = []
    if text.strip() == "":
        try:
            await client.answer_inline_query(query.id, results=answer, cache_time=10)
        except:
            return
    else:
        try:
            res_dict = await a.next()
            result = res_dict.get("result") if isinstance(res_dict, dict) else []
        except Exception:
            result = []
        if not result:
            return
        for item in result[:15]:
            title = (item.get("title") or "Track").title()
            duration = item.get("duration") or "0:00"
            views_dict = item.get("viewCount")
            views = views_dict.get("short", "0") if isinstance(views_dict, dict) else "0"
            thumbs = item.get("thumbnails")
            thumbnail = thumbs[0]["url"].split("?")[0] if thumbs and len(thumbs) > 0 else "https://te.legra.ph/file/ba39a10ba20736f42f202.jpg"
            channel_info = item.get("channel") or {}
            channellink = channel_info.get("link", "https://youtube.com")
            channel = channel_info.get("name", "YouTube")
            link = item.get("link", f"https://youtube.com/watch?v={item.get('id', '')}")
            published = item.get("publishedTime", "")
            description = f"{views} | {duration} ᴍɪɴᴜᴛᴇs | {channel}  | {published}"
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʏᴏᴜᴛᴜʙᴇ 🎄",
                            url=link,
                        )
                    ],
                ]
            )
            searched_text = f"""
❄ <b>ᴛɪᴛʟᴇ :</b> <a href={link}>{title}</a>

⏳ <b>ᴅᴜʀᴀᴛɪᴏɴ :</b> {duration} ᴍɪɴᴜᴛᴇs
👀 <b>ᴠɪᴇᴡs :</b> <code>{views}</code>
🎥 <b>ᴄʜᴀɴɴᴇʟ :</b> <a href={channellink}>{channel}</a>
⏰ <b>ᴘᴜʙʟɪsʜᴇᴅ ᴏɴ :</b> {published}


<u><b>➻ ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴍᴏᴅᴇ ʙʏ {app.name}</b></u>"""
            answers.append(
                InlineQueryResultPhoto(
                    photo_url=thumbnail,
                    title=title,
                    thumb_url=thumbnail,
                    description=description,
                    caption=searched_text,
                    reply_markup=buttons,
                )
            )
        try:
            return await client.answer_inline_query(query.id, results=answers)
        except:
            return

