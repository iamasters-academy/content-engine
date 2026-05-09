#!/usr/bin/env python3
"""
openai_image.py — Cliente OpenAI para gpt-image-1 (DALL-E 3 actualizado).

Uso:
    python tools/openai_image.py \
        --prompt "A professional minimalist scene of..." \
        --size 1024x1024 \
        --output _assets/imagen.png

Entorno:
    OPENAI_API_KEY — obligatoria. https://platform.openai.com/api-keys

Modelo: gpt-image-1
Doc:    https://platform.openai.com/docs/guides/image-generation
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

ENDPOINT = "https://api.openai.com/v1/images/generations"
DEFAULT_MODEL = "gpt-image-1"

# gpt-image-1 sizes (cubre los aspect ratios comunes)
VALID_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}
VALID_QUALITY = {"low", "medium", "high", "auto"}
VALID_FORMATS = {"png", "jpeg", "webp"}

# Mapeo aspect ratio → size de gpt-image-1
ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "9:16": "1024x1536",
    "16:9": "1536x1024",
    "2:3": "1024x1536",
    "3:2": "1536x1024",
}


class OpenAIImageError(Exception):
    """Error al generar imagen con OpenAI."""


def _post(url: str, headers: dict, body: dict, *, timeout_s: int = 180) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, method="POST", data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        raise OpenAIImageError(f"HTTP {e.code} — {err_body}") from e


def generate(
    *,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "auto",
    output_format: str = "png",
    n: int = 1,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict:
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIImageError(
            "OPENAI_API_KEY no está definida. Consíguela en https://platform.openai.com/api-keys"
        )

    if size not in VALID_SIZES:
        raise OpenAIImageError(f"Size inválido. Debe ser uno de: {sorted(VALID_SIZES)}")
    if quality not in VALID_QUALITY:
        raise OpenAIImageError(f"Quality inválido. Debe ser uno de: {sorted(VALID_QUALITY)}")
    if output_format not in VALID_FORMATS:
        raise OpenAIImageError(f"Format inválido. Debe ser uno de: {sorted(VALID_FORMATS)}")

    body = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": output_format,
        "n": n,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    return _post(ENDPOINT, headers, body)


def save_first_image(response: dict, output_path: Path) -> dict:
    """Guarda la primera imagen del response. gpt-image-1 devuelve b64_json."""
    images = response.get("data") or []
    if not images:
        raise OpenAIImageError(f"Sin imágenes en respuesta: {response}")

    first = images[0]
    b64 = first.get("b64_json")
    if not b64:
        # Fallback: si vino como URL (config "response_format: url")
        url = first.get("url")
        if not url:
            raise OpenAIImageError(f"Imagen sin b64_json ni url: {first}")
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read()
    else:
        data = base64.b64decode(b64)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(data)

    return {
        "saved_to": str(output_path),
        "size_bytes": len(data),
        "model": response.get("model", DEFAULT_MODEL),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera una imagen con OpenAI gpt-image-1.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--size", default="1024x1024", choices=sorted(VALID_SIZES))
    parser.add_argument("--aspect-ratio", default=None,
                        help="Atajo para mapear a size válido (1:1, 9:16, 16:9...)")
    parser.add_argument("--quality", default="auto", choices=sorted(VALID_QUALITY))
    parser.add_argument("--output-format", default="png", choices=sorted(VALID_FORMATS))
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    size = args.size
    if args.aspect_ratio:
        size = ASPECT_TO_SIZE.get(args.aspect_ratio, args.size)

    try:
        response = generate(
            prompt=args.prompt,
            size=size,
            quality=args.quality,
            output_format=args.output_format,
            n=args.n,
        )
        info = save_first_image(response, Path(args.output))
    except OpenAIImageError as e:
        print(f"[openai_image] error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
