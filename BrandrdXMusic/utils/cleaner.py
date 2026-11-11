import os
import gc
import shutil
import asyncio
import psutil
from BrandrdXMusic import LOGGER

FILE_EXTENSIONS = (
    ".mp3", ".mp4", ".m4a", ".webm", ".raw", ".wav",
    ".opus", ".ogg", ".aac", ".flac", ".jpg", ".jpeg", ".png"
)


def trim_memory():
    """Trigger Python garbage collection and release heap back to OS if possible."""
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass


def get_dir_size(path: str) -> int:
    total = 0
    if not os.path.exists(path):
        return 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def clean_storage_and_memory(deep: bool = True) -> dict:
    """
    Cleans temporary audio/video downloads, cache, and frees system RAM.
    """
    bytes_freed = 0
    mem_before = psutil.virtual_memory().used

    # 1. Clean downloads directory
    if os.path.exists("downloads"):
        for filename in os.listdir("downloads"):
            filepath = os.path.join("downloads", filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    bytes_freed += os.path.getsize(filepath)
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    bytes_freed += get_dir_size(filepath)
                    shutil.rmtree(filepath, ignore_errors=True)
            except Exception:
                pass

    # 2. Clean cache directory (preserve silence audio if needed)
    if os.path.exists("cache"):
        for filename in os.listdir("cache"):
            if filename in ("silence.wav", "silence.mp4"):
                continue
            filepath = os.path.join("cache", filename)
            try:
                if os.path.isfile(filepath) or os.path.islink(filepath):
                    bytes_freed += os.path.getsize(filepath)
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    bytes_freed += get_dir_size(filepath)
                    shutil.rmtree(filepath, ignore_errors=True)
            except Exception:
                pass

    # 3. Clean raw_files directory if exists
    if os.path.exists("raw_files"):
        for filename in os.listdir("raw_files"):
            filepath = os.path.join("raw_files", filename)
            try:
                bytes_freed += os.path.getsize(filepath)
                os.unlink(filepath)
            except Exception:
                pass

    # 4. Clean stray media files in root
    try:
        for file in os.listdir("."):
            if file.endswith(FILE_EXTENSIONS):
                filepath = os.path.join(".", file)
                try:
                    bytes_freed += os.path.getsize(filepath)
                    os.unlink(filepath)
                except Exception:
                    pass
    except Exception:
        pass

    # 5. Rotate/truncate log.txt if it exceeds 5MB
    if os.path.exists("log.txt"):
        try:
            if os.path.getsize("log.txt") > 5 * 1024 * 1024:
                with open("log.txt", "w") as f:
                    f.write("Log rotated to prevent disk exhaustion.\n")
        except Exception:
            pass

    # 6. Recreate required dirs
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

    # 7. Collect garbage & trim memory
    trim_memory()

    mem_after = psutil.virtual_memory().used
    ram_freed = max(0, mem_before - mem_after)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "disk_freed_mb": round(bytes_freed / (1024 * 1024), 2),
        "ram_freed_mb": round(ram_freed / (1024 * 1024), 2),
        "ram_used_mb": round(vm.used / (1024 * 1024), 2),
        "ram_total_mb": round(vm.total / (1024 * 1024), 2),
        "free_disk_gb": round(disk.free / (1024 ** 3), 2),
        "total_disk_gb": round(disk.total / (1024 ** 3), 2),
    }


async def auto_clean_worker():
    """
    Background worker that runs every 10 minutes to keep disk and memory free on Koyeb 24x7.
    """
    LOGGER("BrandrdXMusic.cleaner").info("Auto Memory & Storage cleaner started (interval: 10 mins).")
    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes
            res = clean_storage_and_memory()
            LOGGER("BrandrdXMusic.cleaner").info(
                f"Auto-Clean: Freed {res['disk_freed_mb']}MB disk, {res['ram_freed_mb']}MB RAM. "
                f"RAM in use: {res['ram_used_mb']}MB."
            )
        except asyncio.CancelledError:
            break
        except Exception as e:
            LOGGER("BrandrdXMusic.cleaner").warning(f"Auto-clean worker error: {e}")
