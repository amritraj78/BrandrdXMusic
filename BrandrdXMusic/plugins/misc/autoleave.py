import asyncio
from datetime import datetime, timedelta

from pyrogram.enums import ChatType

import config
from BrandrdXMusic import app, LOGGER
from BrandrdXMusic.core.call import Hotty, autoend
from BrandrdXMusic.utils.database import (
    get_client,
    is_active_chat,
    get_active_chats,
    group_assistant,
)


async def auto_leave():
    if config.AUTO_LEAVING_ASSISTANT:
        while not await asyncio.sleep(900):
            from BrandrdXMusic.core.userbot import assistants

            for num in assistants:
                client = await get_client(num)
                left = 0
                try:
                    async for i in client.get_dialogs():
                        if i.chat.type in [
                            ChatType.SUPERGROUP,
                            ChatType.GROUP,
                            ChatType.CHANNEL,
                        ]:
                            if (
                                i.chat.id != config.LOGGER_ID
                                and i.chat.id != -1001626004802
                                and i.chat.id != -1001876397776
                            ):
                                if left == 20:
                                    continue
                                if not await is_active_chat(i.chat.id):
                                    try:
                                        await client.leave_chat(i.chat.id)
                                        left += 1
                                    except:
                                        continue
                except:
                    pass


asyncio.create_task(auto_leave())


async def auto_end():
    """Monitors all active voice chats every 15s. If only assistant remains in VC,
    starts a 2-minute timer. If no human rejoins within 2 minutes, leaves VC
    to save server RAM and Koyeb bandwidth."""
    while not await asyncio.sleep(15):
        try:
            active_chats = await get_active_chats()
        except Exception:
            continue

        for chat_id in active_chats:
            try:
                if not await is_active_chat(chat_id):
                    autoend.pop(chat_id, None)
                    continue

                assistant = await group_assistant(Hotty, chat_id)
                try:
                    participants = await assistant.get_participants(chat_id)
                except Exception:
                    continue

                num_participants = len(participants) if participants else 0

                # If only the assistant (or nobody) is in voice chat
                if num_participants <= 1:
                    timer = autoend.get(chat_id)
                    if not timer:
                        # Start 2-minute auto-leave timer
                        autoend[chat_id] = datetime.now() + timedelta(minutes=2)
                        LOGGER("BrandrdXMusic.autoleave").info(
                            f"Empty VC detected in chat {chat_id} (only assistant). Auto-leave timer set for 2 minutes."
                        )
                    elif datetime.now() > timer:
                        # 2 minutes expired! Leave call to save server RAM and Koyeb bandwidth
                        autoend.pop(chat_id, None)
                        try:
                            await Hotty.stop_stream(chat_id)
                        except Exception:
                            pass
                        try:
                            await app.send_message(
                                chat_id,
                                "» ᴀssɪsᴛᴀɴᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ʟᴇғᴛ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ʙᴇᴄᴀᴜsᴇ ɴᴏ ᴏɴᴇ ᴡᴀs ʟɪsᴛᴇɴɪɴɢ (2 ᴍɪɴᴜᴛᴇs ɪɴᴀᴄᴛɪᴠɪᴛʏ) ᴛᴏ sᴀᴠᴇ sᴇʀᴠᴇʀ ʀᴀᴍ & ʙᴀɴᴅᴡɪᴅᴛʜ.",
                            )
                        except Exception:
                            pass
                        LOGGER("BrandrdXMusic.autoleave").info(
                            f"Auto-left VC for chat {chat_id} after 2 minutes of inactivity to save RAM & bandwidth."
                        )
                else:
                    # Humans are present in the VC! Cancel/clear any pending auto-leave timer
                    if chat_id in autoend:
                        autoend.pop(chat_id, None)
            except Exception:
                pass

        # Cleanup chats from autoend that are no longer active
        current_active = set(active_chats)
        for cid in list(autoend.keys()):
            if cid not in current_active:
                autoend.pop(cid, None)


asyncio.create_task(auto_end())

