#!/usr/bin/env python3
"""
fal_image.py — Cliente Fal.ai genérico (cualquier modelo).

Por defecto usa nano-banana-2 (Google). Se puede sobrescribir con --model.

Uso:
    python tools/fal_image.py \
        --prompt "A professional woman at desk, split-screen..." \
        --aspect-ratio 1:1 \
        --resolution 1K \
        --output _assets/imagen.png

    # Otro modelo (ej. flux-pro):
    python tools/fal_image.py \
        --model fal-ai/flux-pro/v1.1-ultra \
        --prompt "..." \
        --output _assets/imagen.png

Entorno:
    FAL_KEY — obligatoria. https://fal.ai/dashboard/keys

Modelo default: fal-ai/nano-banana-2
Doc:           https://fal.ai/models/fal-ai/nano-banana-2/api
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://queue.fal.run"
DEFAULT_MODEL = "fal-ai/nano-banana-2"
DEFAULT_EDIT_MODEL = "fal-ai/nano-banana-2/edit"

# Aspect ratios soportados por nano-banana-2 (otros modelos pueden tener subset).
COMMON_ASPECT_RATIOS = {
    "auto", "21:9", "16:9", "3:2", "4:3", "5:4", "1:1",
    "4:5", "3:4", "2:3", "9:16", "4:1", "1:4", "8:1", "1:8",
}


class FalError(Exception):
    """Error al llamar a Fal.ai."""


def _request(method: str, url: str, *, headers: dict, body: dict | None = None) -> dict:
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


def submit(api_key: str, model_id: str, payload: dict) -> str:
    url = f"{API_BASE}/{model_id}"
    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json",
    }
    result = _request("POST", url, headers=headers, body=payload)
    request_id = result.get("request_id")
    if not request_id:
        raise FalError(f"Respuesta sin request_id: {result}")
    return request_id


def poll(api_key: str, model_id: str, request_id: str, *, timeout_s: int = 120, poll_interval_s: float = 1.5) -> dict:
    status_url = f"{API_BASE}/{model_id}/requests/{request_id}/status"
    result_url = f"{API_BASE}/{model_id}/requests/{request_id}"
    headers = {"Authorization": f"Key {api_key}"}

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = _request("GET", status_url, headers=headers)
        if status.get("status") == "COMPLETED":
            return _request("GET", result_url, headers=headers)
        if status.get("status") in {"FAILED", "CANCELLED"}:
            raise FalError(f"Request {request_id} acabó con status {status}")
        time.sleep(poll_interval_s)
    raise FalError(f"Request {request_id} timeout tras {timeout_s}s")


def download(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as resp, open(output_path, "wb") as f:
        f.write(resp.read())


def file_to_data_uri(path: Path) -> str:
    """Convierte un archivo local a Data URI base64 (para Fal image_urls).

    Fal acepta tanto URLs públicas como Data URIs. Esto evita tener que
    subir el archivo a un servicio externo.
    """
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def generate(
    *,
    prompt: str,
    model_id: str = DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
    resolution: str | None = "2K",
    output_format: str | None = "png",
    num_images: int = 1,
    extra_params: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """Submit + poll. Devuelve el resultado (sin descargar).

    extra_params permite pasar parámetros específicos del modelo (p.ej.
    enable_web_search para nano-banana-2, image_size para otros, etc.).
    """
    api_key = api_key or os.environ.get("FAL_KEY")
    if not api_key:
        raise FalError("FAL_KEY no está definida. Consíguela en https://fal.ai/dashboard/keys")

    payload: dict = {
        "prompt": prompt,
        "num_images": num_images,
    }
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution
    if output_format:
        payload["output_format"] = output_format
    if extra_params:
        payload.update(extra_params)

    request_id = submit(api_key, model_id, payload)
    return poll(api_key, model_id, request_id)


def edit(
    *,
    prompt: str,
    image_paths: list[Path],
    model_id: str = DEFAULT_EDIT_MODEL,
    aspect_ratio: str | None = None,
    resolution: str | None = "2K",
    output_format: str | None = "png",
    num_images: int = 1,
    extra_params: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """Edita una o varias imágenes de referencia con nano-banana-2/edit.

    Útil para:
    - Pasar una foto del usuario y pedir "ponme a mí en este escenario"
    - Pasar un logo y mantener consistencia visual
    - Hacer variantes de una imagen base

    Las imágenes se convierten a Data URI base64 internamente, no hay
    que subirlas a ningún servicio externo.
    """
    api_key = api_key or os.environ.get("FAL_KEY")
    if not api_key:
        raise FalError("FAL_KEY no está definida.")
    if not image_paths:
        raise FalError("Necesito al menos una imagen de referencia.")

    image_urls: list[str] = []
    for p in image_paths:
        if not p.exists():
            raise FalError(f"Imagen de referencia no encontrada: {p}")
        image_urls.append(file_to_data_uri(p))

    payload: dict = {
        "prompt": prompt,
        "image_urls": image_urls,
        "num_images": num_images,
    }
    if aspect_ratio:
        payload["aspect_ratio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution
    if output_format:
        payload["output_format"] = output_format
    if extra_params:
        payload.update(extra_params)

    request_id = submit(api_key, model_id, payload)
    return poll(api_key, model_id, request_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera o edita una imagen con cualquier modelo de Fal.ai.")
    parser.add_argument("--prompt", required=True, help="Prompt de la imagen (recomendado en inglés).")
    parser.add_argument("--model", default=None,
                        help=f"ID del modelo Fal (default: {DEFAULT_MODEL} en generate, "
                             f"{DEFAULT_EDIT_MODEL} con --edit-from)")
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--resolution", default="2K", help="0.5K, 1K, 2K, 4K — depende del modelo")
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
    parser.add_argument("--num-images", type=int, default=1)
    parser.add_argument("--web-search", action="store_true",
                        help="Activa búsqueda web del modelo (nano-banana-2 only).")
    parser.add_argument("--thinking", choices=["minimal", "high"], default=None,
                        help="thinking_level (nano-banana-2 only)")
    parser.add_argument("--edit-from", action="append", default=[], metavar="PATH",
                        help="Modo edit: pasa imagen(es) de referencia. Repetible para múltiples.")
    parser.add_argument("--output", required=True, help="Ruta local para guardar la primera imagen.")
    parser.add_argument("--extra-params", default=None,
                        help="JSON string con parámetros extra del modelo")
    args = parser.parse_args()

    extra: dict = {}
    if args.web_search:
        extra["enable_web_search"] = True
    if args.thinking:
        extra["thinking_level"] = args.thinking
    if args.extra_params:
        try:
            extra.update(json.loads(args.extra_params))
        except json.JSONDecodeError as e:
            print(f"[fal_image] --extra-params no es JSON válido: {e}", file=sys.stderr)
            return 1

    try:
        if args.edit_from:
            # Modo edición — pasa imágenes de referencia
            model = args.model or DEFAULT_EDIT_MODEL
            result = edit(
                prompt=args.prompt,
                image_paths=[Path(p) for p in args.edit_from],
                model_id=model,
                aspect_ratio=args.aspect_ratio if args.aspect_ratio != "1:1" else None,
                resolution=args.resolution,
                output_format=args.output_format,
                num_images=args.num_images,
                extra_params=extra or None,
            )
        else:
            # Modo generación normal
            model = args.model or DEFAULT_MODEL
            result = generate(
                prompt=args.prompt,
                model_id=model,
                aspect_ratio=args.aspect_ratio,
                resolution=args.resolution,
                output_format=args.output_format,
                num_images=args.num_images,
                extra_params=extra or None,
            )
    except FalError as e:
        print(f"[fal_image] error: {e}", file=sys.stderr)
        return 1

    images = result.get("images") or []
    if not images:
        print(f"[fal_image] sin imágenes en respuesta: {result}", file=sys.stderr)
        return 1

    first = images[0]
    download(first["url"], Path(args.output))
    print(json.dumps({
        "saved_to": args.output,
        "width": first.get("width"),
        "height": first.get("height"),
        "content_type": first.get("content_type"),
        "model": model,
        "mode": "edit" if args.edit_from else "generate",
        "image_url": first.get("url"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
