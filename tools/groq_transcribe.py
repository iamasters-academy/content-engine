#!/usr/bin/env python3
"""
groq_transcribe.py — Transcribe audio/video with Groq Whisper API.

Usage:
    python tools/groq_transcribe.py --file audio.mp3 --language es

Environment:
    GROQ_API_KEY — required. Get it at https://console.groq.com/keys

Model: whisper-large-v3-turbo (fast, multilingual, $0.04/h)
       whisper-large-v3 (more accurate, supports translation, $0.111/h)
Docs:  https://console.groq.com/docs/speech-text

File limits: 25 MB free tier, 100 MB dev tier.
Supported formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
import uuid
from pathlib import Path

ENDPOINT_TRANSCRIPTION = "https://api.groq.com/openai/v1/audio/transcriptions"
ENDPOINT_TRANSLATION = "https://api.groq.com/openai/v1/audio/translations"

VALID_MODELS = {"whisper-large-v3-turbo", "whisper-large-v3"}
VALID_RESPONSE_FORMATS = {"json", "verbose_json", "text"}

MAX_SIZE_FREE_TIER_MB = 25


class GroqError(Exception):
    """Raised when Groq API returns an error."""


def _build_multipart(fields: dict[str, str], file_path: Path) -> tuple[bytes, str]:
    """Build a multipart/form-data body using stdlib only.

    Returns (body, content_type).
    """
    boundary = f"----GroqBoundary{uuid.uuid4().hex}"
    lines: list[bytes] = []

    for key, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))

    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    lines.append(f"--{boundary}".encode())
    lines.append(
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"'.encode()
    )
    lines.append(f"Content-Type: {mime}".encode())
    lines.append(b"")
    lines.append(file_path.read_bytes())

    lines.append(f"--{boundary}--".encode())
    lines.append(b"")

    body = b"\r\n".join(lines)
    return body, f"multipart/form-data; boundary={boundary}"


def transcribe(
    file_path: Path,
    *,
    model: str = "whisper-large-v3-turbo",
    language: str | None = None,
    prompt: str | None = None,
    response_format: str = "json",
    temperature: float = 0.0,
    translate: bool = False,
    api_key: str | None = None,
) -> dict | str:
    """Send audio to Groq Whisper API and return the response.

    If translate=True, hits the /translations endpoint (requires whisper-large-v3).
    """
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise GroqError("GROQ_API_KEY env var not set. Get one at https://console.groq.com/keys")

    if not file_path.exists():
        raise GroqError(f"File not found: {file_path}")

    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_SIZE_FREE_TIER_MB:
        raise GroqError(
            f"File is {size_mb:.1f} MB. Free tier limit is {MAX_SIZE_FREE_TIER_MB} MB. "
            f"Upgrade to dev tier (100 MB) or chunk the audio. "
            f"See https://github.com/groq/groq-api-cookbook/tree/main/tutorials/audio-chunking"
        )

    if model not in VALID_MODELS:
        raise GroqError(f"Invalid model. Must be one of: {sorted(VALID_MODELS)}")

    if response_format not in VALID_RESPONSE_FORMATS:
        raise GroqError(f"Invalid response_format. Must be one of: {sorted(VALID_RESPONSE_FORMATS)}")

    if translate and model != "whisper-large-v3":
        raise GroqError("Translation requires model=whisper-large-v3")

    fields: dict[str, str] = {
        "model": model,
        "response_format": response_format,
        "temperature": str(temperature),
    }
    if language and not translate:
        fields["language"] = language
    if prompt:
        fields["prompt"] = prompt[:1500]  # Groq accepts max 224 tokens, ~1500 chars safe ceiling

    body, content_type = _build_multipart(fields, file_path)

    endpoint = ENDPOINT_TRANSLATION if translate else ENDPOINT_TRANSCRIPTION
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": content_type,
    }

    req = urllib.request.Request(endpoint, method="POST", data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        raise GroqError(f"HTTP {e.code} — {err_body}") from e

    if response_format == "text":
        return raw
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe audio with Groq Whisper API.")
    parser.add_argument("--file", required=True, help="Path to audio/video file.")
    parser.add_argument("--model", default="whisper-large-v3-turbo", choices=sorted(VALID_MODELS))
    parser.add_argument("--language", default=None, help="ISO-639-1 code (es, en, fr…).")
    parser.add_argument("--prompt", default=None, help="Style/context hint.")
    parser.add_argument("--response-format", default="json", choices=sorted(VALID_RESPONSE_FORMATS))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--translate", action="store_true", help="Translate to English (uses /translations).")
    parser.add_argument("--output", default=None, help="Optional path to save the transcription.")
    args = parser.parse_args()

    try:
        result = transcribe(
            file_path=Path(args.file),
            model=args.model,
            language=args.language,
            prompt=args.prompt,
            response_format=args.response_format,
            temperature=args.temperature,
            translate=args.translate,
        )
    except GroqError as e:
        print(f"[groq_transcribe] error: {e}", file=sys.stderr)
        return 1

    if isinstance(result, dict):
        text = result.get("text", "")
        output_payload = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        text = result
        output_payload = result

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_payload, encoding="utf-8")
        print(json.dumps({"saved_to": args.output, "chars": len(text), "model": args.model}, indent=2))
    else:
        print(output_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
