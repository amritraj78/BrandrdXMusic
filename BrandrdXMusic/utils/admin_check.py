from pyrogram.enums import ChatMembersFilter, ChatMemberStatus
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.formatters import alpha_to_int
from BrandrdXMusic.utils.database import get_authuser_names
from config import adminlist


async def get_chat_admins(chat_id: int, refresh: bool = False) -> list:
    """
    Returns the list of administrator user IDs for the given chat_id.
    Caches results in config.adminlist for instant response, but refreshes
    automatically if empty or requested. Handles OWNER and Pyrogram privileges safely.
    """
    if not refresh and chat_id in adminlist and adminlist[chat_id]:
        return adminlist[chat_id]

    admins = []
    try:
        async for user in app.get_chat_members(
            chat_id, filter=ChatMembersFilter.ADMINISTRATORS
        ):
            status = getattr(user, "status", None)
            if status == ChatMemberStatus.OWNER or (
                user.privileges and getattr(user.privileges, "can_manage_video_chats", False)
            ):
                if user.user:
                    admins.append(user.user.id)
    except Exception:
        pass

    try:
        authusers = await get_authuser_names(chat_id)
        if authusers:
            for user in authusers:
                user_id = await alpha_to_int(user)
                if user_id not in admins:
                    admins.append(user_id)
    except Exception:
        pass

    if admins:
        adminlist[chat_id] = admins
    return admins


async def is_admin(chat_id: int, user_id: int) -> bool:
    """
    Checks if a user is an administrator or sudo user in chat_id.
    """
    if user_id in SUDOERS:
        return True
    admins = await get_chat_admins(chat_id)
    return user_id in admins
