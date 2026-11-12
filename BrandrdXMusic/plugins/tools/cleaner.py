try:
    import psutil
except ImportError:
    psutil = None
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.cleaner import clean_storage_and_memory


def cleaner_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🗑️ Clean Storage & RAM", callback_data="clean_storage_action"),
                InlineKeyboardButton("🔄 Refresh Stats", callback_data="clean_storage_refresh"),
            ],
            [
                InlineKeyboardButton("🗑️ Deep Wipe", callback_data="clean_storage_deep"),
                InlineKeyboardButton("❌ Close", callback_data="close"),
            ],
        ]
    )


def format_clean_text(data: dict, action: str = "Status") -> str:
    return (
        f"🧹 <b>ꜱᴛᴏʀᴀɢᴇ & ᴍᴇᴍᴏʀʏ ᴍᴀɴᴀɢᴇʀ ({action})</b>\n\n"
        f"🗑️ <b>ᴅɪsᴋ sᴘᴀᴄᴇ ғʀᴇᴇᴅ :</b> <code>{data.get('disk_freed_mb', 0.0)} ᴍʙ</code>\n"
        f"🧠 <b>ʀᴀᴍ ғʀᴇᴇᴅ :</b> <code>{data.get('ram_freed_mb', 0.0)} ᴍʙ</code>\n"
        f"💾 <b>ғʀᴇᴇ ᴅɪsᴋ sᴘᴀᴄᴇ :</b> <code>{data.get('free_disk_gb', 0.0)} ɢʙ / {data.get('total_disk_gb', 0.0)} ɢʙ</code>\n"
        f"📊 <b>ᴄᴜʀʀᴇɴᴛ ʀᴀᴍ ᴜsᴀɢᴇ :</b> <code>{data.get('ram_used_mb', 0.0)} ᴍʙ / {data.get('ram_total_mb', 0.0)} ᴍʙ</code>\n\n"
        f"⚡ <i>ᴀᴜᴛᴏ-ᴄʟᴇᴀɴ ɪs ʀᴜɴɴɪɴɢ 24x7 ɪɴ ʙᴀᴄᴋɢʀᴏᴜɴᴅ ᴛᴏ ᴋᴇᴇᴘ ᴋᴏʏᴇʙ ᴀʟɪᴠᴇ.</i>\n"
        f"👑 <b>ᴏᴡɴᴇʀ :</b> @{config.OWNER_USERNAME}"
    )


@app.on_message(
    filters.command(["clean", "cleancache", "freestorage", "freememory", "free"])
    & (filters.user(config.OWNER_ID) | SUDOERS)
)
async def clean_cmd(_, message: Message):
    m = await message.reply_text("🧹 <i>Cleaning temporary files, cache, and freeing memory...</i>")
    data = clean_storage_and_memory()
    text = format_clean_text(data, action="Cleaned")
    await m.edit_text(text, reply_markup=cleaner_keyboard(), parse_mode=ParseMode.HTML)


@app.on_callback_query(filters.regex("^clean_storage_action$"))
async def clean_action_cb(_, query: CallbackQuery):
    if query.from_user.id != config.OWNER_ID and query.from_user.id not in SUDOERS:
        return await query.answer("❌ Only Owner and Sudo users can use this button!", show_alert=True)
    await query.answer("🧹 Cleaning storage & memory...", show_alert=False)
    data = clean_storage_and_memory()
    text = format_clean_text(data, action="Cleaned Now")
    try:
        await query.edit_message_text(text, reply_markup=cleaner_keyboard(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await query.answer(f"✅ Cleaned! RAM: {data['ram_used_mb']}MB, Disk Free: {data['free_disk_gb']}GB", show_alert=True)


@app.on_callback_query(filters.regex("^clean_storage_deep$"))
async def clean_deep_cb(_, query: CallbackQuery):
    if query.from_user.id != config.OWNER_ID and query.from_user.id not in SUDOERS:
        return await query.answer("❌ Only Owner and Sudo users can use this button!", show_alert=True)
    await query.answer("🧹 Deep wiping cache & temp downloads...", show_alert=False)
    data = clean_storage_and_memory(deep=True)
    text = format_clean_text(data, action="Deep Cleaned")
    try:
        await query.edit_message_text(text, reply_markup=cleaner_keyboard(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await query.answer("✅ Deep cache & memory wipe complete!", show_alert=True)


@app.on_callback_query(filters.regex("^clean_storage_refresh$"))
async def clean_refresh_cb(_, query: CallbackQuery):
    if query.from_user.id != config.OWNER_ID and query.from_user.id not in SUDOERS:
        return await query.answer("❌ Only Owner and Sudo users can use this button!", show_alert=True)
    vm_used = psutil.virtual_memory().used if psutil else 0
    vm_total = psutil.virtual_memory().total if psutil else 0
    disk_free = psutil.disk_usage("/").free if psutil else 0
    disk_total = psutil.disk_usage("/").total if psutil else 0
    data = {
        "disk_freed_mb": 0.0,
        "ram_freed_mb": 0.0,
        "ram_used_mb": round(vm_used / (1024 * 1024), 2),
        "ram_total_mb": round(vm_total / (1024 * 1024), 2),
        "free_disk_gb": round(disk_free / (1024 ** 3), 2),
        "total_disk_gb": round(disk_total / (1024 ** 3), 2),
    }
    text = format_clean_text(data, action="Current Stats")
    try:
        await query.edit_message_text(text, reply_markup=cleaner_keyboard(), parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await query.answer("🔄 Stats updated!", show_alert=False)


__MODULE__ = "Cʟᴇᴀɴᴇʀ"
__HELP__ = """
## Sᴛᴏʀᴀɢᴇ & Mᴇᴍᴏʀʏ Cʟᴇᴀɴᴇʀ

Aᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴄʟᴇᴀɴs ᴛᴇᴍᴘᴏʀᴀʀʏ ᴄᴀᴄʜᴇ, ᴅᴏᴡɴʟᴏᴀᴅs, ᴀɴᴅ ғʀᴇᴇs ᴜᴘ RAM ᴇᴠᴇʀʏ 10 ᴍɪɴᴜᴛᴇs ғᴏʀ Kᴏʏᴇʙ 24x7 ᴜᴘᴛɪᴍᴇ.

### Cᴏᴍᴍᴀɴᴅs:
- `/clean` ᴏʀ `/cleancache`: Cʟᴇᴀɴ ᴀʟʟ ᴄᴀᴄʜᴇ, ᴛᴇᴍᴘ ᴅᴏᴡɴʟᴏᴀᴅs ᴀɴᴅ ғʀᴇᴇ RAM ᴡɪᴛʜ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ʙᴜᴛᴛᴏɴs.
- `/freestorage`: Fʀᴇᴇ ᴜᴘ ᴇxᴛʀᴀ sᴛᴏʀᴀɢᴇ ɪɴsᴛᴀɴᴛʟʏ.
"""
