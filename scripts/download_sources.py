"""Download explicit source-manifest URL excerpts with yt-dlp and ffmpeg."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def download(manifest: Path):
    if not shutil.which("yt-dlp") or not shutil.which("ffmpeg"):
        raise ValueError("Install yt-dlp and ffmpeg before downloading source excerpts")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    incoming = manifest.parent / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    for item in data["speeches"]:
        if item.get("audio_path"):
            continue
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", item["id"]):
            raise ValueError("Source IDs must be simple slugs")
        url = item.get("audio_url", item["source"])
        if not url.startswith(("https://", "http://")):
            raise ValueError("An explicit HTTP(S) source URL is required")
        start, end = float(item.get("start", 0)), float(item.get("end", 90))
        if not 0 <= start < end <= start + 600:
            raise ValueError("Source excerpt must be between 0 and 10 minutes")
        output = str(incoming / (item["id"] + ".%(ext)s"))
        subprocess.run(["yt-dlp", "--no-playlist", "--max-filesize", "200M",
                        "--download-sections", f"*{start}-{end}", "-x",
                        "--audio-format", "wav", "--postprocessor-args",
                        "ffmpeg:-ar 16000 -ac 1", "-o", output, "--", url],
                       check=True, timeout=300)
        expected = incoming / (item["id"] + ".wav")
        if not expected.exists():
            raise ValueError("Downloader did not produce the expected WAV")
        item["audio_path"] = "incoming/" + expected.name
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Downloaded {item['id']}; review attribution and transcript before import")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    download(parser.parse_args().manifest)
