import asyncio
import json
import os
import re
import urllib.parse
import urllib.request

from aiohttp import web
from BrandrdXMusic import LOGGER, app
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import get_active_chats, group_assistant, is_active_chat
from BrandrdXMusic.utils.stream.queue import put_queue
from BrandrdXMusic.utils.thumbnails import get_thumb
import config

# Global in-memory vote skip pool: chat_id -> { user_id: user_name }
vote_skip_pool = {}
VOTES_NEEDED = 2


async def health_check(request):
    return web.Response(text="OK", status=200, content_type="text/plain")


async def root_handler(request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BrandrdXMusic - 24/7 Koyeb Service</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: rgba(30, 41, 59, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            max-width: 480px;
            width: 100%;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        h1 {{
            font-size: 26px;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .badge {{
            display: inline-block;
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 999px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 600;
            margin: 15px 0 25px;
        }}
        .info-list {{
            text-align: left;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 25px;
            font-size: 14px;
            line-height: 1.8;
        }}
        .info-list strong {{ color: #94a3b8; }}
        .info-list span, .info-list a {{ color: #f1f5f9; }}
        .btn {{
            display: inline-block;
            background: #6366f1;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            transition: 0.2s;
            margin: 4px;
        }}
        .btn:hover {{ background: #4f46e5; }}
        .btn-sub {{
            background: rgba(255,255,255,0.08);
            color: #cbd5e1;
        }}
        .btn-sub:hover {{ background: rgba(255,255,255,0.15); }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Music Bot Active</h1>
        <div class="badge">● RUNNING 24×7 ON KOYEB</div>
        <div class="info-list">
            <div><strong>Owner :</strong> <a href="https://t.me/{config.OWNER_USERNAME}">@{config.OWNER_USERNAME}</a></div>
            <div><strong>Owner ID :</strong> <code>{config.OWNER_ID}</code></div>
            <div><strong>Support Group :</strong> <a href="{config.SUPPORT_CHAT}">amrit_feel</a></div>
            <div><strong>Updates Channel :</strong> <a href="{config.SUPPORT_CHANNEL}">privatethink</a></div>
            <div><strong>Instagram :</strong> <a href="{config.OWNER_INSTAGRAM}">ex_amrit</a></div>
            <div><strong>Snapchat :</strong> <a href="{config.OWNER_SNAPCHAT}">ex_amrit</a></div>
        </div>
        <div>
            <a href="{config.SUPPORT_CHAT}" class="btn">Join Support</a>
            <a href="/webapp" class="btn btn-sub">📱 Open Mini App</a>
        </div>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def webapp_handler(request):
    """Renders modern interactive Telegram Mini App."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>BrandrdX Music Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg: #090d16;
            --surface: rgba(18, 24, 38, 0.7);
            --surface-hover: rgba(28, 38, 60, 0.85);
            --border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.35);
            --accent: #a855f7;
            --success: #10b981;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            background-image: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
                              radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 40%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            padding-bottom: 75px;
        }

        /* Top Header */
        header {
            position: sticky;
            top: 0;
            z-index: 50;
            background: rgba(9, 13, 22, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            padding: 14px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-icon {
            width: 32px;
            height: 32px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px var(--primary-glow);
            font-size: 16px;
        }

        .brand-title {
            font-size: 16px;
            font-weight: 700;
            background: linear-gradient(90deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 999px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.25);
            color: #34d399;
            font-size: 12px;
            font-weight: 600;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }

        /* Container */
        .container {
            flex: 1;
            padding: 16px;
            max-width: 600px;
            margin: 0 auto;
            width: 100%;
        }

        /* Tabs */
        .tab-content {
            display: none;
            animation: fadeIn 0.25s ease-in-out;
        }

        .tab-content.active {
            display: block;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Now Playing Card */
        .player-card {
            background: var(--surface);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }

        .player-card::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at center, rgba(99, 102, 241, 0.12) 0%, transparent 60%);
            pointer-events: none;
        }

        .track-header {
            display: flex;
            gap: 14px;
            align-items: center;
            margin-bottom: 16px;
        }

        .track-thumb {
            width: 80px;
            height: 80px;
            border-radius: 14px;
            object-fit: cover;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
            background: #1e293b;
        }

        .track-info {
            flex: 1;
            min-width: 0;
        }

        .track-title {
            font-size: 16px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .track-meta {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .req-badge {
            display: inline-block;
            font-size: 11px;
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.25);
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 500;
        }

        /* Progress Bar */
        .progress-box {
            margin-bottom: 16px;
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 8px;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            width: 35%;
            background: linear-gradient(90deg, #6366f1, #a855f7);
            border-radius: 999px;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px var(--primary-glow);
        }

        .time-labels {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Vote to Skip Box */
        .vote-box {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .vote-details {
            font-size: 13px;
        }

        .vote-title {
            font-weight: 600;
            color: #fff;
            margin-bottom: 2px;
        }

        .vote-count {
            font-size: 12px;
            color: var(--text-muted);
        }

        .btn-vote {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: #fff;
            border: none;
            padding: 9px 16px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
            transition: transform 0.15s, opacity 0.15s;
        }

        .btn-vote:active {
            transform: scale(0.96);
        }

        /* Section Headings */
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 18px 0 12px;
        }

        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Queue List */
        .queue-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .queue-item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: transform 0.15s;
        }

        .queue-item:active {
            transform: scale(0.99);
        }

        .queue-index {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.08);
            font-size: 12px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
        }

        .queue-thumb {
            width: 48px;
            height: 48px;
            border-radius: 10px;
            object-fit: cover;
            background: #1e293b;
        }

        .queue-info {
            flex: 1;
            min-width: 0;
        }

        .queue-title {
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 3px;
        }

        .queue-meta {
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .precache-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            color: var(--text-muted);
        }

        .empty-state svg {
            width: 48px;
            height: 48px;
            stroke: var(--text-muted);
            margin-bottom: 12px;
            opacity: 0.6;
        }

        /* Search Tab */
        .search-box {
            position: relative;
            margin-bottom: 16px;
        }

        .search-input {
            width: 100%;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 14px 44px 14px 16px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .search-btn {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--primary);
            color: #fff;
            border: none;
            border-radius: 10px;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }

        .chip-container {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 16px;
            scrollbar-width: none;
        }

        .chip {
            white-space: nowrap;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border);
            border-radius: 999px;
            padding: 6px 14px;
            font-size: 13px;
            color: var(--text-muted);
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
        }

        .chip:active, .chip.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }

        /* Search Results */
        .search-results {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .result-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .result-thumb {
            width: 60px;
            height: 60px;
            border-radius: 10px;
            object-fit: cover;
            background: #1e293b;
        }

        .result-info {
            flex: 1;
            min-width: 0;
        }

        .result-title {
            font-size: 14px;
            font-weight: 600;
            color: #fff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 3px;
        }

        .result-meta {
            font-size: 12px;
            color: var(--text-muted);
        }

        .btn-add {
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.35);
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.15s;
            white-space: nowrap;
        }

        .btn-add:active {
            background: var(--primary);
            color: #fff;
            transform: scale(0.95);
        }

        /* Bottom Tab Bar */
        nav.tab-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(9, 13, 22, 0.9);
            backdrop-filter: blur(20px);
            border-top: 1px solid var(--border);
            display: flex;
            padding: 8px 16px;
            z-index: 100;
            justify-content: space-around;
        }

        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 600;
            padding: 6px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: color 0.15s, transform 0.15s;
        }

        .tab-btn.active {
            color: #818cf8;
            background: rgba(99, 102, 241, 0.12);
        }

        .tab-btn svg {
            width: 20px;
            height: 20px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }

        /* Toast Alert */
        .toast {
            position: fixed;
            bottom: 85px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff;
            padding: 10px 18px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s, transform 0.25s;
            z-index: 200;
        }

        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-icon">🎵</div>
            <div class="brand-title">BrandrdX Music</div>
        </div>
        <div class="status-badge" id="statusBadge">
            <span class="status-dot"></span>
            <span id="statusText">LIVE IN VC</span>
        </div>
    </header>

    <div class="container">
        <!-- TAB 1: PLAYER & QUEUE -->
        <div id="playerTab" class="tab-content active">
            <!-- Now Playing -->
            <div class="player-card">
                <div class="track-header">
                    <img id="nowPlayingThumb" class="track-thumb" src="https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg" alt="Thumb">
                    <div class="track-info">
                        <div id="nowPlayingTitle" class="track-title">Loading track...</div>
                        <div class="track-meta">
                            <span id="nowPlayingDur">0:00</span>
                            <span>•</span>
                            <span id="nowPlayingBy" class="req-badge">By @user</span>
                        </div>
                    </div>
                </div>

                <div class="progress-box">
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill" style="width: 0%;"></div>
                    </div>
                    <div class="time-labels">
                        <span id="playedTime">0:00</span>
                        <span id="totalTime">0:00</span>
                    </div>
                </div>

                <div class="vote-box">
                    <div class="vote-details">
                        <div class="vote-title">🗳️ Vote to Skip</div>
                        <div id="voteCountText" class="vote-count">0 / 2 votes needed</div>
                    </div>
                    <button id="voteBtn" class="btn-vote" onclick="castVote()">
                        <span>🗳️ Skip</span>
                    </button>
                </div>
            </div>

            <!-- Queue Section -->
            <div class="section-header">
                <div class="section-title">
                    <span>📋 Up Next in Queue</span>
                    <span id="queueCount" style="color: var(--primary); font-size: 13px;">(0)</span>
                </div>
            </div>

            <div id="queueList" class="queue-list">
                <div class="empty-state">
                    <svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13M9 9l12-2M9 18a3 3 0 11-6 0 3 3 0 016 0zm12-2a3 3 0 11-6 0 3 3 0 016 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    <div>Queue is empty</div>
                    <div style="font-size: 12px; margin-top: 4px;">Tap 'Search' below to add songs!</div>
                </div>
            </div>
        </div>

        <!-- TAB 2: SEARCH SONGS -->
        <div id="searchTab" class="tab-content">
            <div class="search-box">
                <input id="searchInput" class="search-input" type="text" placeholder="Search song title or artist..." onkeypress="if(event.key === 'Enter') doSearch()">
                <button class="search-btn" onclick="doSearch()">🔍</button>
            </div>

            <div class="chip-container">
                <div class="chip" onclick="quickSearch('Trending Bollywood 2026')">🔥 Trending</div>
                <div class="chip" onclick="quickSearch('Arijit Singh Hits')">❤️ Arijit Singh</div>
                <div class="chip" onclick="quickSearch('Punjabi Top Songs')">💃 Punjabi</div>
                <div class="chip" onclick="quickSearch('English Pop Hits')">🌎 English Pop</div>
                <div class="chip" onclick="quickSearch('Lofi Chill Songs')">🌙 Lo-Fi Chill</div>
            </div>

            <div id="searchResults" class="search-results">
                <div class="empty-state">
                    <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                    <div>Type a song name above to search</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Navigation Bar -->
    <nav class="tab-bar">
        <button id="navPlayer" class="tab-btn active" onclick="switchTab('player')">
            <svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13M9 9l12-2M9 18a3 3 0 11-6 0 3 3 0 016 0zm12-2a3 3 0 11-6 0 3 3 0 016 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>Live Queue</span>
        </button>
        <button id="navSearch" class="tab-btn" onclick="switchTab('search')">
            <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>Search & Play</span>
        </button>
    </nav>

    <!-- Toast -->
    <div id="toast" class="toast">
        <span id="toastIcon">✅</span>
        <span id="toastMsg">Notification</span>
    </div>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }

        const urlParams = new URLSearchParams(window.location.search);
        let chatId = urlParams.get('chat_id') || tg?.initDataUnsafe?.chat?.id || null;
        let currentUser = tg?.initDataUnsafe?.user || { id: 7576534973, first_name: "Member" };

        function showToast(msg, icon = '✅') {
            const toast = document.getElementById('toast');
            document.getElementById('toastIcon').innerText = icon;
            document.getElementById('toastMsg').innerText = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }
        }

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            if (tab === 'player') {
                document.getElementById('navPlayer').classList.add('active');
                document.getElementById('playerTab').classList.add('active');
                fetchQueue();
            } else {
                document.getElementById('navSearch').classList.add('active');
                document.getElementById('searchTab').classList.add('active');
            }
        }

        function quickSearch(q) {
            document.getElementById('searchInput').value = q;
            doSearch();
        }

        async function fetchQueue() {
            if (!chatId) return;
            try {
                const res = await fetch(`/api/queue?chat_id=${chatId}`);
                const data = await res.json();

                if (!data.active || !data.current) {
                    document.getElementById('nowPlayingTitle').innerText = 'No Active Stream';
                    document.getElementById('nowPlayingDur').innerText = '0:00';
                    document.getElementById('nowPlayingBy').innerText = 'Idle';
                    document.getElementById('statusText').innerText = 'IDLE';
                    document.getElementById('statusBadge').style.borderColor = 'rgba(148, 163, 184, 0.2)';
                    document.getElementById('statusBadge').style.color = '#94a3b8';
                    document.getElementById('statusBadge').querySelector('.status-dot').style.background = '#94a3b8';
                    document.getElementById('queueList').innerHTML = `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13M9 9l12-2M9 18a3 3 0 11-6 0 3 3 0 016 0zm12-2a3 3 0 11-6 0 3 3 0 016 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            <div>No songs playing right now</div>
                            <div style="font-size: 12px; margin-top: 4px;">Tap 'Search & Play' to start streaming!</div>
                        </div>`;
                    document.getElementById('queueCount').innerText = '(0)';
                    return;
                }

                // Active Stream
                const cur = data.current;
                document.getElementById('nowPlayingTitle').innerText = cur.title;
                document.getElementById('nowPlayingThumb').src = cur.thumb || 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg';
                document.getElementById('nowPlayingDur').innerText = cur.dur;
                document.getElementById('nowPlayingBy').innerText = `By ${cur.by || 'Member'}`;
                document.getElementById('totalTime').innerText = cur.dur;
                document.getElementById('statusText').innerText = 'LIVE IN VC';

                // Progress Bar
                const playedSec = cur.played || 0;
                const totalSec = cur.seconds || 1;
                const pct = Math.min(100, Math.max(0, (playedSec / totalSec) * 100));
                document.getElementById('progressFill').style.width = `${pct}%`;
                const m = Math.floor(playedSec / 60);
                const s = Math.floor(playedSec % 60);
                document.getElementById('playedTime').innerText = `${m}:${s < 10 ? '0' : ''}${s}`;

                // Vote info
                const votes = data.votes || { count: 0, needed: 2 };
                document.getElementById('voteCountText').innerText = `${votes.count} / ${votes.needed} votes needed`;
                if (votes.user_voted) {
                    document.getElementById('voteBtn').innerText = '✅ Voted';
                    document.getElementById('voteBtn').style.opacity = '0.7';
                } else {
                    document.getElementById('voteBtn').innerText = '🗳️ Skip';
                    document.getElementById('voteBtn').style.opacity = '1';
                }

                // Queue items
                const q = data.queue || [];
                document.getElementById('queueCount').innerText = `(${q.length})`;
                if (q.length === 0) {
                    document.getElementById('queueList').innerHTML = `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13M9 9l12-2M9 18a3 3 0 11-6 0 3 3 0 016 0zm12-2a3 3 0 11-6 0 3 3 0 016 0z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            <div>Queue is empty</div>
                            <div style="font-size: 12px; margin-top: 4px;">Tap 'Search & Play' to queue more songs!</div>
                        </div>`;
                } else {
                    let html = '';
                    q.forEach(item => {
                        html += `
                            <div class="queue-item">
                                <div class="queue-index">#${item.position}</div>
                                <img class="queue-thumb" src="${item.thumb}" alt="Thumb">
                                <div class="queue-info">
                                    <div class="queue-title">${item.title}</div>
                                    <div class="queue-meta">
                                        <span>${item.dur}</span>
                                        <span>•</span>
                                        <span>By ${item.by}</span>
                                        ${item.is_ready ? '<span class="precache-badge">⚡ READY</span>' : ''}
                                    </div>
                                </div>
                            </div>`;
                    });
                    document.getElementById('queueList').innerHTML = html;
                }
            } catch (e) {
                console.error("fetchQueue error:", e);
            }
        }

        async function castVote() {
            if (!chatId) return;
            try {
                const res = await fetch('/api/vote_skip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat_id: chatId,
                        user_id: currentUser.id,
                        user_name: currentUser.first_name
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message, data.skipped ? '⏭️' : '🗳️');
                    fetchQueue();
                } else {
                    showToast(data.message || 'Vote failed', '⚠️');
                }
            } catch (e) {
                showToast('Error casting vote', '❌');
            }
        }

        async function doSearch() {
            const q = document.getElementById('searchInput').value.trim();
            if (!q) return;
            const container = document.getElementById('searchResults');
            container.innerHTML = '<div class="empty-state">Searching songs... 🔍</div>';

            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                const results = data.results || [];

                if (results.length === 0) {
                    container.innerHTML = '<div class="empty-state">No songs found. Try a different query.</div>';
                    return;
                }

                let html = '';
                results.forEach(it => {
                    const safeTitle = it.title.replace(/'/g, "\\\\'");
                    html += `
                        <div class="result-card">
                            <img class="result-thumb" src="${it.thumb}" alt="Thumb">
                            <div class="result-info">
                                <div class="result-title">${it.title}</div>
                                <div class="result-meta">${it.duration || '3:00'} • ${it.uploader || 'Audio'}</div>
                            </div>
                            <button class="btn-add" onclick="addToQueue('${it.vidid}', '${safeTitle}', '${it.duration}')">
                                ➕ Add
                            </button>
                        </div>`;
                });
                container.innerHTML = html;
            } catch (e) {
                container.innerHTML = '<div class="empty-state">Search error. Please try again.</div>';
            }
        }

        async function addToQueue(vidid, title, duration) {
            if (!chatId) {
                showToast('Chat ID not detected', '⚠️');
                return;
            }
            try {
                const res = await fetch('/api/play', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat_id: chatId,
                        vidid: vidid,
                        title: title,
                        duration: duration,
                        user_id: currentUser.id,
                        user_name: currentUser.first_name
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Added to queue (#${data.position})!`, '🎵');
                    switchTab('player');
                } else {
                    showToast(data.message || 'Failed to add', '⚠️');
                }
            } catch (e) {
                showToast('Failed to queue song', '❌');
            }
        }

        // Auto poll queue every 3 seconds
        fetchQueue();
        setInterval(fetchQueue, 3000);
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def api_queue_handler(request):
    """API endpoint to get live current track and queue for a chat."""
    chat_id_raw = request.query.get("chat_id")
    if not chat_id_raw:
        return web.json_response({"active": False, "message": "Missing chat_id"})

    try:
        chat_id = int(chat_id_raw)
    except ValueError:
        return web.json_response({"active": False, "message": "Invalid chat_id"})

    queue_data = db.get(chat_id)
    if not queue_data or not await is_active_chat(chat_id):
        return web.json_response({"active": False, "current": None, "queue": []})

    cur = queue_data[0]
    vidid = cur.get("vidid", "")
    thumb = f"https://img.youtube.com/vi/{vidid}/hqdefault.jpg" if vidid and vidid not in ("telegram", "soundcloud") else config.SOUNCLOUD_IMG_URL

    current = {
        "title": cur.get("title", "Unknown Track"),
        "dur": cur.get("dur", "0:00"),
        "seconds": cur.get("seconds", 0),
        "played": cur.get("played", 0),
        "by": cur.get("by", "Member"),
        "vidid": vidid,
        "thumb": thumb,
        "streamtype": cur.get("streamtype", "audio"),
    }

    upcoming = []
    for idx, item in enumerate(queue_data[1:]):
        item_vid = item.get("vidid", "")
        item_file = str(item.get("file", ""))
        is_ready = not item_file.startswith("vid_")
        item_thumb = f"https://img.youtube.com/vi/{item_vid}/hqdefault.jpg" if item_vid and item_vid not in ("telegram", "soundcloud") else config.SOUNCLOUD_IMG_URL
        upcoming.append({
            "position": idx + 1,
            "title": item.get("title", "Track"),
            "dur": item.get("dur", "0:00"),
            "by": item.get("by", "Member"),
            "vidid": item_vid,
            "thumb": item_thumb,
            "is_ready": is_ready,
        })

    votes = vote_skip_pool.get(chat_id, {})
    return web.json_response({
        "active": True,
        "current": current,
        "queue": upcoming,
        "votes": {
            "count": len(votes),
            "needed": VOTES_NEEDED,
        }
    })


async def api_search_handler(request):
    """API endpoint to search songs across YouTube & JioSaavn."""
    query = request.query.get("q", "").strip()
    if not query:
        return web.json_response({"results": []})

    results = []

    # 1. Try py_yt VideosSearch
    try:
        from py_yt import VideosSearch
        vs = VideosSearch(query, limit=8)
        search_res = (await vs.next()).get("result", [])
        for item in search_res:
            vid = item.get("id")
            if vid:
                results.append({
                    "title": item.get("title", "Unknown Track"),
                    "vidid": vid,
                    "duration": item.get("duration", "3:00"),
                    "thumb": item.get("thumbnails", [{}])[0].get("url", "").split("?")[0],
                    "uploader": item.get("channel", {}).get("name", "YouTube"),
                })
        if results:
            return web.json_response({"results": results})
    except Exception as e:
        LOGGER("BrandrdXMusic.web").warning(f"VideosSearch error in api_search: {e}")

    # 2. Fallback: JioSaavn Search
    try:
        search_query = re.sub(r"[^\w\s]", " ", query).strip()
        search_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={urllib.parse.quote(search_query)}"
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            songs = data.get("songs", {}).get("data", [])
            for s in songs[:8]:
                results.append({
                    "title": s.get("title", "Track"),
                    "vidid": s.get("id", "saavn"),
                    "duration": "3:30",
                    "thumb": s.get("image", "").replace("50x50", "250x250"),
                    "uploader": s.get("more_info", {}).get("primary_artists", "JioSaavn"),
                })
    except Exception as e:
        LOGGER("BrandrdXMusic.web").warning(f"JioSaavn search error: {e}")

    return web.json_response({"results": results})


async def api_vote_skip_handler(request):
    """API endpoint to cast vote-to-skip from Mini App."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    chat_id_raw = data.get("chat_id")
    user_id = data.get("user_id")
    user_name = data.get("user_name", "Member")

    if not chat_id_raw or not user_id:
        return web.json_response({"success": False, "message": "Missing chat_id or user_id"}, status=400)

    try:
        chat_id = int(chat_id_raw)
    except ValueError:
        return web.json_response({"success": False, "message": "Invalid chat_id"}, status=400)

    if not await is_active_chat(chat_id) or not db.get(chat_id):
        return web.json_response({"success": False, "message": "Nothing is playing in voice chat right now."})

    if chat_id not in vote_skip_pool:
        vote_skip_pool[chat_id] = {}

    votes = vote_skip_pool[chat_id]

    if user_id in votes:
        return web.json_response({
            "success": True,
            "message": f"Already voted! ({len(votes)}/{VOTES_NEEDED} votes)",
            "count": len(votes),
            "needed": VOTES_NEEDED,
            "skipped": False,
        })

    votes[user_id] = user_name
    count = len(votes)

    if count >= VOTES_NEEDED:
        vote_skip_pool[chat_id] = {}
        try:
            assistant = await group_assistant(Hotty, chat_id)
            await Hotty.change_stream(assistant, chat_id)
            try:
                await app.send_message(
                    chat_id,
                    f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ ᴘᴀssᴇᴅ!</b>\n\n» {VOTES_NEEDED}/{VOTES_NEEDED} ᴠᴏᴛᴇs ʀᴇᴀᴄʜᴇᴅ ᴠɪᴀ ᴍɪɴɪ ᴀᴘᴘ.\n» ɴᴏᴡ ᴘʟᴀʏɪɴɢ ɴᴇxᴛ ᴛʀᴀᴄᴋ!"
                )
            except Exception:
                pass
            return web.json_response({
                "success": True,
                "skipped": True,
                "count": count,
                "needed": VOTES_NEEDED,
                "message": "Vote passed! Skipped to next track.",
            })
        except Exception as e:
            LOGGER("BrandrdXMusic.web").error(f"Error skipping via vote: {e}")
            return web.json_response({"success": False, "message": "Error skipping track."})

    try:
        await app.send_message(
            chat_id,
            f"🗳️ <b>ᴠᴏᴛᴇ-ᴛᴏ-sᴋɪᴘ (ᴍɪɴɪ ᴀᴘᴘ) :</b>\n» <b>ᴠᴏᴛᴇʀ :</b> {user_name}\n» <b>ᴠᴏᴛᴇs :</b> {count}/{VOTES_NEEDED} ɴᴇᴇᴅᴇᴅ ᴛᴏ sᴋɪᴘ."
        )
    except Exception:
        pass

    return web.json_response({
        "success": True,
        "skipped": False,
        "count": count,
        "needed": VOTES_NEEDED,
        "message": f"Vote recorded! ({count}/{VOTES_NEEDED} votes)",
    })


async def api_play_handler(request):
    """API endpoint to queue a song via the Mini App."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"success": False, "message": "Invalid JSON"}, status=400)

    chat_id_raw = data.get("chat_id")
    vidid = data.get("vidid")
    title = data.get("title", "Track")
    duration = data.get("duration", "3:00")
    user_id = data.get("user_id", 0)
    user_name = data.get("user_name", "Member")

    if not chat_id_raw or not vidid:
        return web.json_response({"success": False, "message": "Missing chat_id or vidid"}, status=400)

    try:
        chat_id = int(chat_id_raw)
    except ValueError:
        return web.json_response({"success": False, "message": "Invalid chat_id"}, status=400)

    if await is_active_chat(chat_id):
        await put_queue(
            chat_id,
            chat_id,
            f"vid_{vidid}",
            title,
            duration,
            user_name,
            vidid,
            user_id,
            "audio",
        )
        position = len(db.get(chat_id, [])) - 1
        # Trigger background pre-caching for gapless playback
        await Hotty.precache_next_track(chat_id)

        try:
            await app.send_message(
                chat_id,
                f"📱 <b>ᴀᴅᴅᴇᴅ ᴠɪᴀ ᴍɪɴɪ ᴀᴘᴘ :</b>\n\n» <b>ᴛɪᴛʟᴇ :</b> {title[:40]}\n» <b>ǫᴜᴇᴜᴇ ᴘᴏsɪᴛɪᴏɴ :</b> #{position}\n» <b>ᴀᴅᴅᴇᴅ ʙʏ :</b> {user_name}"
            )
        except Exception:
            pass

        return web.json_response({
            "success": True,
            "queued": True,
            "position": position,
            "title": title,
        })
    else:
        # Voice chat not yet active in this group
        return web.json_response({
            "success": False,
            "message": "Voice chat is not active. Please start the voice chat with /play in group first!"
        })


async def start_web_server():
    """Starts aiohttp web server on PORT for Koyeb 24x7 web service uptime and Mini App."""
    port = int(os.environ.get("PORT", getattr(config, "PORT", 8000)))
    app_runner = web.Application()
    app_runner.router.add_get("/", root_handler)
    app_runner.router.add_get("/health", health_check)
    app_runner.router.add_get("/ping", health_check)
    app_runner.router.add_get("/webapp", webapp_handler)
    app_runner.router.add_get("/api/queue", api_queue_handler)
    app_runner.router.add_get("/api/search", api_search_handler)
    app_runner.router.add_post("/api/vote_skip", api_vote_skip_handler)
    app_runner.router.add_post("/api/play", api_play_handler)

    runner = web.AppRunner(app_runner)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER("BrandrdXMusic.web").info(f"Koyeb Web Server & Mini App running on 0.0.0.0:{port} (24x7 Alive)")
