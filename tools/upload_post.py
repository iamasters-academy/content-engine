#!/usr/bin/env python3
"""
upload_post.py — Cliente Upload-Post API.

Publica una foto en LinkedIn / Instagram / X / TikTok / Facebook / Threads / etc.

Uso:
    python tools/upload_post.py \
        --user mi-usuario-upload-post \
        --image _assets/imagen.png \
        --title "Título del post / caption por defecto" \
        --description "Texto extendido opcional" \
        --platforms linkedin,instagram

Entorno:
    UPLOAD_POST_API_KEY — obligatoria. https://upload-post.com

Endpoints (verificados contra docs.upload-post.com):
    POST  https://api.upload-post.com/api/upload_photos
    GET   https://api.upload-post.com/api/uploadposts/status?request_id=...

Header de autenticación: Authorization: Apikey YOUR_KEY
Content-Type: multipart/form-data

Campos obligatorios: user, platform[], photos[]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import uuid
from pathlib import Path

API_BASE = "https://api.upload-post.com/api"
ENDPOINT_PHOTOS = f"{API_BASE}/upload_photos"
ENDPOINT_VIDEO = f"{API_BASE}/upload"
ENDPOINT_STATUS = f"{API_BASE}/uploadposts/status"

# Plataformas soportadas por Upload-Post (verificado en docs).
VALID_PLATFORMS = {
    "tiktok", "instagram", "linkedin", "facebook", "x",
    "threads", "pinterest", "bluesky", "reddit", "google_business",
}


class UploadPostError(Exception):
    """Error al llamar a Upload-Post."""


def _build_multipart(fields: list[tuple[str, str]], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    """Construye multipart/form-data con stdlib.

    fields: lista de (nombre, valor) — permite repetir nombres (ej. platform[]).
    files: lista de (nombre_campo, ruta) — para photos[].
    """
    boundary = f"----UploadPostBoundary{uuid.uuid4().hex}"
    lines: list[bytes] = []

    for key, value in fields:
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))

    for key, file_path in files:
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        lines.append(f"--{boundary}".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{file_path.name}"'.encode()
        )
        lines.append(f"Content-Type: {mime}".encode())
        lines.append(b"")
        lines.append(file_path.read_bytes())

    lines.append(f"--{boundary}--".encode())
    lines.append(b"")
    return b"\r\n".join(lines), f"multipart/form-data; boundary={boundary}"


def _http(method: str, url: str, *, headers: dict, body: bytes | None = None, timeout_s: int = 120) -> dict:
    req = urllib.request.Request(url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
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
    user: str,
    image_path: Path,
    title: str,
    platforms: list[str],
    description: str | None = None,
    request_id: str | None = None,
    async_upload: bool = False,
    facebook_page_id: str | None = None,
    target_linkedin_page_id: str | None = None,
    linkedin_visibility: str = "PUBLIC",
    extra_fields: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """Publica una foto en una o varias plataformas.

    Args:
        user: identificador de usuario en Upload-Post (obligatorio).
        image_path: ruta a la imagen.
        title: caption por defecto (visible en todas las plataformas salvo override).
        platforms: lista de plataformas (ver VALID_PLATFORMS).
        description: texto extendido opcional.
        request_id: identificador de tracking. Si None se genera uuid.
        async_upload: si True, procesa en background.
        facebook_page_id: obligatorio si publicas en Facebook.
        target_linkedin_page_id: opcional para publicar en página de empresa LI.
        linkedin_visibility: PUBLIC | CONNECTIONS.
        extra_fields: dict con cualquier campo adicional (overrides por canal, etc.).
        api_key: si None, lee UPLOAD_POST_API_KEY del entorno.

    Returns:
        dict con la respuesta JSON de Upload-Post (request_id, job_id, success, etc.).
    """
    api_key = api_key or os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        raise UploadPostError(
            "UPLOAD_POST_API_KEY no está definida. Consíguela en https://upload-post.com"
        )

    if not user:
        raise UploadPostError("El campo 'user' es obligatorio. Es tu identificador en Upload-Post.")
    if not image_path.exists():
        raise UploadPostError(f"Imagen no encontrada: {image_path}")

    bad = [p for p in platforms if p not in VALID_PLATFORMS]
    if bad:
        raise UploadPostError(
            f"Plataforma(s) inválidas: {bad}. Soportadas: {sorted(VALID_PLATFORMS)}"
        )

    if "facebook" in platforms and not facebook_page_id:
        raise UploadPostError("Facebook requiere facebook_page_id.")

    request_id = request_id or f"content-engine-{uuid.uuid4().hex[:12]}"

    # Campos obligatorios + opcionales.
    fields: list[tuple[str, str]] = [
        ("user", user),
        ("title", title),
        ("request_id", request_id),
        ("async_upload", "true" if async_upload else "false"),
    ]
    if description:
        fields.append(("description", description))
    if facebook_page_id:
        fields.append(("facebook_page_id", facebook_page_id))
    if target_linkedin_page_id:
        fields.append(("target_linkedin_page_id", target_linkedin_page_id))
    if linkedin_visibility:
        fields.append(("visibility", linkedin_visibility))
    if extra_fields:
        for k, v in extra_fields.items():
            fields.append((k, str(v)))

    # platform[] se repite una vez por plataforma.
    for p in platforms:
        fields.append(("platform[]", p))

    files = [("photos[]", image_path)]

    body, content_type = _build_multipart(fields, files)
    headers = {
        "Authorization": f"Apikey {api_key}",
        "Content-Type": content_type,
    }
    return _http("POST", ENDPOINT_PHOTOS, headers=headers, body=body)


def get_status(*, request_id: str | None = None, job_id: str | None = None, api_key: str | None = None) -> dict:
    """Consulta el estado de un upload."""
    api_key = api_key or os.environ.get("UPLOAD_POST_API_KEY")
    if not api_key:
        raise UploadPostError("UPLOAD_POST_API_KEY no está definida.")
    if not request_id and not job_id:
        raise UploadPostError("Se requiere request_id o job_id.")

    params = {}
    if request_id:
        params["request_id"] = request_id
    if job_id:
        params["job_id"] = job_id
    query = urllib.parse.urlencode(params)
    url = f"{ENDPOINT_STATUS}?{query}"
    headers = {"Authorization": f"Apikey {api_key}"}
    return _http("GET", url, headers=headers)


def wait_until_published(
    *,
    request_id: str,
    timeout_s: int = 90,
    poll_s: float = 2.0,
    api_key: str | None = None,
) -> dict:
    """Polea status hasta publicación o timeout."""
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        last = get_status(request_id=request_id, api_key=api_key)
        # Estado puede venir bajo distintas claves según versión del API.
        status = (last.get("status") or last.get("state") or "").lower()
        success = last.get("success")
        if status in {"published", "completed", "success"} or success is True:
            return last
        if status in {"failed", "error", "rejected"} or success is False:
            raise UploadPostError(f"Job {request_id} falló: {last}")
        time.sleep(poll_s)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="Publica una foto via Upload-Post API.")
    parser.add_argument("--user", required=True, help="Identificador de usuario en Upload-Post.")
    parser.add_argument("--image", required=True, help="Ruta a la imagen.")
    parser.add_argument("--title", required=True, help="Caption / título del post (default).")
    parser.add_argument("--description", default=None, help="Texto extendido opcional.")
    parser.add_argument(
        "--platforms",
        required=True,
        help=f"Plataformas separadas por coma. Soportadas: {sorted(VALID_PLATFORMS)}",
    )
    parser.add_argument("--facebook-page-id", default=None)
    parser.add_argument("--linkedin-page-id", default=None)
    parser.add_argument("--linkedin-visibility", default="PUBLIC")
    parser.add_argument("--async-upload", action="store_true",
                        help="Procesa en background. Si la subida tarda >59s pasa a async automáticamente.")
    parser.add_argument("--wait", action="store_true", help="Polea hasta que el post esté publicado.")
    args = parser.parse_args()

    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    try:
        result = publish_photo(
            user=args.user,
            image_path=Path(args.image),
            title=args.title,
            description=args.description,
            platforms=platforms,
            facebook_page_id=args.facebook_page_id,
            target_linkedin_page_id=args.linkedin_page_id,
            linkedin_visibility=args.linkedin_visibility,
            async_upload=args.async_upload,
        )
        if args.wait:
            req_id = result.get("request_id")
            if req_id:
                result = wait_until_published(request_id=req_id)
    except UploadPostError as e:
        print(f"[upload_post] error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
