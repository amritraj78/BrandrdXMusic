<div align="center">

# 🎧 BrandrdXMusic

### ✨ High-Quality Telegram Voice Chat Music Bot
**Optimized for 24×7 Koyeb Free Tier Hosting with Auto Storage & RAM Cleaner**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](LICENSE)

[**OWNER**](https://t.me/ex_amrit) · [**SUPPORT GROUP**](https://t.me/amrit_feel) · [**UPDATES CHANNEL**](https://t.me/privatethink)

---

</div>

## 🌟 Key Features

- 🎵 **Crystal Clear Streaming**: High quality audio & video voice chat streaming via PyTgCalls.
- ⚡ **24×7 Koyeb Free Tier Compatible**: Built-in HTTP health check server on `$PORT` to keep the bot alive lifetime without sleeping or failing health checks.
- 🧹 **Automatic Storage & Memory Cleaner**:
  - Background daemon runs every 10 minutes to delete old downloaded tracks, temp video/audio cache, and free system RAM via `gc.collect()` and `malloc_trim`.
  - Manual interactive Owner command `/clean` with buttons to free cache & RAM on demand!
- 🎛️ **Full Playback Controls**: `/play`, `/vplay`, `/pause`, `/resume`, `/skip`, `/stop`, `/loop`, `/speed`, `/queue`.
- 👥 **Multi-Assistant Support**: Connect up to 5 userbots for high traffic load balancing.
- 🔒 **Backdoor-Free & Bug-Free**: Completely audited codebase with all external data leaks and hardcoded backdoors removed.

---

## 👤 Owner & Social Info

- **Owner**: [@ex_amrit](https://t.me/ex_amrit)
- **Owner ID**: `7576534973`
- **Support Group**: [amrit_feel](https://t.me/amrit_feel) (`-1004478038866`)
- **Updates Channel**: [privatethink](https://t.me/privatethink)
- **Instagram**: [ex_amrit](https://instagram.com/ex_amrit)
- **Snapchat**: [ex_amrit](https://snapchat.com/add/ex_amrit)

---

## 🚀 Koyeb Free Tier Deployment (24×7 Lifetime)

Deploying on Koyeb Free Tier is effortless and completely free:

1. **Fork or Push** this repository to your GitHub account.
2. Sign up on [Koyeb](https://www.koyeb.com/).
3. Click **Create App** → **GitHub**.
4. Select your repository.
5. In **Service Type**, choose **Web Service**.
6. Set **Instance Type** to **Nano (Free Tier)**.
7. Under **Environment Variables**, add:
   - `API_ID`: Your Telegram API ID from [my.telegram.org](https://my.telegram.org)
   - `API_HASH`: Your Telegram API Hash from [my.telegram.org](https://my.telegram.org)
   - `BOT_TOKEN`: Your Telegram Bot Token from [@BotFather](https://t.me/BotFather)
   - `MONGO_DB_URI`: Your MongoDB database connection string
   - `LOGGER_ID`: `-1004478038866` (or your log group ID)
   - `STRING_SESSION`: Pyrogram v2 string session of your assistant account
   - `OWNER_ID`: `7576534973`
   - `OWNER_USERNAME`: `ex_amrit`
   - `SUPPORT_CHAT`: `https://t.me/amrit_feel`
   - `SUPPORT_CHANNEL`: `https://t.me/privatethink`
   - `PORT`: `8000`
8. In **Ports**, enter `8000` with path `/`.
9. Click **Deploy**!

> 💡 **Keep Alive Lifetime**: Koyeb checks port `8000` automatically. You can also monitor your Koyeb URL (`https://<app>.koyeb.app/health`) with UptimeRobot or Cron-job.org for 100% 24x7 uptime.

---

## 🧹 Storage & Memory Management Commands

| Command | Description |
|:--|:--|
| `/clean` or `/cleancache` | Wipe temporary downloads, cache, and free RAM immediately with interactive buttons |
| `/freestorage` | Quick free extra disk storage |
| `/owner` | View owner details, support links, Instagram & Snapchat |
| `/stats` | View live system and RAM statistics with clean cache button |
| `/ping` | Check bot uptime, latency, and system health |

---

## 🎮 Playback Commands

| Command | Description |
|:--|:--|
| `/play <query/url>` | Play audio stream in group voice chat |
| `/vplay <query/url>` | Play video stream in group voice chat |
| `/pause` | Pause stream |
| `/resume` | Resume playback |
| `/skip` | Skip to the next queued song |
| `/stop` or `/end` | Stop stream and clear queue |
| `/queue` | View upcoming songs |
| `/loop <1-10>` | Loop current track |
| `/speed` | Change voice chat playback speed |
| `/reload` | Reload admin cache |

---

<div align="center">

Made with ❤️ by [ex_amrit](https://t.me/ex_amrit)

</div>
