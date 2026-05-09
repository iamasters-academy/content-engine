#!/usr/bin/env python3
"""
image_engine.py — Selector de proveedor de imagen.

Punto de entrada único que lee `data/image_config.yaml` y delega al backend
correcto (Fal.ai o OpenAI). La skill solo llama a este módulo, nunca a los
clientes específicos directamente.

Uso (CLI):
    python tools/image_engine.py \
        --prompt "..." \
        --aspect-ratio 1:1 \
        --output _assets/imagen.png

Uso (Python):
    from tools import image_engine
    image_engine.generate(prompt=..., aspect_ratio="1:1", output=Path("img.png"))

Config esperada en data/image_config.yaml:

    provider: fal              # fal | openai
    model_id: nano-banana-2
    endpoint: fal-ai/nano-banana-2
    defaults:
      aspect_ratio: "1:1"
      resolution: "1K"
      output_format: "png"
    notes: ""
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Importes con fallback: el módulo puede llamarse como script o como import.
try:
    from . import fal_image, openai_image
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    import fal_image  # type: ignore
    import openai_image  # type: ignore


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "data" / "image_config.yaml"


class ImageEngineError(Exception):
    """Error en el selector de imagen."""


def _parse_simple_yaml(path: Path) -> dict:
    """Parser YAML mínimo (stdlib only). Soporta el subset que usa image_config.yaml.

    Suficiente para nuestro schema: claves planas + bloque `defaults:` con sub-claves.
    No soporta listas, anclas, multi-line strings.
    """
    if not path.exists():
        raise ImageEngineError(
            f"No existe {path}. Ejecuta la Fase 0.5 de la skill para crear "
            f"image_config.yaml, o crea el archivo manualmente desde el ejemplo "
            f"de docs/onboarding-flow.md."
        )

    config: dict = {}
    current_block: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            value = value.strip().strip('"').strip("'")
            if value == "":
                # Bloque anidado
                current_block = key.strip()
                config[current_block] = {}
            else:
                config[key.strip()] = value
                current_block = None
        elif raw_line.startswith(" ") and ":" in line and current_block is not None:
            sub_key, _, sub_value = line.strip().partition(":")
            sub_value = sub_value.strip().strip('"').strip("'")
            config[current_block][sub_key.strip()] = sub_value
    return config


def load_config(config_path: Path | None = None) -> dict:
    """Carga image_config.yaml. Si no existe, devuelve config default (Fal nano-banana-2)."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return {
            "provider": "fal",
            "model_id": "nano-banana-2",
            "endpoint": "fal-ai/nano-banana-2",
            "defaults": {
                "aspect_ratio": "1:1",
                "resolution": "1K",
                "output_format": "png",
            },
        }
    return _parse_simple_yaml(path)


def generate(
    *,
    prompt: str,
    output: Path,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    output_format: str | None = None,
    config: dict | None = None,
) -> dict:
    """Genera la imagen usando el backend definido en config.

    Args:
        prompt: prompt de la imagen (preferiblemente en inglés).
        output: ruta donde guardar la imagen.
        aspect_ratio: override (1:1, 9:16, 16:9...). Si None, usa config.defaults.
        resolution: solo aplica a Fal (0.5K, 1K, 2K, 4K).
        output_format: png, jpeg, webp.
        config: dict de config. Si None, se carga de image_config.yaml.

    Returns:
        dict con 'saved_to', 'provider', 'model'.
    """
    cfg = config or load_config()
    provider = (cfg.get("provider") or "fal").lower()
    defaults = cfg.get("defaults") or {}

    aspect_ratio = aspect_ratio or defaults.get("aspect_ratio") or "1:1"
    resolution = resolution or defaults.get("resolution") or "1K"
    output_format = output_format or defaults.get("output_format") or "png"

    output = Path(output)

    if provider == "fal":
        endpoint = cfg.get("endpoint") or f"fal-ai/{cfg.get('model_id', 'nano-banana-2')}"
        result = fal_image.generate(
            prompt=prompt,
            model_id=endpoint,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format=output_format,
        )
        images = result.get("images") or []
        if not images:
            raise ImageEngineError(f"Fal devolvió sin imágenes: {result}")
        fal_image.download(images[0]["url"], output)
        return {
            "saved_to": str(output),
            "provider": "fal",
            "model": endpoint,
        }

    if provider == "openai":
        size = openai_image.ASPECT_TO_SIZE.get(aspect_ratio, "1024x1024")
        response = openai_image.generate(
            prompt=prompt,
            size=size,
            output_format=output_format,
        )
        info = openai_image.save_first_image(response, output)
        info["provider"] = "openai"
        return info

    raise ImageEngineError(
        f"Provider desconocido: '{provider}'. Soportados: fal, openai."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera imagen usando el backend configurado.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--aspect-ratio", default=None)
    parser.add_argument("--resolution", default=None, help="Solo Fal (0.5K, 1K, 2K, 4K)")
    parser.add_argument("--output-format", default=None, choices=["png", "jpeg", "webp"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default=None, help="Ruta a image_config.yaml")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    try:
        cfg = load_config(config_path)
        info = generate(
            prompt=args.prompt,
            output=Path(args.output),
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_format=args.output_format,
            config=cfg,
        )
    except (ImageEngineError, fal_image.FalError, openai_image.OpenAIImageError) as e:
        print(f"[image_engine] error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
