import os
from aiohttp import web
from BrandrdXMusic import LOGGER
import config


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
            <a href="{config.SUPPORT_CHANNEL}" class="btn btn-sub">Updates Channel</a>
        </div>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


async def start_web_server():
    """Starts aiohttp web server on PORT for Koyeb 24x7 web service uptime."""
    port = int(os.environ.get("PORT", getattr(config, "PORT", 8000)))
    app = web.Application()
    app.router.add_get("/", root_handler)
    app.router.add_get("/health", health_check)
    app.router.add_get("/ping", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER("BrandrdXMusic.web").info(f"Koyeb Web Server running on 0.0.0.0:{port} (24x7 Alive)")
