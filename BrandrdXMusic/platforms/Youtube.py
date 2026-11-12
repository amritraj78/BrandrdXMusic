import asyncio
import os
import re
from typing import Union
import aiohttp
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch
from BrandrdXMusic.logging import LOGGER

API_URL = os.environ.get("API_URL", "")
API_KEY = os.environ.get("API_KEY", os.environ.get("SAPI_KEY", ""))

DOWNLOAD_DIR = "downloads"


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # 1. Try external API if configured
    if API_URL:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/download",
                    params={"url": video_id, "type": "audio", "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(131072):
                                f.write(chunk)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
        except Exception as e:
            LOGGER(__name__).warning("External API download failed: %s", e)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    # 2. Try yt-dlp file download
    try:
        loop = asyncio.get_event_loop()
        def _ytdl_audio():
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb"],
                    }
                },
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
            for fname in os.listdir(DOWNLOAD_DIR):
                if fname.startswith(video_id):
                    p = os.path.join(DOWNLOAD_DIR, fname)
                    if os.path.getsize(p) > 0:
                        return p
            return None

        res = await loop.run_in_executor(None, _ytdl_audio)
        if res and os.path.exists(res) and os.path.getsize(res) > 0:
            return res
    except Exception as e:
        LOGGER(__name__).warning("yt-dlp file download failed: %s", e)

    # 3. Fallback to direct stream URL
    try:
        loop = asyncio.get_event_loop()
        def _extract_url():
            ydl_opts = {
                "format": "bestaudio/best",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb"],
                    }
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info.get("url")

        direct_url = await loop.run_in_executor(None, _extract_url)
        if direct_url:
            return direct_url
    except Exception as e:
        LOGGER(__name__).error("yt-dlp stream URL extraction failed: %s", e)

    return None


async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # 1. Try external API if configured
    if API_URL:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/download",
                    params={"url": video_id, "type": "video", "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as resp:
                    if resp.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(131072):
                                f.write(chunk)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
        except Exception as e:
            LOGGER(__name__).warning("External API video download failed: %s", e)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    # 2. Try yt-dlp video download
    try:
        loop = asyncio.get_event_loop()
        def _ytdl_video():
            ydl_opts = {
                "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb"],
                    }
                },
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path
            for fname in os.listdir(DOWNLOAD_DIR):
                if fname.startswith(video_id):
                    p = os.path.join(DOWNLOAD_DIR, fname)
                    if os.path.getsize(p) > 0:
                        return p
            return None

        res = await loop.run_in_executor(None, _ytdl_video)
        if res and os.path.exists(res) and os.path.getsize(res) > 0:
            return res
    except Exception as e:
        LOGGER(__name__).warning("yt-dlp video download failed: %s", e)

    # 3. Fallback: extract direct stream URL
    try:
        loop = asyncio.get_event_loop()
        def _extract_video_url():
            ydl_opts = {
                "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "mweb"],
                    }
                },
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info.get("url")

        direct_url = await loop.run_in_executor(None, _extract_video_url)
        if direct_url:
            return direct_url
    except Exception as e:
        LOGGER(__name__).error("yt-dlp video stream URL extraction failed: %s", e)

    return None



class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        ids = []
        try:
            from py_yt import Playlist
            plist = await Playlist.get(link)
            videos = plist.get("videos") or []
            for data in videos[:limit]:
                if data and data.get("id"):
                    ids.append(data.get("id"))
            if ids:
                return ids
        except Exception:
            pass

        try:
            loop = asyncio.get_event_loop()
            def _extract_playlist():
                ydl_opts = {
                    "extract_flat": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    entries = info.get("entries") or []
                    return [e["id"] for e in entries[:limit] if e and "id" in e]
            extracted = await loop.run_in_executor(None, _extract_playlist)
            if extracted:
                return extracted
        except Exception:
            pass
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False


YouTube = YouTubeAPI()
