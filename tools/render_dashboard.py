#!/usr/bin/env python3
"""
render_dashboard.py — Renderiza el dashboard.html final desde el template.

Lee:
- templates/dashboard.html.template (Mustache-lite syntax)
- data/inbox-redes/<YYYYMMDD>-<slug>/*.md (las 5 piezas)
- data/inbox-redes/<YYYYMMDD>-<slug>/imagen.png (si existe)
- data/inbox-redes/<YYYYMMDD>-<slug>/meta.json (metadatos: brand_slug, schedules, etc.)

Genera:
- data/inbox-redes/<YYYYMMDD>-<slug>/dashboard.html

Uso:
    python tools/render_dashboard.py --slug 20260510-pyme-26h
    python tools/render_dashboard.py --dir data/inbox-redes/20260510-pyme-26h

Sintaxis del template soportada (subset Mustache):
- {{var}}             — reemplazo simple
- {{nested.key}}      — acceso anidado
- {{#var}}...{{/var}} — bloque condicional (renderiza si var es truthy)

NO soporta: loops sobre arrays, partials, comentarios, escaping HTML
(la salida es trusted porque nosotros generamos el contenido).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "dashboard.html.template"
INBOX_DIR = REPO_ROOT / "data" / "inbox-redes"


class RenderError(Exception):
    """Error renderizando el dashboard."""


def _resolve_path(context: dict, path: str) -> str | None:
    """Resuelve clave anidada estilo 'linkedin.content'. None si no existe."""
    parts = path.strip().split(".")
    cur: object = context
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return None if cur is None else str(cur)


def _is_truthy(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    if isinstance(value, bool):
        return value
    return True


def render(template: str, context: dict) -> str:
    """Renderiza el template con el contexto."""
    # 1) Bloques condicionales {{#var}}...{{/var}}
    block_re = re.compile(r"\{\{#([\w\.]+)\}\}(.*?)\{\{/\1\}\}", re.DOTALL)

    def block_sub(m: re.Match[str]) -> str:
        key = m.group(1)
        inner = m.group(2)
        # Para bloques, comprobamos truthiness del contexto sin _resolve_path estrictamente.
        parts = key.split(".")
        cur: object = context
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                cur = None
                break
        if _is_truthy(cur):
            return render(inner, context)
        return ""

    # Aplicar bloques iterativamente hasta que no haya más
    prev = None
    cur = template
    while prev != cur:
        prev = cur
        cur = block_re.sub(block_sub, cur)

    # 2) Reemplazos simples {{var}} y {{nested.key}}
    var_re = re.compile(r"\{\{([\w\.]+)\}\}")

    def var_sub(m: re.Match[str]) -> str:
        key = m.group(1)
        value = _resolve_path(context, key)
        return value if value is not None else ""

    return var_re.sub(var_sub, cur)


def _read_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def build_context(out_dir: Path) -> dict:
    """Lee los outputs de la skill y construye el contexto para renderizar."""
    if not out_dir.exists():
        raise RenderError(f"No existe: {out_dir}")

    meta_path = out_dir / "meta.json"
    meta: dict = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    slug = meta.get("slug") or out_dir.name
    title = meta.get("title") or slug.replace("-", " ").title()
    brand_slug = meta.get("brand_slug") or "tu-marca"
    generated_at = meta.get("generated_at") or ""
    language = meta.get("language") or "es"

    image_meta = meta.get("image") or {}
    image_present = (out_dir / "imagen.png").exists() or bool(image_meta)

    def piece(channel: str) -> dict:
        """Carga el contenido de una pieza por canal. Devuelve dict con
        content, schedule, word_count, etc."""
        md = _read_text(out_dir / f"{channel}.md") or ""
        meta_for_channel = (meta.get("pieces") or {}).get(channel, {})
        return {
            "content": md,
            "schedule": meta_for_channel.get("schedule", ""),
            "word_count": meta_for_channel.get("word_count", str(len(md.split()))),
            "tweet_count": meta_for_channel.get("tweet_count", ""),
            "duration_s": meta_for_channel.get("duration_s", ""),
            "hashtags": meta_for_channel.get("hashtags", ""),
            "thread": meta_for_channel.get("thread", md),
            "script": meta_for_channel.get("script", md),
            "caption": meta_for_channel.get("caption", ""),
        }

    return {
        "title": title,
        "slug": slug,
        "brand_slug": brand_slug,
        "generated_at": generated_at,
        "language": language,
        "image": image_present,
        "image_model": image_meta.get("model", ""),
        "aspect_ratio": image_meta.get("aspect_ratio", ""),
        "resolution": image_meta.get("resolution", ""),
        "linkedin": piece("linkedin"),
        "instagram": piece("instagram"),
        "x": piece("x-thread"),
        "youtube": piece("youtube-short"),
        "tiktok": piece("tiktok"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Renderiza dashboard.html desde el template.")
    parser.add_argument("--slug", default=None, help="Slug del directorio (resuelto contra data/inbox-redes/).")
    parser.add_argument("--dir", default=None, help="Ruta absoluta o relativa al directorio de outputs.")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE),
                        help=f"Template a usar. Default: {DEFAULT_TEMPLATE}")
    parser.add_argument("--output", default=None, help="Ruta de salida. Default: <dir>/dashboard.html")
    args = parser.parse_args()

    if not args.slug and not args.dir:
        print("[render_dashboard] Necesito --slug o --dir", file=sys.stderr)
        return 1

    out_dir = Path(args.dir) if args.dir else INBOX_DIR / args.slug

    try:
        template = Path(args.template).read_text(encoding="utf-8")
        context = build_context(out_dir)
        rendered = render(template, context)
    except RenderError as e:
        print(f"[render_dashboard] {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"[render_dashboard] archivo no encontrado: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else (out_dir / "dashboard.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    print(json.dumps({
        "rendered": str(output_path),
        "size_bytes": output_path.stat().st_size,
        "slug": context["slug"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
