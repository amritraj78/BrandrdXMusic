import re
from typing import Union

import aiohttp
from bs4 import BeautifulSoup
from py_yt import VideosSearch


class AppleAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/music.apple.com\/)(.*)$"
        self.base = "https://music.apple.com/in/playlist/"

    async def valid(self, link: str):
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def track(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False
                html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        search = None
        for tag in soup.find_all("meta"):
            if tag.get("property", None) == "og:title":
                search = tag.get("content", None)
        if search is None:
            return False
        results = VideosSearch(search, limit=1)
        res_data = (await results.next()).get("result") or []
        if not res_data:
            return False
        result = res_data[0]
        title = result.get("title", "Track")
        ytlink = result.get("link", "")
        vidid = result.get("id", "")
        duration_min = result.get("duration", "0:00")
        thumbs = result.get("thumbnails", [{}])
        thumbnail = thumbs[0].get("url", "").split("?")[0] if thumbs else ""
        track_details = {
            "title": title,
            "link": ytlink,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def playlist(self, url, playid: Union[bool, str] = None):
        if playid:
            url = self.base + url
        playlist_id = url.split("playlist/")[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False
                html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        applelinks = soup.find_all("meta", attrs={"property": "music:song"})
        results = []
        for item in applelinks:
            try:
                xx = (((item["content"]).split("album/")[1]).split("/")[0]).replace(
                    "-", " "
                )
            except:
                xx = ((item["content"]).split("album/")[1]).split("/")[0]
            results.append(xx)
        return results, playlist_id
