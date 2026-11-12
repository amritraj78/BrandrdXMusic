import asyncio
from os import path
from yt_dlp import YoutubeDL
from BrandrdXMusic.utils.formatters import seconds_to_min


class SoundAPI:
    def __init__(self):
        self.opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "format": "best",
            "retries": 3,
            "nooverwrites": False,
            "continuedl": True,
        }

    async def valid(self, link: str):
        if "soundcloud" in link:
            return True
        else:
            return False

    async def download(self, url):
        loop = asyncio.get_event_loop()

        # 1. Try direct stream URL extraction (fastest: ~700ms, no disk download)
        def _extract_stream():
            stream_opts = {
                "format": "bestaudio/best",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }
            with YoutubeDL(stream_opts) as ydl:
                return ydl.extract_info(url, download=False)

        try:
            info = await loop.run_in_executor(None, _extract_stream)
            if info:
                stream_url = info.get("url")
                if stream_url and stream_url.startswith("http"):
                    duration_sec = int(info.get("duration") or 0)
                    duration_min = seconds_to_min(duration_sec)
                    track_details = {
                        "title": info.get("title", "SoundCloud Track"),
                        "duration_sec": duration_sec,
                        "duration_min": duration_min,
                        "uploader": info.get("uploader", "SoundCloud"),
                        "filepath": stream_url,
                    }
                    return track_details, stream_url
        except Exception:
            pass

        # 2. Fallback: Download file to disk
        def _download_file():
            d = YoutubeDL(self.opts)
            return d.extract_info(url)

        try:
            info = await loop.run_in_executor(None, _download_file)
            if not info:
                return False
        except:
            return False
        xyz = path.join("downloads", f"{info['id']}.{info['ext']}")
        duration_sec = int(info.get("duration") or 0)
        duration_min = seconds_to_min(duration_sec)
        track_details = {
            "title": info["title"],
            "duration_sec": duration_sec,
            "duration_min": duration_min,
            "uploader": info["uploader"],
            "filepath": xyz,
        }
        return track_details, xyz

