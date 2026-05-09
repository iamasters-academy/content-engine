# Flujo de onboarding — qué pasa la primera vez

Este documento explica **qué te va a preguntar la skill la primera vez** que la ejecutas, para que sepas qué esperar.

> **No tienes que leer esto antes de usarla.** La skill te lleva de la mano. Lee este doc solo si tienes curiosidad de qué va a pasar o si algo se te atascó.

---

## El flujo en una imagen

```
clone repo  →  /content-engine  →  Fase 0  →  Fase 0.5  →  Fase A  →  primer post
                                  setup     modelo     brief    publicado
                                  (~10 min)  (~2 min)  (~8 min)
```

---

## Fase 0 — Setup Wizard (~10 min)

La skill detecta que no tienes `.env.local` y arranca el wizard.

### Paso 0.1 — Fal.ai

> *"¿Tienes ya cuenta en Fal.ai?"*
> - Si sí → te pide la API key.
> - Si no → te dice exactamente qué hacer:
>   1. Ir a https://fal.ai
>   2. Registrarte (puedes usar tu Google)
>   3. Ir a https://fal.ai/dashboard/keys
>   4. Crear una key y copiarla
>
> Pegas la key. La skill la guarda en `.env.local` directamente. No queda en el chat.
> Hace una llamada de test para verificar que funciona.

### Paso 0.2 — Upload-Post

> *"¿Quieres publicar automáticamente o solo generar contenido?"*
>
> Si **solo generar**: salta al siguiente paso. No necesitas Upload-Post.
>
> Si **publicar también**:
>   1. Vas a https://upload-post.com — Plan Free, 10 publicaciones/mes.
>   2. Conectas LinkedIn (5 min OAuth).
>   3. Conectas Instagram. Importante: tu cuenta IG tiene que ser **Business o Creator** y estar enlazada a una página de Facebook. Si no la tienes así, la skill te explica cómo cambiarla.
>   4. Generas API key en sección API. La copias.
>
> Pegas la key. La skill la valida.

### Paso 0.3 — Groq

> *"¿Vas a pasar audios o vídeos como input?"*
>
> Si **no**: salta. No necesitas Groq.
>
> Si **sí**:
>   1. https://console.groq.com — registro free.
>   2. https://console.groq.com/keys — crear key.
>   3. Copiar y pegar.

### Paso 0.4 — Confirmación

> *"Listo. Has configurado: ✓ Fal.ai · ✓ Upload-Post · ✓ Groq. Las claves están en `.env.local` (gitignored). Pasamos al siguiente paso."*

---

## Fase 0.5 — Selección de modelo de imagen (~2 min)

La skill te pregunta qué modelo quieres usar:

```
1. nano-banana-2 (Google, default — recomendado para empezar)
2. flux-pro/v1.1-ultra (Black Forest Labs, máxima calidad fotorealista)
3. flux/dev (más rápido y barato)
4. Otro modelo de Fal.ai (pásame la URL)
5. OpenAI gpt-image-1 (necesita OPENAI_API_KEY)
6. Decidir más tarde (uso default = nano-banana-2)
```

### Si eliges 4 (otro de Fal)

> *"Pásame la URL del modelo, ej. https://fal.ai/models/fal-ai/recraft-v3/api"*

La skill lee la doc del modelo, extrae el endpoint y los parámetros, y configura
el adaptador. Si hay algo del modelo que no encaja con el flujo (ej. requiere
imágenes de referencia obligatorias), te avisa.

### Si eliges 5 (OpenAI)

> *"Necesito tu OpenAI API key. Consíguela en https://platform.openai.com/api-keys"*

Pegas, valida, listo.

### Resultado

Se guarda en `data/image_config.yaml`:

```yaml
provider: fal
model_id: nano-banana-2
endpoint: fal-ai/nano-banana-2
defaults:
  aspect_ratio: "1:1"
  resolution: "1K"
  output_format: "png"
notes: ""
```

Puedes editar este archivo después si quieres cambiar de modelo. La skill lo
respeta como fuente de verdad.

---

## Fase A — Brief de marca personal (~8 min)

La skill te entrevista con 8-10 preguntas:

1. ¿Quién es tu cliente ideal?
2. ¿Qué transformación entregas?
3. ¿Qué te diferencia?
4. ¿Qué tono tienes?
5. ¿Anti-temas? (cosas de las que NUNCA hablas)
6. ¿En qué redes estás activo?
7. ¿Qué formatos te funcionan?
8. ¿CTA por defecto?
9. ¿Idioma del output?
10. ¿Marcas que admiras como referencia?

Genera un YAML, te lo enseña, validas (o pides cambios). Se guarda en
`data/briefs/<slug>.yaml`.

**Solo se hace una vez.** En adelante la skill carga este brief automáticamente.

---

## Total tiempo primer arranque

- Setup wizard (Fase 0): ~10 min
- Selección modelo (Fase 0.5): ~2 min
- Brief personal (Fase A): ~8 min
- **Total: ~20 min**

A partir de aquí, cada post nuevo te lleva ~2-3 min.

---

## ¿Y si quiero saltarme el wizard?

Puedes hacerlo todo manual:

1. `cp .env.example .env.local` y rellena las keys.
2. Crea `data/image_config.yaml` con tu modelo elegido (mira la sección [Fase 0.5](#fase-05--selección-de-modelo-de-imagen-2-min) de este doc).
3. Crea `data/briefs/mi-marca.yaml` desde `templates/brief.yaml.template`.
4. Ejecuta `/content-engine`.

La skill detecta que ya tienes todo y va directa a generar contenido.

Ver [installation.md](installation.md) para el detalle paso a paso del setup manual.

---

## Si algo falla durante el wizard

La skill te explica qué falló y qué hacer. Casos comunes:

- **`FAL_KEY` rechazada**: la key tiene espacios al pegarla, regenérala y vuelve a pegar.
- **Instagram no conecta en Upload-Post**: tu cuenta no es Business/Creator. Conviértela en Settings → Account type.
- **Groq devuelve 401**: la key se pegó mal o se revocó. Genera una nueva.
- **OpenAI 403**: tu cuenta no tiene crédito o no ha verificado el método de pago. Mete 5 € en https://platform.openai.com/billing.

Si el problema persiste, abre un issue en https://github.com/iamasters-academy/content-engine/issues.
