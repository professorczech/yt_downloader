#!/usr/bin/env python3.12
"""
yt_grab.py – resilient MP4 downloader (Python 3.12)
pip install -U yt-dlp
"""

from pathlib import Path
import sys, argparse
from yt_dlp import YoutubeDL, utils

def build_opts(out_dir: Path, use_cookies: bool) -> dict:
    opts = {
        "format": "bv*[vcodec^=avc1][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best",
        "hls_prefer_native": False,
        "fragment_retries": 5,
        "merge_output_format": "mp4",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [lambda d: print(f"{d['status']}: {d.get('filename','')}")],
    }
    if use_cookies:
        # ← pick ONE of the lines below
        # opts["cookiefile"] = "brave.txt"           # fix B
        opts["cookiesfrombrowser"] = ("brave",)      # fix A/C
    return opts

def download(url: str, opts: dict):
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
    except utils.DownloadError as e:
        print(f"[yt-grab] Download failed: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="YouTube link")
    ap.add_argument("-d", "--dir", default=".", help="output directory")
    ap.add_argument("--cookies", action="store_true",
                    help="use browser cookies (requires Brave closed)")
    args = ap.parse_args()

    target = Path(args.dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    download(args.url, build_opts(target, args.cookies))
