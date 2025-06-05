#!/usr/bin/env python3.12
"""
Download a single YouTube video as MP4.

usage:
    python yt_grab.py <YouTube-URL> [output_directory]

requirements:
    pip install --upgrade yt-dlp
    ffmpeg (must be on PATH)
"""
from pathlib import Path
import sys
from yt_dlp import YoutubeDL


def download(url: str, out_dir: Path = Path.cwd()) -> None:
    """Grab <url> and save an MP4 in <out_dir>."""
    ydl_opts = {
        # 1) Pick the best compatible video+audio or fallback to any MP4
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        # 2) Force final container to MP4 even when streams differ
        "merge_output_format": "mp4",
        # 3) Nice filename: <title>.mp4
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        # 4) Single video, ignore playlists
        "noplaylist": True,
        # 5) Minimal but visible progress
        "progress_hooks": [lambda d: print(f"{d['status']}: {d.get('filename','')}")],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python yt_grab.py <YouTube-URL> [output_directory]")
    target_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)
    download(sys.argv[1], target_dir)
