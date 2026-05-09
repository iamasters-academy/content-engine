# Ejemplos de uso

Casos reales para entender el comportamiento de la skill.

## Ejemplo 1 — Idea suelta → 5 piezas (sin imagen, sin publicar)

```
> /content-engine
> "Solo genera las 5 piezas para esta idea, sin imagen y sin publicar:
   Pasé 2h reconstruyendo nuestra base de Notion desde cero y acabé
   recortándola a la mitad. Menos es más, confirmado otra vez."
```

La skill:
1. Carga tu brief de `data/briefs/<tu-slug>.yaml`.
2. Salta fases 0, 0.5, D, D2, E.
3. Ejecuta Fase B (input es texto, sin transcripción).
4. Ejecuta Fase C (5 piezas).
5. Te las muestra. Las copias y pegas tú a mano donde quieras.

## Ejemplo 2 — Audio → flujo completo

```
> /content-engine
> "Coge este audio y conviértelo en post de LinkedIn + Instagram con
   imagen. Ratio 1:1, sin yo en la foto, ruta pro.
   Audio: ~/Desktop/idea-mañana.m4a"
```

La skill:
1. Carga brief.
2. Fase B: transcribe el audio con Groq (`whisper-large-v3-turbo`) usando el idioma del brief.
3. Fase C: genera las 5 piezas (aunque solo vayas a usar LI + IG, las 5 sirven para el dashboard).
4. Fase D: ya respondiste en el prompt inicial, no pregunta más.
5. Fase D2: construye prompt en inglés, llama a `image_engine.py`, descarga la imagen.
6. Fase E: pregunta "¿LinkedIn + Instagram?", confirmas, los posts salen reales.
7. Guarda todo en `data/inbox-redes/20260510-idea-mañana/`.

## Ejemplo 3 — URL de YouTube → solo hilo de X

```
> /content-engine
> "Lee este vídeo de YouTube y saca solo un hilo de X. Sin imagen, sin publicar.
   https://www.youtube.com/watch?v=..."
```

La skill:
1. Fase B: WebFetch sobre la URL, extrae transcripción o texto de la página.
2. Fase C: solo la plantilla de X thread.
3. Para. Copias y pegas el hilo en X manualmente.

## Ejemplo 4 — Cambiar de modelo de imagen sobre la marcha

```
> /content-engine
> "Cambia el modelo de imagen a flux-pro/v1.1-ultra. Esta foto la quiero más fotorealista."
```

La skill edita `data/image_config.yaml` y continúa con el nuevo modelo.

O incluso pasarle un modelo nuevo que no conoce:

```
> "Usa este modelo: https://fal.ai/models/fal-ai/recraft-v3/api"
```

La skill lee la doc, configura el adaptador y genera la imagen. Sin actualizar el repo.

## Ejemplo 5 — Reusar brief con varias marcas personales

Si publicas como tú **y** como tu empresa, mantén briefs separados:

```
data/briefs/
├── personal-angel.yaml
├── solutech-ia.yaml
└── iamasters-academy.yaml
```

Cuando ejecutas `/content-engine`, dile:

> "Usa el brief iamasters-academy para este post"

La skill carga ese brief específico y adapta la voz.

## Ejemplo 6 — Ajustar el brief con el tiempo

Edita `data/briefs/<slug>.yaml` directamente cuando notes patrones que quieres ajustar:

- Añadir un anti-tema nuevo en el que la skill se mete sin querer.
- Cambiar `format_preferences.text_heavy` a `false` si empiezas a preferir posts más cortos.
- Actualizar el CTA por defecto a una oferta nueva.
- Añadir una marca de referencia si quieres que la voz tire hacia alguien específico.

Guarda el archivo. La próxima ejecución la skill recoge los cambios.

## Ejemplo 7 — Solo dashboard, sin publicar

Si tu community manager publica desde Buffer/Metricool, no hace falta que la skill publique. Solo dile:

```
> "Genera las 5 piezas + imagen + dashboard. No publiques."
```

La skill genera todo y te deja `dashboard.html` listo. Tu CM lo abre y trabaja desde ahí.
