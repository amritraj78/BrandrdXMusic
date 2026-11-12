import os

from config import autoclean


async def auto_clean(popped):
    try:
        rem = popped.get("file")
        if not rem:
            return
        if rem in autoclean:
            autoclean.remove(rem)
        count = autoclean.count(rem)
        if count == 0:
            if (
                "vid_" not in rem
                and "live_" not in rem
                and "index_" not in rem
                and not str(rem).startswith("http")
            ):
                try:
                    if os.path.exists(rem):
                        os.remove(rem)
                except Exception:
                    pass
    except Exception:
        pass
