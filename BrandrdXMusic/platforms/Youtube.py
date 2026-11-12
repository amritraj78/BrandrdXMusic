import asyncio
import base64
import json
import os
import re
import urllib.parse
import urllib.request
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

COMMON_YTDL_OPTS = {
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

COOKIE_PATH = "cookies.txt"
if os.path.exists(COOKIE_PATH):
    COMMON_YTDL_OPTS["cookiefile"] = COOKIE_PATH


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


def extract_video_id(link: str) -> str:
    if not link:
        return ""
    link = str(link).strip()
    if len(link) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", link):
        return link
    patterns = [
        r"(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|live\/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        m = re.search(pattern, link)
        if m:
            return m.group(1)
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    if "youtu.be/" in link:
        return link.split("youtu.be/")[-1].split("?")[0]
    return link


def get_yt_title_oembed(vid: str) -> str:
    if not vid:
        return ""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title", "")
    except Exception:
        return ""


def download_from_saavn_sync(query: str, file_path: str) -> bool:
    try:
        from pyDes import des, ECB, PAD_PKCS5
    except ImportError:
        return False
    try:
        search_query = re.sub(r"[^\w\s]", " ", query).strip()
        search_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={urllib.parse.quote(search_query)}"
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            songs = data.get("songs", {}).get("data", [])
            if not songs:
                return False
            song_id = songs[0].get("id")

        detail_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0&_format=json&pids={song_id}"
        req = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            song_info = data.get(song_id, {})
            enc_url = song_info.get("encrypted_media_url")
            if not enc_url:
                vlink = song_info.get("vlink")
                if vlink:
                    urllib.request.urlretrieve(vlink, file_path)
                    return os.path.exists(file_path) and os.path.getsize(file_path) > 0
                return False

        des_key = b"38346591"
        des_cipher = des(des_key, ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
        enc_url_bytes = base64.b64decode(enc_url.strip())
        dec_bytes = des_cipher.decrypt(enc_url_bytes, padmode=PAD_PKCS5)
        media_url = dec_bytes.decode("utf-8").replace("_96.mp4", "_320.mp4")

        req = urllib.request.Request(media_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as stream_resp:
            with open(file_path, "wb") as f:
                f.write(stream_resp.read())
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
    except Exception as e:
        LOGGER(__name__).warning("JioSaavn fallback failed: %s", e)
        return False


async def download_song(link: str, title: str = None) -> str:
    raw_id = extract_video_id(link)
    video_id = re.sub(r"[^a-zA-Z0-9_-]", "", raw_id) if raw_id else ""
    if not video_id or len(video_id) < 3:
        video_id = "song_" + str(abs(hash(link)))[:8]

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

    yt_target = f"https://www.youtube.com/watch?v={video_id}" if len(video_id) == 11 else link

    # 2. Try yt-dlp YouTube download
    try:
        loop = asyncio.get_event_loop()
        def _ytdl_audio():
            ydl_opts = dict(COMMON_YTDL_OPTS)
            ydl_opts.update({
                "format": "bestaudio/best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            })
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([yt_target])
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
        LOGGER(__name__).warning("yt-dlp YouTube download failed: %s", e)

    # 3. Fallback: SoundCloud Search & Download
    search_term = title or ""
    if not search_term or search_term == "Unknown Track":
        oembed_ttl = get_yt_title_oembed(video_id)
        search_term = oembed_ttl if oembed_ttl else video_id
    if search_term and search_term != "Unknown Track":
        try:
            loop = asyncio.get_event_loop()
            def _sc_audio():
                sc_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                    "prefer_ffmpeg": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
                with yt_dlp.YoutubeDL(sc_opts) as ydl:
                    ydl.download([f"scsearch1:{search_term}"])
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return file_path
                for fname in os.listdir(DOWNLOAD_DIR):
                    if fname.startswith(video_id):
                        p = os.path.join(DOWNLOAD_DIR, fname)
                        if os.path.getsize(p) > 0:
                            return p
                return None

            sc_res = await loop.run_in_executor(None, _sc_audio)
            if sc_res and os.path.exists(sc_res) and os.path.getsize(sc_res) > 0:
                LOGGER(__name__).info("SoundCloud download succeeded for: %s", search_term)
                return sc_res
        except Exception as e:
            LOGGER(__name__).warning("SoundCloud fallback download failed: %s", e)

    # 4. Fallback: JioSaavn Direct Download
    if search_term and search_term != "Unknown Track":
        try:
            loop = asyncio.get_event_loop()
            saavn_ok = await loop.run_in_executor(None, download_from_saavn_sync, search_term, file_path)
            if saavn_ok and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                LOGGER(__name__).info("JioSaavn download succeeded for: %s", search_term)
                return file_path
        except Exception as e:
            LOGGER(__name__).warning("JioSaavn fallback failed: %s", e)

    # 5. Fallback: Direct SoundCloud stream URL
    if search_term and search_term != "Unknown Track":
        try:
            loop = asyncio.get_event_loop()
            def _sc_url():
                sc_opts = {
                    "format": "bestaudio/best",
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "quiet": True,
                    "no_warnings": True,
                }
                with yt_dlp.YoutubeDL(sc_opts) as ydl:
                    info = ydl.extract_info(f"scsearch1:{search_term}", download=False)
                    if info and info.get("entries"):
                        return info["entries"][0].get("url")
                return None

            direct_sc_url = await loop.run_in_executor(None, _sc_url)
            if direct_sc_url:
                LOGGER(__name__).info("SoundCloud stream URL extracted for: %s", search_term)
                return direct_sc_url
        except Exception as e:
            LOGGER(__name__).warning("SoundCloud stream URL extraction failed: %s", e)

    # 6. Fallback: Direct YouTube stream URL
    try:
        loop = asyncio.get_event_loop()
        def _extract_url():
            ydl_opts = dict(COMMON_YTDL_OPTS)
            ydl_opts["format"] = "bestaudio/best"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_target, download=False)
                return info.get("url")

        direct_url = await loop.run_in_executor(None, _extract_url)
        if direct_url:
            return direct_url
    except Exception as e:
        LOGGER(__name__).error("yt-dlp stream URL extraction failed: %s", e)

    return None


async def download_video(link: str, title: str = None) -> str:
    raw_id = extract_video_id(link)
    video_id = re.sub(r"[^a-zA-Z0-9_-]", "", raw_id) if raw_id else ""
    if not video_id or len(video_id) < 3:
        video_id = "video_" + str(abs(hash(link)))[:8]

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

    yt_target = f"https://www.youtube.com/watch?v={video_id}" if len(video_id) == 11 else link

    # 2. Try yt-dlp video download
    try:
        loop = asyncio.get_event_loop()
        def _ytdl_video():
            ydl_opts = dict(COMMON_YTDL_OPTS)
            ydl_opts.update({
                "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegVideoConvertor",
                        "preferedformat": "mp4",
                    }
                ],
            })
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([yt_target])
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
            ydl_opts = dict(COMMON_YTDL_OPTS)
            ydl_opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(yt_target, download=False)
                return info.get("url")

        direct_url = await loop.run_in_executor(None, _extract_video_url)
        if direct_url:
            return direct_url
    except Exception as e:
        LOGGER(__name__).error("yt-dlp video stream URL extraction failed: %s", e)

    # 4. Fallback: Download audio so playback never fails
    search_term = title or ""
    if not search_term or search_term == "Unknown Track":
        oembed_ttl = get_yt_title_oembed(video_id)
        search_term = oembed_ttl if oembed_ttl else video_id
    LOGGER(__name__).info("Video download failed, attempting audio fallback for: %s", search_term)
    try:
        audio_file = await download_song(link, title=search_term)
        if audio_file and os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            LOGGER(__name__).info("Audio fallback succeeded for video request: %s", audio_file)
            return audio_file
    except Exception as e:
        LOGGER(__name__).warning("Audio fallback in download_video failed: %s", e)

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

        # 1. Try VideosSearch
        try:
            results = VideosSearch(link, limit=1)
            res = (await results.next()).get("result")
            if res and len(res) > 0:
                result = res[0]
                title = result.get("title", "Unknown Track")
                duration_min = result.get("duration", "0:00")
                thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
                vidid = result.get("id") or extract_video_id(link)
                duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
                return title, duration_min, duration_sec, thumbnail, vidid
        except Exception as e:
            LOGGER(__name__).warning("VideosSearch failed in details: %s", e)

        # 2. Fallback to yt-dlp flat extract
        try:
            loop = asyncio.get_event_loop()
            def _extract_details():
                opts = dict(COMMON_YTDL_OPTS)
                opts["extract_flat"] = True
                with yt_dlp.YoutubeDL(opts) as ydl:
                    target = link if (link.startswith("http://") or link.startswith("https://")) else f"ytsearch1:{link}"
                    info = ydl.extract_info(target, download=False)
                    if info and info.get("entries"):
                        info = info["entries"][0]
                    if info:
                        vid = info.get("id") or extract_video_id(link)
                        ttl = info.get("title") or "Unknown Track"
                        dur = int(info.get("duration") or 0)
                        d_min = f"{dur // 60}:{dur % 60:02d}"
                        thumb = info.get("thumbnail") or f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                        return ttl, d_min, dur, thumb, vid
                    return None

            ytdl_res = await loop.run_in_executor(None, _extract_details)
            if ytdl_res:
                return ytdl_res
        except Exception as e:
            LOGGER(__name__).warning("yt-dlp fallback failed in details: %s", e)

        # 3. Final default fallback with oembed
        vid = extract_video_id(link) or "unknown"
        oembed_ttl = get_yt_title_oembed(vid)
        ttl = oembed_ttl if oembed_ttl else "Unknown Track"
        return ttl, "0:00", 0, f"https://img.youtube.com/vi/{vid}/hqdefault.jpg", vid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        t, _, _, _, _ = await self.details(link, videoid)
        return t

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        _, d, _, _, _ = await self.details(link, videoid)
        return d

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        _, _, _, thumb, _ = await self.details(link, videoid)
        return thumb

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
                opts = dict(COMMON_YTDL_OPTS)
                opts["extract_flat"] = True
                with yt_dlp.YoutubeDL(opts) as ydl:
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

        # 1. Try VideosSearch
        try:
            results = VideosSearch(link, limit=1)
            res = (await results.next()).get("result")
            if res and len(res) > 0:
                result = res[0]
                title = result.get("title", "Unknown Track")
                duration_min = result.get("duration", "0:00")
                vidid = result.get("id") or extract_video_id(link)
                yturl = result.get("link") or f"https://www.youtube.com/watch?v={vidid}"
                thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
                track_details = {
                    "title": title,
                    "link": yturl,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }
                return track_details, vidid
        except Exception as e:
            LOGGER(__name__).warning("VideosSearch failed in track: %s", e)

        # 2. Fallback to yt-dlp search
        try:
            loop = asyncio.get_event_loop()
            def _search_track():
                opts = dict(COMMON_YTDL_OPTS)
                opts["extract_flat"] = True
                with yt_dlp.YoutubeDL(opts) as ydl:
                    target = link if (link.startswith("http://") or link.startswith("https://")) else f"ytsearch1:{link}"
                    info = ydl.extract_info(target, download=False)
                    if info and info.get("entries"):
                        info = info["entries"][0]
                    if info:
                        vid = info.get("id") or extract_video_id(link)
                        ttl = info.get("title") or "Unknown Track"
                        dur = int(info.get("duration") or 0)
                        d_min = f"{dur // 60}:{dur % 60:02d}"
                        thumb = info.get("thumbnail") or f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                        return {
                            "title": ttl,
                            "link": f"https://www.youtube.com/watch?v={vid}",
                            "vidid": vid,
                            "duration_min": d_min,
                            "thumb": thumb,
                        }, vid
                    return None, None

            td, vid = await loop.run_in_executor(None, _search_track)
            if td and vid:
                return td, vid
        except Exception as e:
            LOGGER(__name__).warning("yt-dlp fallback failed in track: %s", e)

        # 3. Final fallback with oembed
        vid = extract_video_id(link) or "unknown"
        oembed_ttl = get_yt_title_oembed(vid)
        ttl = oembed_ttl if oembed_ttl else "Unknown Track"
        return {
            "title": ttl,
            "link": f"https://www.youtube.com/watch?v={vid}",
            "vidid": vid,
            "duration_min": "0:00",
            "thumb": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
        }, vid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]

        loop = asyncio.get_event_loop()
        def _extract_formats():
            opts = dict(COMMON_YTDL_OPTS)
            formats_available = []
            with yt_dlp.YoutubeDL(opts) as ydl:
                r = ydl.extract_info(link, download=False)
                for fmt in r.get("formats", []):
                    try:
                        if "dash" not in str(fmt.get("format", "")).lower():
                            sz = fmt.get("filesize") or fmt.get("filesize_approx")
                            formats_available.append(
                                {
                                    "format": fmt.get("format", ""),
                                    "filesize": sz if sz else 5000000,
                                    "format_id": fmt.get("format_id", "best"),
                                    "ext": fmt.get("ext", "mp4"),
                                    "format_note": fmt.get("format_note", "Standard"),
                                    "yturl": link,
                                }
                            )
                    except Exception:
                        continue
            return formats_available

        try:
            formats_available = await loop.run_in_executor(None, _extract_formats)
            if formats_available:
                return formats_available, link
        except Exception as e:
            LOGGER(__name__).error("formats extraction failed: %s", e)

        # Fallback formats for format selector
        vid = extract_video_id(link)
        yt_url = f"https://www.youtube.com/watch?v={vid}" if vid else link
        fallback_formats = [
            {
                "format": "audio only (mp3)",
                "filesize": 4000000,
                "format_id": "bestaudio",
                "ext": "mp3",
                "format_note": "High Quality",
                "yturl": yt_url,
            },
            {
                "format": "136 - 1280x720 (720p)",
                "filesize": 15000000,
                "format_id": "136",
                "ext": "mp4",
                "format_note": "720p",
                "yturl": yt_url,
            },
            {
                "format": "134 - 640x360 (360p)",
                "filesize": 8000000,
                "format_id": "134",
                "ext": "mp4",
                "format_note": "360p",
                "yturl": yt_url,
            },
        ]
        return fallback_formats, yt_url

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            a = VideosSearch(link, limit=10)
            res = (await a.next()).get("result") or []
            if len(res) > query_type:
                result = res[query_type]
                title = result.get("title", "Unknown Track")
                duration_min = result.get("duration", "0:00")
                vidid = result.get("id") or extract_video_id(link)
                thumbnail = result.get("thumbnails", [{}])[0].get("url", "").split("?")[0]
                return title, duration_min, thumbnail, vidid
        except Exception as e:
            LOGGER(__name__).warning("slider error: %s", e)

        # Fallback to single details
        title, duration_min, _, thumbnail, vidid = await self.details(link)
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic=None,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            vid = link
            link = self.base + link
        else:
            vid = extract_video_id(link)

        if not title:
            try:
                title, _, _, _, _ = await self.details(link)
            except Exception:
                title = vid

        try:
            if video:
                downloaded_file = await download_video(link, title=title)
            else:
                downloaded_file = await download_song(link, title=title)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception as e:
            LOGGER(__name__).error("YouTube.download error: %s", e)
            return None, False


YouTube = YouTubeAPI()
