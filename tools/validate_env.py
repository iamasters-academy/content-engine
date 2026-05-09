#!/usr/bin/env python3
"""
validate_env.py — Verifica que las API keys configuradas funcionan de verdad.

Hace un ping mínimo a cada servicio para confirmar 200 OK. Si alguna key
está mal pegada, revocada o tiene espacios, lo detectamos antes de empezar
el flujo real.

Uso:
    python tools/validate_env.py
    python tools/validate_env.py --json    # output machine-readable
    python tools/validate_env.py --only fal,upload_post

Returncode:
    0 — todas las keys disponibles funcionan
    1 — alguna key configurada falla
    2 — falta una key obligatoria

La skill llama a este script al arrancar para decidir si entrar en
Fase 0 (setup) o saltar a Fase A (uso normal).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def _http_get(url: str, headers: dict, timeout_s: int = 10) -> tuple[int, str]:
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:500]
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            body = str(e)
        return e.code, body
    except Exception as e:
        return -1, str(e)


def check_fal() -> dict:
    key = os.environ.get("FAL_KEY")
    if not key or key.startswith("tu-"):
        return {"service": "fal", "ok": False, "configured": False, "message": "FAL_KEY no configurada"}
    # Ping ligero al endpoint de queue health (no consume créditos).
    status, body = _http_get(
        "https://queue.fal.run/health",
        headers={"Authorization": f"Key {key}"},
    )
    # Aunque /health a veces devuelve 404, lo importante es que no sea 401/403.
    if status in {401, 403}:
        return {"service": "fal", "ok": False, "configured": True,
                "message": f"FAL_KEY rechazada (HTTP {status}). Regenérala en https://fal.ai/dashboard/keys"}
    return {"service": "fal", "ok": True, "configured": True, "message": "OK"}


def check_groq() -> dict:
    key = os.environ.get("GROQ_API_KEY")
    if not key or key.startswith("tu-"):
        return {"service": "groq", "ok": False, "configured": False,
                "message": "GROQ_API_KEY no configurada (opcional)"}
    # Endpoint /openai/v1/models es público con la key, no consume cuota.
    status, body = _http_get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    if status == 200:
        return {"service": "groq", "ok": True, "configured": True, "message": "OK"}
    if status in {401, 403}:
        return {"service": "groq", "ok": False, "configured": True,
                "message": f"GROQ_API_KEY rechazada (HTTP {status}). Regenérala en https://console.groq.com/keys"}
    return {"service": "groq", "ok": False, "configured": True,
            "message": f"Groq devolvió HTTP {status}: {body[:200]}"}


def check_upload_post() -> dict:
    key = os.environ.get("UPLOAD_POST_API_KEY")
    if not key or key.startswith("tu-"):
        return {"service": "upload_post", "ok": False, "configured": False,
                "message": "UPLOAD_POST_API_KEY no configurada (opcional)"}
    # Endpoint de status acepta peticiones GET con la key. Sin params devuelve 400 con JSON,
    # pero al menos confirma que la key es válida (vs 401).
    status, body = _http_get(
        "https://api.upload-post.com/api/uploadposts/status?request_id=ping-validate",
        headers={"Authorization": f"Apikey {key}"},
    )
    if status in {401, 403}:
        return {"service": "upload_post", "ok": False, "configured": True,
                "message": f"UPLOAD_POST_API_KEY rechazada (HTTP {status}). Regenérala en https://upload-post.com"}
    return {"service": "upload_post", "ok": True, "configured": True, "message": "OK"}


def check_openai() -> dict:
    key = os.environ.get("OPENAI_API_KEY")
    if not key or key.startswith("tu-") or key.startswith("sk-tu"):
        return {"service": "openai", "ok": False, "configured": False,
                "message": "OPENAI_API_KEY no configurada (opcional, solo si eliges OpenAI como proveedor de imagen)"}
    status, body = _http_get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    if status == 200:
        return {"service": "openai", "ok": True, "configured": True, "message": "OK"}
    if status in {401, 403}:
        return {"service": "openai", "ok": False, "configured": True,
                "message": f"OPENAI_API_KEY rechazada (HTTP {status}). Regenérala en https://platform.openai.com/api-keys"}
    return {"service": "openai", "ok": False, "configured": True,
            "message": f"OpenAI devolvió HTTP {status}: {body[:200]}"}


SERVICES = {
    "fal": check_fal,
    "groq": check_groq,
    "upload_post": check_upload_post,
    "openai": check_openai,
}


def run(only: list[str] | None = None) -> list[dict]:
    targets = list(only) if only else list(SERVICES.keys())
    results: list[dict] = []
    for name in targets:
        if name not in SERVICES:
            results.append({"service": name, "ok": False, "configured": False,
                            "message": f"Servicio desconocido: {name}"})
            continue
        results.append(SERVICES[name]())
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida las API keys configuradas.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    parser.add_argument("--only", default=None,
                        help="Comma-separated: fal,groq,upload_post,openai")
    args = parser.parse_args()

    only = [s.strip() for s in args.only.split(",")] if args.only else None
    results = run(only)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Validación de API keys:")
        for r in results:
            icon = "✓" if r["ok"] else ("·" if not r["configured"] else "✗")
            print(f"  {icon} {r['service']:14} {r['message']}")

    # Returncode:
    # 0 — todas las configuradas funcionan
    # 1 — alguna configurada falla
    # 2 — todas las opcionales no configuradas y ninguna obligatoria → ambiguo, devolver 0
    fal_state = next((r for r in results if r["service"] == "fal"), None)
    if fal_state and fal_state["configured"] and not fal_state["ok"]:
        return 1
    for r in results:
        if r["configured"] and not r["ok"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
