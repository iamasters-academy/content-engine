#!/usr/bin/env python3
"""
upload_post.py — Publish a post via Upload-Post API to LinkedIn / Instagram / X.

Usage:
    python tools/upload_post.py \
        --image _assets/imagen.png \
        --caption "$(cat data/inbox-redes/.../linkedin.md)" \
        --platforms linkedin,instagram

Environment:
    UPLOAD_POST_API_KEY — required. Get it at https://upload-post.com

Endpoints:
    POST https://api.upload-post.com/api/upload_photos     (image posts)
    POST https://api.upload-post.com/api/upload            (video posts)
    GET  https://api.upload-post.com/api/uploadposts/status/{id}

Header: Authorization: Apikey YOUR_KEY
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

API_BASE = "https://api.upload-post.com/api"
ENDPOINT_PHOTOS = f"{API_BASE}/upload_photos"
ENDPOINT_VIDEO = f"{API_BASE}/upload"
ENDPOINT_STATUS = f"{API_BASE}/uploadposts/status"

VALID_PLATFORMS = {"linkedin", "instagram", "x", "tiktok", "youtube", "facebook", "threads"}


class UploadPostError(Exception):
    """Raised when Upload-Post API returns an error."""


def _build_multipart(fields: dict[str, str], file_path: Path | None, file_field: str = "media") -> tuple[bytes, str]:
    """Build multipart/form-data body using stdlib only."""
    boundary = f"----UploadPostBoundary{uuid.uuid4().hex}"
    lines: list[bytes] = []

    for key, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))

    if file_path is not None:
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        lines.append(f"--{boundary}".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'.encode()
        )
        lines.append(f"Content-Type: {mime}".encode())
        lines.append(b"")
        lines.append(file_path.read_bytes())

    lines.append(f"--{boundary}--".encode())
    lines.append(b"")
    return b"\r\n".join(lines), f"multipart/form-data; boundary={boundary}"


def _http(method: str, url: str, *, headers: dict, body: bytes | None = None) -> dict:
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        raise UploadPostError(f"HTTP {e.code} — {err_body}") from e
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def publish_photo(
    *,
    image_path: Path,
    caption: str,
    platforms: list[str],
    api_key: str | None = None,
) -> dict:
    """Publish a photo post to one or more platforms."""
    api_key = api_key or os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        raise UploadPostError(
            "UPLOAD_POST_API_KEY env var not set. Get one at https://upload-post.com"
        )

    if not image_path.exists():
        raise UploadPostError(f"Image not found: {image_path}")

    bad = [p for p in platforms if p not in VALID_PLATFORMS]
    if bad:
        raise UploadPostError(f"Invalid platform(s): {bad}. Must be in {sorted(VALID_PLATFORMS)}")

    fields = {
        "title": caption[:300] if len(caption) > 300 else caption,
        "caption": caption,
        "platforms[]": ",".join(platforms),
    }
    # Some Upload-Post endpoints expect platforms repeated as separate fields.
    # We pass both for safety.
    body, content_type = _build_multipart(fields, image_path, file_field="photos[]")

    headers = {
        "Authorization": f"Apikey {api_key}",
        "Content-Type": content_type,
    }
    return _http("POST", ENDPOINT_PHOTOS, headers=headers, body=body)


def get_status(job_id: str, *, api_key: str | None = None) -> dict:
    api_key = api_key or os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        raise UploadPostError("UPLOAD_POST_API_KEY env var not set.")
    headers = {"Authorization": f"Apikey {api_key}"}
    return _http("GET", f"{ENDPOINT_STATUS}/{job_id}", headers=headers)


def wait_until_published(job_id: str, *, timeout_s: int = 60, poll_s: float = 2.0) -> dict:
    """Poll the status endpoint until the post is published or fails."""
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        last = get_status(job_id)
        status = (last.get("status") or last.get("state") or "").lower()
        if status in {"published", "completed", "success"}:
            return last
        if status in {"failed", "error", "rejected"}:
            raise UploadPostError(f"Job {job_id} failed: {last}")
        time.sleep(poll_s)
    return last  # return whatever we have; caller can decide


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a photo post via Upload-Post API.")
    parser.add_argument("--image", required=True, help="Path to image file.")
    parser.add_argument("--caption", required=True, help="Post caption text.")
    parser.add_argument(
        "--platforms",
        required=True,
        help="Comma-separated platforms (linkedin,instagram,x,tiktok,youtube).",
    )
    parser.add_argument("--wait", action="store_true", help="Poll until published.")
    args = parser.parse_args()

    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    try:
        result = publish_photo(
            image_path=Path(args.image),
            caption=args.caption,
            platforms=platforms,
        )
        if args.wait:
            job_id = result.get("job_id") or result.get("id")
            if job_id:
                result = wait_until_published(job_id)
    except UploadPostError as e:
        print(f"[upload_post] error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
