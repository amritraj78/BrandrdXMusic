from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, User

from BrandrdXMusic import app


async def extract_user(m: Message) -> User:
    if m.reply_to_message:
        return m.reply_to_message.from_user
    if len(m.command) < 2:
        return None
    try:
        user_input = m.command[1].strip()
        if m.entities and len(m.entities) > 1:
            for entity in m.entities[1:]:
                if entity.type == MessageEntityType.TEXT_MENTION and entity.user:
                    return entity.user
        if user_input.isdecimal() or (user_input.startswith("-") and user_input[1:].isdecimal()):
            user_input = int(user_input)
        return await app.get_users(user_input)
    except Exception:
        return None
