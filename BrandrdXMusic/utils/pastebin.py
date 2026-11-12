import asyncio
import socket
import urllib.parse
import urllib.request


def _netcat(host, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(content.encode())
    s.shutdown(socket.SHUT_WR)
    while True:
        data = s.recv(4096).decode("utf-8").strip("\n\x00")
        if not data:
            break
        return data
    s.close()


def _sync_paste(content):
    url = "https://pastebin.com/api/api_post.php"
    data = urllib.parse.urlencode({
        "api_dev_key": "9Rfu50iV5l3EuRWATw7EDLuC37RED-C4",
        "api_paste_code": content,
        "api_option": "paste",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8")


async def HottyBin(content):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _sync_paste, content)
    except Exception:
        return "https://pastebin.com"
