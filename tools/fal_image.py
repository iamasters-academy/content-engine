#!/usr/bin/env python3
"""
fal_image.py — Generate images with Fal.ai's nano-banana-2 (Google).

Usage:
    python tools/fal_image.py \
        --prompt "A professional woman at desk with invoices, split-screen..." \
        --aspect-ratio 1:1 \
        --resolution 1K \
        --output _assets/imagen.png

Environment:
    FAL_KEY — required. Get it at https://fal.ai/dashboard/keys

Model: fal-ai/nano-banana-2
Docs:  https://fal.ai/models/fal-ai/nano-banana-2/api
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://queue.fal.run"
MODEL_ID = "fal-ai/nano-banana-2"

VALID_ASPECT_RATIOS = {
    "auto", "21:9", "16:9", "3:2", "4:3", "5:4", "1:1",
    "4:5", "3:4", "2:3", "9:16", "4:1", "1:4", "8:1", "1:8",
}
VALID_RESOLUTIONS = {"0.5K", "1K", "2K", "4K"}
VALID_FORMATS = {"jpeg", "png", "webp"}


class FalError(Exception):
    """Raised when Fal.ai API returns an error or times out."""


def _request(method: str, url: str, *, headers: dict, body: dict | None = None) -> dict:
    """Minimal HTTP client using stdlib (no extra deps)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        raise FalError(f"HTTP {e.code} — {err_body}") from e


def submit(api_key: str, payload: dict) -> str:
    """Submit a generation request. Returns request_id."""
    url = f"{API_BASE}/{MODEL_ID}"
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }
    result = _request("POST", url, headers=headers, body=payload)
    request_id = result.get("request_id")
    if not request_id:
        raise FalError(f"No request_id in response: {result}")
    return request_id


def poll(api_key: str, request_id: str, *, timeout_s: int = 90, poll_interval_s: float = 1.5) -> dict:
    """Poll until the request completes. Returns the final result dict."""
    status_url = f"{API_BASE}/{MODEL_ID}/requests/{request_id}/status"
    result_url = f"{API_BASE}/{MODEL_ID}/requests/{request_id}"
    headers = {"Authorization": f"Key {api_key}"}

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = _request("GET", status_url, headers=headers)
        if status.get("status") == "COMPLETED":
            return _request("GET", result_url, headers=headers)
        if status.get("status") in {"FAILED", "CANCELLED"}:
            raise FalError(f"Request {request_id} ended with status {status}")
        time.sleep(poll_interval_s)
    raise FalError(f"Request {request_id} timed out after {timeout_s}s")


def download(url: str, output_path: Path) -> None:
    """Download an image URL to a local path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as resp, open(output_path, "wb") as f:
        f.write(resp.read())


def generate(
    *,
    prompt: str,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    output_format: str = "png",
    num_images: int = 1,
    enable_web_search: bool = False,
    thinking_level: str | None = None,
    api_key: str | None = None,
) -> dict:
    """High-level: submit + poll + return the result. Does not download."""
    api_key = api_key or os.environ.get("FAL_KEY")
    if not api_key:
        raise FalError("FAL_KEY env var not set. Get one at https://fal.ai/dashboard/keys")

    if aspect_ratio not in VALID_ASPECT_RATIOS:
        raise FalError(f"Invalid aspect_ratio. Must be one of: {sorted(VALID_ASPECT_RATIOS)}")
    if resolution not in VALID_RESOLUTIONS:
        raise FalError(f"Invalid resolution. Must be one of: {sorted(VALID_RESOLUTIONS)}")
    if output_format not in VALID_FORMATS:
        raise FalError(f"Invalid output_format. Must be one of: {sorted(VALID_FORMATS)}")

    payload: dict = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "output_format": output_format,
        "num_images": num_images,
    }
    if enable_web_search:
        payload["enable_web_search"] = True
    if thinking_level in {"minimal", "high"}:
        payload["thinking_level"] = thinking_level

    request_id = submit(api_key, payload)
    return poll(api_key, request_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an image with Fal.ai nano-banana-2.")
    parser.add_argument("--prompt", required=True, help="Image prompt in English (recommended).")
    parser.add_argument("--aspect-ratio", default="1:1", choices=sorted(VALID_ASPECT_RATIOS))
    parser.add_argument("--resolution", default="1K", choices=sorted(VALID_RESOLUTIONS))
    parser.add_argument("--output-format", default="png", choices=sorted(VALID_FORMATS))
    parser.add_argument("--num-images", type=int, default=1)
    parser.add_argument("--web-search", action="store_true", help="Enable model web search.")
    parser.add_argument("--thinking", choices=["minimal", "high"], default=None)
    parser.add_argument("--output", required=True, help="Local path to save the first image.")
    args = parser.parse_args()

    try:
        result = generate(
            prompt=args.prompt,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_format=args.output_format,
            num_images=args.num_images,
            enable_web_search=args.web_search,
            thinking_level=args.thinking,
        )
    except FalError as e:
        print(f"[fal_image] error: {e}", file=sys.stderr)
        return 1

    images = result.get("images") or []
    if not images:
        print(f"[fal_image] no images returned: {result}", file=sys.stderr)
        return 1

    first = images[0]
    download(first["url"], Path(args.output))
    print(json.dumps({
        "saved_to": args.output,
        "width": first.get("width"),
        "height": first.get("height"),
        "content_type": first.get("content_type"),
        "model": MODEL_ID,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
