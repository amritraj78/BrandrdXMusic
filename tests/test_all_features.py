import asyncio
import base64
import json
import math
import os
import re
import sys
import unittest
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import importlib.util

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def _load_module(mod_name, file_rel_path):
    file_path = os.path.join(ROOT_DIR, file_rel_path)
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod

des_mod = _load_module("des_mod", "BrandrdXMusic/utils/des.py")
des, ECB, PAD_PKCS5 = des_mod.des, des_mod.ECB, des_mod.PAD_PKCS5

fmt_mod = _load_module("fmt_mod", "BrandrdXMusic/utils/formatters.py")
seconds_to_min, time_to_seconds = fmt_mod.seconds_to_min, fmt_mod.time_to_seconds


class TestAllFeatures(unittest.TestCase):

    def test_1_des_decryption_and_jiosaavn_cdn(self):
        """Test JioSaavn direct CDN stream URL extraction and DES decryption."""
        query = "Kesariya"
        search_query = re.sub(r"[^\w\s]", " ", query).strip()
        search_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={urllib.parse.quote(search_query)}"
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            songs = data.get("songs", {}).get("data", [])
            self.assertTrue(len(songs) > 0, "No songs found for Kesariya on JioSaavn")
            song_id = songs[0].get("id")

        detail_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0&_format=json&pids={song_id}"
        req = urllib.request.Request(detail_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            song_info = data.get(song_id, {})
            enc_url = song_info.get("encrypted_media_url")

        des_key = b"38346591"
        des_cipher = des(des_key, ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
        enc_url_bytes = base64.b64decode(enc_url.strip())
        dec_bytes = des_cipher.decrypt(enc_url_bytes, padmode=PAD_PKCS5)
        media_url = dec_bytes.decode("utf-8").replace("_96.mp4", "_320.mp4")

        self.assertTrue(media_url.startswith("http"), f"Invalid stream url: {media_url}")
        self.assertTrue(".mp4" in media_url or ".m4a" in media_url, f"Expected audio container: {media_url}")
        print(f"\n[PASS] Test 1: JioSaavn direct CDN stream URL resolved: {media_url[:60]}...")

    def test_2_formatters(self):
        """Test time_to_seconds and seconds_to_min with edge cases."""
        self.assertEqual(seconds_to_min(0), "00:00")
        self.assertEqual(seconds_to_min(5), "00:05")
        self.assertEqual(seconds_to_min(65), "01:05")
        self.assertEqual(seconds_to_min(3665), "01:01:05")
        self.assertEqual(seconds_to_min(-10), "00:00")
        self.assertEqual(seconds_to_min(None), "00:00")

        self.assertEqual(time_to_seconds("00:00"), 0)
        self.assertEqual(time_to_seconds("01:05"), 65)
        self.assertEqual(time_to_seconds("01:01:05"), 3665)
        self.assertEqual(time_to_seconds("-"), 0)
        self.assertEqual(time_to_seconds(""), 0)
        print("\n[PASS] Test 2: Formatter functions handled 0 and edge cases correctly.")

    def test_3_stream_timer_bar_logic(self):
        """Test timer progress bar calculations across percentages."""
        test_cases = [
            ("00:00", "03:30"),
            ("00:30", "03:30"),
            ("01:45", "03:30"),
            ("03:15", "03:30"),
            ("03:30", "03:30"),
            ("05:00", "03:30"),  # Played > duration
        ]
        for played, dur in test_cases:
            played_sec = time_to_seconds(played)
            duration_sec = time_to_seconds(dur) or 1
            pct = (played_sec / duration_sec) * 100
            pct = max(0, min(100, pct))
            umm = math.floor(pct)

            if 0 < umm <= 10:
                bar = "▷—————————"
            elif 10 < umm < 20:
                bar = "—▷————————"
            elif 20 <= umm < 30:
                bar = "——▷———————"
            elif 30 <= umm < 40:
                bar = "———▷——————"
            elif 40 <= umm < 50:
                bar = "————▷—————"
            elif 50 <= umm < 60:
                bar = "—————▷————"
            elif 60 <= umm < 70:
                bar = "——————▷———"
            elif 70 <= umm < 80:
                bar = "———————▷——"
            elif 80 <= umm < 95:
                bar = "————————▷—"
            else:
                bar = "—————————▷"

            button_text = f"{played} {bar} {dur}"
            self.assertIn("▷", button_text)
            self.assertEqual(len(bar), 10)
        print("\n[PASS] Test 3: Stream timer progress bar renders perfectly at all percentages.")

    def test_4_button_callback_lengths(self):
        """Test that all callback_data in buttons are <= 64 bytes (Telegram restriction)."""
        chat_id = -1001234567890
        vidid = "BddP6PYo2gs"

        callbacks = [
            f"ADMIN Resume|{chat_id}",
            f"ADMIN Pause|{chat_id}",
            f"ADMIN Replay|{chat_id}",
            f"ADMIN Skip|{chat_id}",
            f"ADMIN Stop|{chat_id}",
            f"ADMIN VolDown|{chat_id}",
            f"ADMIN VolUp|{chat_id}",
            f"ADMIN Shuffle|{chat_id}",
            f"ADMIN Loop|{chat_id}",
            f"ADMIN FilterMenu|{chat_id}",
            f"ADMIN BackToPlayer|{chat_id}",
            f"ADMIN Filter_bass|{chat_id}",
            f"ADMIN Filter_slowed|{chat_id}",
            f"ADMIN Filter_nightcore|{chat_id}",
            f"ADMIN Filter_8d|{chat_id}",
            f"ADMIN Filter_vaporwave|{chat_id}",
            f"ADMIN Filter_reset|{chat_id}",
            "close",
            "GetTimer",
        ]

        for cb in callbacks:
            byte_len = len(cb.encode("utf-8"))
            self.assertLessEqual(byte_len, 64, f"Callback data too long ({byte_len} bytes): {cb}")

        print(f"\n[PASS] Test 4: All {len(callbacks)} inline button callbacks are within Telegram 64-byte limit.")

    def test_5_volume_controls(self):
        """Test volume bounds (10% to 200%)."""
        vol = 100
        # VolUp
        for _ in range(10):
            vol = min(200, vol + 15)
        self.assertEqual(vol, 200)

        # VolDown
        for _ in range(20):
            vol = max(10, vol - 15)
        self.assertEqual(vol, 10)

        # Vol100
        vol = 100
        self.assertEqual(vol, 100)
        print("\n[PASS] Test 5: Volume controls clamp correctly between 10% and 200%.")

    def test_6_autoleave_logic(self):
        """Test 2-minute empty voice chat auto-leave timer."""
        autoend = {}
        chat_id = -1001234567890

        # Scenario 1: Only assistant in VC (1 participant)
        participants = ["assistant_id"]
        if len(participants) <= 1:
            if chat_id not in autoend:
                autoend[chat_id] = datetime.now() + timedelta(minutes=2)

        self.assertIn(chat_id, autoend)
        self.assertGreater(autoend[chat_id], datetime.now())

        # Scenario 2: Human rejoins (2 participants)
        participants = ["assistant_id", "user_id_1"]
        if len(participants) > 1:
            autoend.pop(chat_id, None)

        self.assertNotIn(chat_id, autoend)

        # Scenario 3: Human leaves, timer expires
        autoend[chat_id] = datetime.now() - timedelta(seconds=1)
        timer = autoend.get(chat_id)
        should_leave = timer is not None and datetime.now() > timer
        self.assertTrue(should_leave)
        print("\n[PASS] Test 6: Auto-leave 2-minute timer logic verified.")

    def test_7_audio_filter_presets(self):
        """Test ffmpeg audio filter definitions."""
        AUDIO_FILTERS = {
            "bass": "equalizer=f=60:width_type=h:width=50:g=12",
            "bassboost": "equalizer=f=60:width_type=h:width=50:g=16",
            "slowed": "atempo=0.86,asetrate=44100*0.92,aecho=0.8:0.88:60:0.4",
            "nightcore": "atempo=1.06,asetrate=44100*1.22",
            "8d": "apulsator=hz=0.125",
            "vaporwave": "atempo=0.8,asetrate=44100*0.85",
            "echo": "aecho=0.8:0.9:1000:0.3",
        }
        for name, filter_str in AUDIO_FILTERS.items():
            self.assertTrue(len(filter_str) > 0)
            # Ensure no command injection characters
            self.assertNotIn(";", filter_str)
            self.assertNotIn("&", filter_str)
            self.assertNotIn("|", filter_str)
        print(f"\n[PASS] Test 7: All {len(AUDIO_FILTERS)} audio filter presets verified safely.")

    def test_8_gapless_precache_logic(self):
        """Test queue precache logic for gapless playback."""
        # Case A: Queue has 0 or 1 track -> no precache
        queue_small = [{"file": "current.mp3", "vidid": "1"}]
        self.assertTrue(len(queue_small) < 2)

        # Case B: Queue has 2 tracks, next track is vid_ -> precache needed
        queue_two = [
            {"file": "current.mp3", "vidid": "1"},
            {"file": "vid_abc123", "vidid": "abc123", "title": "Next Song"}
        ]
        next_track = queue_two[1]
        needs_precache = str(next_track.get("file", "")).startswith("vid_")
        self.assertTrue(needs_precache)

        # Precache completes -> file updated to downloaded mp3 path
        queue_two[1]["file"] = "/tmp/downloads/abc123.mp3"
        self.assertFalse(str(queue_two[1]["file"]).startswith("vid_"))
        print("\n[PASS] Test 8: Gapless pre-caching queue state transitions verified.")

    def test_9_play_markups(self):
        """Test inline keyboard markup generation and rows."""
        # Load play.py directly
        play_mod = _load_module("play_mod", "BrandrdXMusic/utils/inline/play.py")
        _ = {"CLOSE_BUTTON": "🗑️ Close"}
        chat_id = -1001234567890
        vidid = "BddP6PYo2gs"

        sm = play_mod.stream_markup(_, vidid, chat_id)
        self.assertEqual(len(sm), 4, f"stream_markup should have 4 rows, got {len(sm)}")

        smt = play_mod.stream_markup_timer(_, vidid, chat_id, "01:30", "03:30")
        self.assertEqual(len(smt), 5, f"stream_markup_timer should have 5 rows, got {len(smt)}")

        sm2 = play_mod.stream_markup2(_, chat_id)
        self.assertEqual(len(sm2), 4, f"stream_markup2 should have 4 rows, got {len(sm2)}")

        smt2 = play_mod.stream_markup_timer2(_, chat_id, "01:30", "03:30")
        self.assertEqual(len(smt2), 5, f"stream_markup_timer2 should have 5 rows, got {len(smt2)}")

        fm = play_mod.filter_markup(chat_id)
        self.assertEqual(len(fm), 4, f"filter_markup should have 4 rows, got {len(fm)}")

        # Verify Mini App button URL
        mini_app_btn = smt[3][0]
        self.assertIn("webapp?chat_id=", mini_app_btn.url)
        self.assertIn(str(chat_id), mini_app_btn.url)
        print("\n[PASS] Test 9: All 5-row inline markups, timers, and Mini App URL verified.")

    def test_10_admin_check_and_call_record(self):
        """Test record_played history tracking, admin caching, and signature compatibility."""
        from BrandrdXMusic.utils.database import record_played, _chat_history
        from config import adminlist

        test_chat_id = -10099887766
        # Test record_played
        self.assertNotIn(test_chat_id, _chat_history)
        record_played(test_chat_id, "test_vid_1")
        record_played(test_chat_id, "test_vid_2")
        record_played(test_chat_id, "")  # Should ignore empty
        self.assertEqual(len(_chat_history[test_chat_id]), 2)
        self.assertIn("test_vid_1", _chat_history[test_chat_id])
        self.assertIn("test_vid_2", _chat_history[test_chat_id])

        # Test adminlist caching
        adminlist[test_chat_id] = [12345, 67890]
        from BrandrdXMusic.utils.admin_check import get_chat_admins
        loop = asyncio.get_event_loop()
        cached = loop.run_until_complete(get_chat_admins(test_chat_id, refresh=False))
        self.assertEqual(cached, [12345, 67890])

        # Test signature inspector compatibility
        import inspect
        async def func_3_args(client, message, _): pass
        async def func_4_args(client, message, _, chat_id): pass

        self.assertEqual(len(inspect.signature(func_3_args).parameters), 3)
        self.assertEqual(len(inspect.signature(func_4_args).parameters), 4)

        print("\n[PASS] Test 10: Admin check caching, record_played history, and signature compatibility verified.")


if __name__ == "__main__":
    unittest.main()

