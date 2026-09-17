# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture - Central Configuration & Settings
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env variables if present
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", BASE_DIR)

# SQLite Database Path (WAL Mode)
DB_PATH = os.path.join(PROJECT_ROOT, "config", "atube_data.sqlite")

# Server Configuration
SERVER_HOST = os.environ.get("HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", 8085))
DEBUG_MODE = os.environ.get("DEBUG", "0") == "1"

# Universal Browser User-Agent
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

def get_tmdb_api_key() -> str:
    """Retrieves active TMDB API key from env, config file, or fallback."""
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if key:
        return key
    cfg_file = os.path.join(PROJECT_ROOT, "config", "remote_config.json")
    if os.path.exists(cfg_file):
        try:
            import json
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                k = cfg.get("tmdb", {}).get("api_key", "").strip()
                if k:
                    return k
        except Exception:
            pass
    return "cabefb963ee5db1ecd2c5778bda9b6d0"

# Host Spoofing Map
HOST_SPOOF_MAP = {
    # Video Streaming Hosts
    "vipserver": ("https://mycima.buzz/", "https://mycima.buzz"),
    "liiivideo": ("https://mycima.buzz/", "https://mycima.buzz"),
    "bysebuho": ("https://egydead.live/", "https://egydead.live"),
    "minochinos": ("https://egydead.live/", "https://egydead.live"),
    "megamax": ("https://egydead.live/", "https://egydead.live"),
    "vidmoly": ("https://vidmoly.to/", "https://vidmoly.to"),
    "mixdrop": ("https://mixdrop.ag/", "https://mixdrop.ag"),
    "voe": ("https://voe.sx/", "https://voe.sx"),
    "streamtape": ("https://streamtape.com/", "https://streamtape.com"),
    "dood": ("https://dood.to/", "https://dood.to"),
    "ds2play": ("https://dood.to/", "https://dood.to"),
    "upstream": ("https://upstream.to/", "https://upstream.to"),
    "hgcloud": ("https://vidsrc.pm/", "https://vidsrc.pm"),
    "filelions": ("https://filelions.online/", "https://filelions.online"),
    "streamwish": ("https://streamwish.to/", "https://streamwish.to"),
    "streamhub": ("https://streamhub.to/", "https://streamhub.to"),
    
    # Arabic Portals & Mirrors
    "akwam": ("https://akwam.to/", "https://akwam.to"),
    "akwam.to": ("https://akwam.to/", "https://akwam.to"),
    "akwam.link": ("https://akwam.link/", "https://akwam.link"),
    "akwam.cc": ("https://akwam.cc/", "https://akwam.cc"),
    "mycima": ("https://mycima.buzz/", "https://mycima.buzz"),
    "wecima": ("https://wecima.show/", "https://wecima.show"),
    "we-cima": ("https://wecima.show/", "https://wecima.show"),
    "my-cima": ("https://mycima.buzz/", "https://mycima.buzz"),
    "w-cima": ("https://wecima.show/", "https://wecima.show"),
    "fasel": ("https://faselhd.club/", "https://faselhd.club"),
    "faselhd": ("https://faselhd.club/", "https://faselhd.club"),
    "fasel-hd": ("https://faselhd.club/", "https://faselhd.club"),
    "arabseed": ("https://m.arabseed.site/", "https://m.arabseed.site"),
    "arabseed.site": ("https://m.arabseed.site/", "https://m.arabseed.site"),
    "arabseed.net": ("https://m.arabseed.site/", "https://m.arabseed.site"),
    "arabseed.show": ("https://m.arabseed.show/", "https://m.arabseed.show"),
    "cima4u": ("https://cima4u.tv/", "https://cima4u.tv"),
    "cima4u.tv": ("https://cima4u.tv/", "https://cima4u.tv"),
    "cima4u.cam": ("https://cima4u.cam/", "https://cima4u.cam"),
    "topcinema": ("https://topcinema.cam/", "https://topcinema.cam"),
    "topcinema.cam": ("https://topcinema.cam/", "https://topcinema.cam"),
    "egydead": ("https://egydead.live/", "https://egydead.live"),
    "egydead.live": ("https://egydead.live/", "https://egydead.live"),
    "egydead.net": ("https://egydead.net/", "https://egydead.net"),
    "shahid4u": ("https://shahid4u.com/", "https://shahid4u.com"),
    "shahed4u": ("https://shahid4u.com/", "https://shahid4u.com"),

    # Global TMDB Gateways & Mirrors
    "vidsrc": ("https://vidsrc.pm/", "https://vidsrc.pm"),
    "vidlink": ("https://vidlink.pro/", "https://vidlink.pro"),
    "multiembed": ("https://multiembed.mov/", "https://multiembed.mov"),
    "2embed": ("https://www.2embed.cc/", "https://www.2embed.cc"),
    "autoembed": ("https://autoembed.to/", "https://autoembed.to"),
    "streamingnow": ("https://streamingnow.mov/", "https://streamingnow.mov"),
}

# Trusted Global Embed Gateways
TRUSTED_EMBED_KEYWORDS = [
    "vidlink",
    "multiembed",
    "2embed",
    "vidsrc",
    "autoembed",
    "streamingnow",
    "hgcloud",
]

# Arabic Category Feed Mapping
CATEGORY_MAP = {
    "أفلام أجنبي": ("movie", "foreign"),
    "افلام اجنبي": ("movie", "foreign"),
    "أفلام عربي": ("movie", "arabic"),
    "افلام عربي": ("movie", "arabic"),
    "أفلام تركي": ("movie", "turkish"),
    "افلام تركي": ("movie", "turkish"),
    "أفلام هندي": ("movie", "indian"),
    "افلام هندي": ("movie", "indian"),
    "أفلام أنمي": ("movie", "anime"),
    "افلام انمي": ("movie", "anime"),
    "أفلام آسيوي": ("movie", "asian"),
    "أفلام وثائقية": ("movie", "documentary"),
    "مسلسلات أجنبي": ("series", "foreign"),
    "مسلسلات اجنبي": ("series", "foreign"),
    "مسلسلات عربي": ("series", "arabic"),
    "مسلسلات تركي": ("series", "turkish"),
    "مسلسلات هندي": ("series", "indian_series"),
    "مسلسلات أنمي": ("series", "anime"),
    "مسلسلات كورية": ("series", "korean_series"),
    "مسلسلات كورية وآسيوية": ("series", "korean_series"),
    "مسلسلات وثائقية": ("series", "documentary"),
    "كارتون للأطفال": ("kids", "cartoon"),
    "مسرحيات": ("movie", "plays"),
    "مصارعة حرة": ("wwe", "wwe"),
    "مصارعة WWE": ("wwe", "wwe"),
    "wwe": ("wwe", "all"),
    "أنمي": ("anime", "anime"),
    "anime": ("anime", "all"),
    "عالم Atube": ("atube", "atube"),
    "atube": ("atube", "all"),
    "وصل حديثاً": ("all", "recent"),
    "الأكثر مشاهدة في السعودية": ("all", "trending_sa"),
}
