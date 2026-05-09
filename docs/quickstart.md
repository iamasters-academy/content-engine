# Quickstart — tu primer post en 10 minutos

> Asume que ya has clonado el repo. Si no, hazlo:
> ```bash
> git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine
> ```

---

## 1. Abre Claude Code en cualquier proyecto

```bash
cd ~/cualquier-carpeta
claude
```

> ¿Usas Claude Cowork? Igual: abre Cowork, ya tienes la skill disponible.

## 2. Lanza la skill

```
/content-engine
```

## 3. Primer arranque — onboarding (~20 min, solo la primera vez)

La skill detecta que es tu primera vez y arranca el wizard. Te lleva por:

- **Fase 0** — Crear las 3 cuentas necesarias (Fal, Groq, Upload-Post). Te dice exactamente qué hacer en cada una.
- **Fase 0.5** — Elegir tu modelo de imagen (default: `nano-banana-2`).
- **Fase A** — Construir tu brief de marca con 8-10 preguntas.

Detalle completo del wizard: [onboarding-flow.md](onboarding-flow.md).

## 4. Pásale tu input

Cualquiera de estos:

```
"Hazme contenido para LinkedIn e Instagram con esta idea:
Hoy un cliente de 18 personas facturaba 200 facturas al mes a mano,
8 minutos cada una, 26 horas mensuales. Lo automatizamos con IA: 30
segundos por factura, cero errores."
```

O un archivo:

```
"Transcribe este audio y conviértelo en contenido: ./grabacion-mañana.m4a"
```

O una URL:

```
"Lee este artículo y saca el insight clave para contenido:
https://ejemplo.com/articulo-que-me-gusto"
```

## 5. Revisa las 5 piezas

La skill genera LinkedIn / X / Instagram / YouTube short / TikTok y te las muestra todas. Edita la que quieras:

> "Acorta el post de LinkedIn un 30% y quita la tercera lección"

## 6. Decide el visual

La skill pregunta:

- ¿1 imagen, carrusel de 3 o guion de reel?
- ¿Aspect ratio? (1:1 IG, 9:16 reels, 16:9 LinkedIn cover)
- ¿Sales tú en la imagen?
- ¿Pro (skill genera con tu modelo configurado) o gratis (te da el prompt para ChatGPT)?

Si eliges Pro, la skill llama a tu modelo (Fal, OpenAI o el que configuraste), espera ~10 segundos y te enseña la imagen.

## 7. Publica

La skill pregunta en qué redes (checkboxes). Llama a Upload-Post API y te devuelve las URLs reales de los posts publicados.

## 8. Todo en el chat

La skill te muestra todo en el propio chat: la imagen renderizada, el prompt en inglés (por si quieres refinarlo en otra herramienta), las 5 piezas separadas por canal, las URLs reales de los posts publicados.

Si tu community manager prefiere un HTML con tabs y copy-to-clipboard para programar desde Buffer/Metricool, **pídeselo a la skill**: `"genérame también el dashboard HTML para mi CM"`. Es opcional, no por defecto.

---

## Posts siguientes (después del primer arranque)

Sin onboarding. Solo:

```
/content-engine
"Convierte esto en contenido: <tu input>"
```

Tiempo medio: **2-3 minutos por post**.

---

## Qué viene después

- Mira [examples.md](examples.md) para casos reales.
- Ajusta tu brief cuando quieras editando `data/briefs/<slug>.yaml` directamente.
- Cambia de modelo de imagen editando `data/image_config.yaml` directamente o pidiéndoselo a la skill: "cambia el modelo de imagen a flux-pro/v1.1-ultra".
- Comparte la skill: es MIT.
