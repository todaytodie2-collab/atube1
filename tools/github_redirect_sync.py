# -*- coding: utf-8 -*-
"""
A TuBe - GitHub Dynamic Redirection & Tunnel URL Synchronizer
Automatically updates docs/active_url.json and synchronizes it to GitHub Pages and/or Gists.
"""

import os
import sys
import json
import time
import datetime
import subprocess
import urllib.request
import urllib.parse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import PROJECT_ROOT

DOCS_JSON_PATH = os.path.join(PROJECT_ROOT, "docs", "active_url.json")
LOG_URL_PATH = os.path.join(PROJECT_ROOT, "logs", "current_tunnel_url.txt")

def update_local_active_url(tunnel_url: str) -> dict:
    """Updates docs/active_url.json with the new live URL."""
    clean_url = tunnel_url.strip().rstrip("/")
    payload = {
        "url": clean_url,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "online",
        "service": "A TuBe Streaming Platform",
        "version": "2.0.0"
    }
    
    os.makedirs(os.path.dirname(DOCS_JSON_PATH), exist_ok=True)
    with open(DOCS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    return payload

def sync_via_git(commit_msg: str = "chore: update active tunnel url [skip ci]") -> bool:
    """Commits and pushes docs/active_url.json using local git if available."""
    try:
        # Check if inside git repo
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # Add active_url.json
        subprocess.run(
            ["git", "add", "docs/active_url.json"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # Check if there are staged changes
        res = subprocess.run(
            ["git", "diff", "--staged", "--quiet"],
            cwd=PROJECT_ROOT
        )
        if res.returncode == 0:
            return True # No changes to commit
            
        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        # Push
        subprocess.run(
            ["git", "push"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
        print("[✓ GitHub Sync] Successfully committed and pushed active URL to Git repository.")
        return True
    except Exception as e:
        # Git push might fail if remote is not set or network is offline
        return False

def sync_via_github_api(payload: dict) -> bool:
    """Updates docs/active_url.json via GitHub REST API if GITHUB_TOKEN and GITHUB_REPO are set."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", os.environ.get("GITHUB_REPOSITORY", "")).strip()
    if not token or not repo:
        return False
        
    try:
        import base64
        api_url = f"https://api.github.com/repos/{repo}/contents/docs/active_url.json"
        
        # 1. Get existing file SHA if exists
        sha = None
        req = urllib.request.Request(api_url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "A-TuBe-Tunnel-Sync"
        })
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha")
        except Exception:
            pass
            
        # 2. Put file update
        body_content = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        b64_content = base64.b64encode(body_content).decode("ascii")
        
        put_data = {
            "message": f"update live tunnel url ({payload['url']})",
            "content": b64_content
        }
        if sha:
            put_data["sha"] = sha
            
        req_put = urllib.request.Request(
            api_url,
            data=json.dumps(put_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "A-TuBe-Tunnel-Sync"
            },
            method="PUT"
        )
        with urllib.request.urlopen(req_put, timeout=8) as resp:
            if resp.status in (200, 201):
                print(f"[✓ GitHub Sync] Updated docs/active_url.json on GitHub repo {repo} via REST API.")
                return True
    except Exception as e:
        print(f"[!] GitHub REST API sync notice: {e}")
    return False

def sync_via_github_gist(payload: dict) -> bool:
    """Updates a public or secret GitHub Gist with the latest active URL for instantaneous access."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    gist_id = os.environ.get("GIST_ID", "").strip()
    if not token or not gist_id:
        return False
        
    try:
        gist_url = f"https://api.github.com/gists/{gist_id}"
        patch_data = {
            "description": "A TuBe Live Active Tunnel URL",
            "files": {
                "active_url.json": {
                    "content": json.dumps(payload, indent=2, ensure_ascii=False)
                }
            }
        }
        req = urllib.request.Request(
            gist_url,
            data=json.dumps(patch_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "A-TuBe-Tunnel-Sync"
            },
            method="PATCH"
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                print(f"[✓ GitHub Sync] Successfully updated Gist ({gist_id}) with live URL: {payload['url']}")
                return True
    except Exception as e:
        print(f"[!] GitHub Gist sync notice: {e}")
    return False

def sync_tunnel_url(tunnel_url: str = "") -> dict:
    """Full synchronization pipeline called on tunnel startup or renewal."""
    if not tunnel_url and os.path.exists(LOG_URL_PATH):
        try:
            with open(LOG_URL_PATH, "r", encoding="utf-8") as f:
                tunnel_url = f.read().strip()
        except Exception:
            pass
            
    if not tunnel_url:
        tunnel_url = "http://127.0.0.1:8085"
        
    payload = update_local_active_url(tunnel_url)
    
    # Try all sync strategies in order
    synced_api = sync_via_github_api(payload)
    synced_gist = sync_via_github_gist(payload)
    if not synced_api:
        sync_via_git()
        
    return payload

if __name__ == "__main__":
    import sys
    url_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    result = sync_tunnel_url(url_arg)
    print(f"[🚀 A TuBe Sync] Finished syncing: {result['url']} ({result['updated_at']})")
