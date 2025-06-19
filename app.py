#!/usr/bin/env python3.12
"""
pip install -U yt-dlp flask-socketio python-socketio
python app.py
(No eventlet/gevent required; we use the standard-thread async mode)
"""
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO
from yt_dlp import YoutubeDL, utils
import secrets, math

# ── Flask / Socket.IO ────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me"
# use blocking threads so we don’t depend on monkey-patching
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

DL_DIR = Path("downloads")
DL_DIR.mkdir(exist_ok=True)

# ── yt-dlp option builder ───────────────────────────────────────────────
def build_opts(dest: Path, mbps: float | None, use_cookies: bool, job_id: str):
    def _hook(d):
        if d["status"] != "downloading":
            return
        # robust % calc in case _percent_str missing
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        done  = d.get("downloaded_bytes", 0)
        pct   = f"{done / total * 100:.1f} %" if total else "?"
        socketio.emit("progress", {
            "job":   job_id,
            "pct":   pct,
            "eta":   (d.get('_eta_str')  or '—'),
            "speed": (d.get('_speed_str') or '—'),
        })

    opts = {
        "format": "bv*[vcodec^=avc1][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "hls_prefer_native": False,
        "fragment_retries": 5,
        "outtmpl": str(dest / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [_hook],
    }
    if mbps:
        opts["ratelimit"] = int(mbps * 1024 * 1024)  # bytes / s
    if use_cookies:
        opts["cookiesfrombrowser"] = ("brave",)
    return opts

# ── download worker ─────────────────────────────────────────────────────
def ytdl_worker(url: str, opts: dict, job_id: str):
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        socketio.emit("complete", {"job": job_id})
    except utils.DownloadError as exc:
        socketio.emit("error", {"job": job_id, "msg": str(exc)})

# ── routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    files = sorted(p.name for p in DL_DIR.glob("*.mp4"))
    return render_template("index.html", files=files, default_dir=str(DL_DIR))

@app.route("/download", methods=["POST"])
def download():
    job_id = secrets.token_hex(4)
    url    = request.form["url"].strip()
    mbps   = float(request.form.get("speed") or 0) or None
    dest   = Path(request.form.get("folder") or DL_DIR).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    opts   = build_opts(dest, mbps, "cookies" in request.form, job_id)
    # launch in a background thread managed by Flask-SocketIO
    socketio.start_background_task(ytdl_worker, url, opts, job_id)
    return jsonify(job=job_id), 202

@app.route("/downloads/<path:filename>")
def downloads(filename):
    return send_from_directory(DL_DIR, filename, as_attachment=True)

# ── main ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, debug=True)
