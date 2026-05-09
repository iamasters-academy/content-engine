# content-engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made by IA Masters Academy](https://img.shields.io/badge/made%20by-IA%20Masters%20Academy-3FB8C9)](https://iamastersacademy.com)
[![Skill for Claude Code](https://img.shields.io/badge/skill%20for-Claude%20Code-E85A2C)](https://docs.claude.com/en/docs/claude-code)
[![Idioma: español](https://img.shields.io/badge/idioma-espa%C3%B1ol-7FCC3F)]()

> **Skill agéntica para Claude Code que convierte cualquier input en 5 piezas adaptadas para redes sociales, genera la imagen con el modelo que elijas (nano-banana-2 de Google, Flux, OpenAI, o cualquier otro de Fal.ai vía URL) y publica en LinkedIn + Instagram. Todo hablando con tu agente. Cero nodos de n8n.**

---

## Lo que hace

Le pasas cualquiera de estos:
- Una idea suelta
- Texto largo o un artículo
- Un archivo de audio (cualquier formato)
- Un vídeo
- Una URL (YouTube, Instagram, podcast, blog)
- Un PDF

Y la skill hace esto:

1. Si es tu primera vez, **te guía paso a paso** para configurar tus cuentas (Fal, Groq, Upload-Post). Cero docs externas.
2. Te pregunta qué modelo de imagen quieres usar (default: `nano-banana-2`).
3. Construye tu brief de marca personal con 8-10 preguntas (una sola vez, se guarda en YAML).
4. Procesa el input (transcribe si es audio/vídeo, fetcha si es URL).
5. Investiga lo que está funcionando en 2026 en cada red.
6. Genera 5 piezas adaptadas (LinkedIn / X / Instagram / YouTube short / TikTok).
7. Te pregunta sobre el visual (1 imagen / carrusel / reel · ratio · si sales tú · ruta pro o gratis).
8. Si es ruta pro, **genera la imagen agénticamente** con el modelo configurado.
9. Publica en LinkedIn + Instagram con Upload-Post API.
10. Genera un dashboard HTML para pasar al community manager.

---

## Por qué existe

La mayoría de workflows de contenido viven en n8n: 25 nodos, el mismo texto en todas las redes, y un paso de imagen externo que rompe el flujo. Esta skill reemplaza el workflow completo con una conversación. Le hablas. Piensa. Publica.

Construida como implementación de referencia para la masterclass dominical del 10 de mayo de 2026 de [IA Masters Academy](https://iamastersacademy.com), última clase abierta antes de la apertura de la comunidad el 17 de mayo.

---

## Quickstart en 30 segundos

```bash
# 1. Clona en tu carpeta de skills
git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine

# 2. Abre Claude Code en cualquier carpeta
claude
```

Dentro de Claude Code:

```
/content-engine
```

**La skill te lleva de la mano desde aquí.** Si no tienes nada configurado, te guía a crear las cuentas necesarias y meter las API keys. No tienes que abrir ninguna documentación externa.

> 💡 **¿Usas Claude Cowork?** Mismo flujo. Después del primer onboarding puedes anclar la skill al panel lateral.

---

## Modelos de imagen soportados

La skill funciona con cualquiera de estos:

| Proveedor | Modelo | Cuándo usarlo |
|---|---|---|
| Fal.ai | `nano-banana-2` (Google) | **Default**. Rápido, multilingüe, state-of-the-art |
| Fal.ai | `flux-pro/v1.1-ultra` | Máxima calidad fotorealista |
| Fal.ai | `flux/dev` | Más rápido y barato |
| Fal.ai | **Cualquier otro modelo** | Le pasas la URL y la skill lo conecta sola |
| OpenAI | `gpt-image-1` | DALL-E 3 actualizado, requiere `OPENAI_API_KEY` |

¿Sale un modelo nuevo mañana? Le dices a la skill: "usa este modelo: <URL>". La skill lee la doc y se conecta. **Sin actualizaciones manuales del repo.**

---

## Requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) o [Claude Cowork](https://claude.com/cowork) instalados.
- Python 3.9+ (la skill usa solo stdlib — cero dependencias `pip`).
- Las API keys, que la skill te ayuda a conseguir en el primer arranque:
  - [Fal.ai](https://fal.ai) (gratis para empezar, pago por imagen)
  - [Groq](https://console.groq.com) (free tier abundante, solo si vas a usar audio/vídeo)
  - [Upload-Post](https://upload-post.com) (Free: 10 publicaciones/mes, solo si quieres publicar)
  - [OpenAI](https://platform.openai.com) (opcional, solo si eliges OpenAI como proveedor de imagen)

---

## Arquitectura

```
content-engine/
├── SKILL.md                    # Instrucciones agénticas (las lee Claude)
├── tools/
│   ├── image_engine.py         # Selector — único punto de entrada para imagen
│   ├── fal_image.py            # Cliente Fal.ai (cualquier modelo)
│   ├── openai_image.py         # Cliente OpenAI gpt-image-1
│   ├── groq_transcribe.py      # Cliente Groq Whisper
│   └── upload_post.py          # Cliente Upload-Post
├── templates/
│   ├── brief.yaml.template     # Schema del brief de marca
│   ├── linkedin.md             # Reglas para post LinkedIn
│   ├── instagram.md            # Reglas para caption Instagram
│   ├── x-thread.md             # Reglas para hilo X
│   ├── youtube-short.md        # Reglas para guion YouTube short
│   ├── tiktok.md               # Reglas para guion TikTok
│   └── dashboard.html.template # Dashboard final (paleta IA Masters)
├── data/
│   ├── briefs/                 # Tus briefs de marca (gitignored)
│   ├── image_config.yaml       # Modelo de imagen elegido (gitignored)
│   └── inbox-redes/            # Outputs por fecha (gitignored)
├── docs/
│   ├── onboarding-flow.md      # Qué pasa en el primer arranque
│   ├── installation.md         # Setup manual (alternativa al wizard)
│   ├── quickstart.md           # Tu primer post en 10 min
│   └── examples.md             # Casos de uso reales
└── .env.example                # Plantilla de claves (copia a .env.local)
```

---

## Uso manual de los tools (avanzado)

Cada tool es un script Python independiente, llamable directamente:

```bash
# Generar imagen (usa el modelo configurado en image_config.yaml)
python ~/.claude/skills/content-engine/tools/image_engine.py \
    --prompt "A minimalist scene of a person at a clean desk..." \
    --aspect-ratio 1:1 \
    --output _assets/imagen.png

# Forzar un modelo Fal específico
python ~/.claude/skills/content-engine/tools/fal_image.py \
    --model fal-ai/recraft-v3 \
    --prompt "..." \
    --aspect-ratio 1:1 \
    --output _assets/imagen.png

# Transcribir audio
python ~/.claude/skills/content-engine/tools/groq_transcribe.py \
    --file mi-audio.mp3 --language es

# Publicar
python ~/.claude/skills/content-engine/tools/upload_post.py \
    --image _assets/imagen.png \
    --caption "..." \
    --platforms linkedin,instagram \
    --wait
```

---

## Coste real

- **Fal.ai (`nano-banana-2`)**: pago por imagen, ver [precios](https://fal.ai/models/fal-ai/nano-banana-2/api).
- **Groq Whisper**: free tier cubre uso personal con holgura.
- **Upload-Post**: free tier = 10 publicaciones/mes.
- **OpenAI** (opcional): pago por imagen.

Para uso típico (1-2 posts/semana), espera **menos de 5 €/mes en total**.

---

## Lo que la skill NO hace (y por qué)

- ❌ NO publica solo a las 9:00 sin tu Mac encendido. Necesitas que Claude Code esté corriendo.
- ❌ NO sustituye a tu community manager — produce el material listo para handoff.
- ❌ NO conecta directo a LinkedIn ni Instagram. Upload-Post es el agregador certificado.
- ❌ NO inventa estadísticas ni citas. Cita fuentes cuando las usa.
- ❌ NO hace cross-posting del mismo texto. Adapta por canal por diseño.

---

## Contribuir

Esta es una implementación de referencia. Forks bienvenidos. PRs bienvenidas si mantienen la skill en su misma línea: agéntica, conversacional, cero dependencias donde sea posible.

---

## Licencia

MIT. Ver [LICENSE](LICENSE).

---

## Citación

Si construyes encima de esto, cítalo via [CITATION.cff](CITATION.cff).

---

<sub>Construida por [Angel Aparicio](https://www.linkedin.com/in/angel-aparicio92) · [IA Masters Academy](https://iamastersacademy.com) · [AASC Associates](https://github.com/iamasters-academy) · `aaparicio@iamastersacademy.com`</sub>
