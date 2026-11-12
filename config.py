import os
import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# Get this value from my.telegram.org/apps
API_ID = int(getenv("API_ID", 0)) if getenv("API_ID") else None
API_HASH = getenv("API_HASH", None)

# Get your token from @BotFather on Telegram.
BOT_TOKEN = getenv("BOT_TOKEN", None)

# Get your mongo url from cloud.mongodb.com
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 900))

# Chat id of a group for logging bot's activities
LOGGER_ID = int(getenv("LOGGER_ID", "-1004478038866")) if getenv("LOGGER_ID") else -1004478038866

# Owner Information
OWNER_ID = int(getenv("OWNER_ID", "7576534973"))
OWNER_USERNAME = getenv("OWNER_USERNAME", "ex_amrit")

# Group and Channel Links & IDs
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/privatethink")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/amrit_feel")
SUPPORT_CHAT_ID = int(getenv("SUPPORT_CHAT_ID", "-1004478038866"))

# Owner Socials
OWNER_INSTAGRAM = getenv("OWNER_INSTAGRAM", "https://instagram.com/ex_amrit")
OWNER_SNAPCHAT = getenv("OWNER_SNAPCHAT", "https://snapchat.com/add/ex_amrit")

# Koyeb Web Server Port (Free tier web service listening port)
PORT = int(getenv("PORT", 8000))
WEB_APP_URL = getenv("WEB_APP_URL", "https://brandrd-music-animeworlds-b77dd182.apps.mistral.run")

# Heroku deployment variables (optional)
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv("UPSTREAM_REPO", None)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", None)

# Assistant auto leave chats
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", False))

# Spotify credentials
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "bcfe26b0ebc3428882a0b5fb3e872473")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "907c6a054c214005aeae1fd752273cc4")

# Limits
SERVER_PLAYLIST_LIMIT = int(getenv("SERVER_PLAYLIST_LIMIT", "50"))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "25"))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "180"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "2000"))

# Telegram audio and video file size limit (in bytes)
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 104857600))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 1073741824))

# Assistant string sessions
STRING1 = getenv("STRING_SESSION",  None)
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

START_IMG_URL = getenv("START_IMG_URL", "https://imgdb.io/i/O3m-KbU.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://imgdb.io/i/2hO70lw.jpg")
PLAYLIST_IMG_URL = "https://imgdb.io/i/46apElg.jpg"
STATS_IMG_URL = "https://imgdb.io/i/XArO4l8.jpg"
TELEGRAM_AUDIO_URL = "https://imgdb.io/i/X-6L38g.jpg"
TELEGRAM_VIDEO_URL = "https://imgdb.io/i/qi_QJx0.jpg"
STREAM_IMG_URL = "https://imgdb.io/i/jgqv2mQ.jpg"
SOUNCLOUD_IMG_URL = "https://imgdb.io/i/jjJShXQ.jpg"
YOUTUBE_IMG_URL = "https://imgdb.io/i/HTo_3F0.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://imgdb.io/i/UX0rVaE.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://imgdb.io/i/O3m-KbU.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://imgdb.io/i/2hO70lw.jpg"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

if SUPPORT_CHANNEL:
    if not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHANNEL url is wrong. Please ensure that it starts with https://"
        )

if SUPPORT_CHAT:
    if not re.match(r"(?:http|https)://", SUPPORT_CHAT):
        raise SystemExit(
            "[ERROR] - Your SUPPORT_CHAT url is wrong. Please ensure that it starts with https://"
        )
