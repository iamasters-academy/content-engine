# Guía de instalación

> **¿Solo quieres usarla rápido?** No leas esta guía. Ejecuta `/content-engine` y la skill te lleva sola. Esta guía es para casos en que prefieres hacerlo manualmente.

---

## Instalación express (con wizard)

```bash
git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine
claude
```

Dentro de Claude Code:

```
/content-engine
```

La skill te guía. Listo. **Si esto te basta, no necesitas el resto del documento.**

---

## Instalación manual (sin wizard)

Útil si prefieres tener todo configurado antes de hablar con la skill.

### 1. Clonar la skill

```bash
git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine
cd ~/.claude/skills/content-engine
```

### 2. Conseguir las API keys

#### Fal.ai (generación de imagen) — obligatoria

1. Regístrate en https://fal.ai (puedes usar tu Google).
2. Ve a https://fal.ai/dashboard/keys y crea una key.
3. Cópiala.

#### Groq (transcripción de audio/vídeo) — opcional

Solo si vas a pasar audios o vídeos como input.

1. Regístrate en https://console.groq.com.
2. Ve a https://console.groq.com/keys y crea una key.
3. Cópiala.

#### Upload-Post (publicación) — opcional

Solo si vas a publicar automáticamente. Si solo quieres generar contenido y publicar a mano, salta esto.

1. Regístrate en https://upload-post.com — Plan Free, 10 publicaciones/mes.
2. En el dashboard, conecta LinkedIn (botón "Connect LinkedIn" → autoriza).
3. Conecta Instagram. **Importante**: requiere cuenta Business o Creator enlazada a una página de Facebook. Si no la tienes así, la conviertes en `Instagram → Settings → Account → Switch to Professional Account`.
4. Sección API → genera API key. Cópiala.

#### OpenAI (alternativa de imagen) — opcional

Solo si vas a usar OpenAI en lugar de Fal para imagen.

1. https://platform.openai.com/api-keys → crea key.
2. Asegúrate de tener crédito en https://platform.openai.com/billing.

### 3. Configurar variables de entorno

```bash
cd ~/.claude/skills/content-engine
cp .env.example .env.local
```

Edita `.env.local` y rellena las claves que tengas.

Cárgalas en cada sesión de shell:

```bash
# Opción A — sourcear manualmente
source .env.local

# Opción B — añadir a ~/.zshrc o ~/.bashrc para que se carguen siempre
echo 'set -a; source ~/.claude/skills/content-engine/.env.local; set +a' >> ~/.zshrc
source ~/.zshrc
```

Verifica:

```bash
echo $FAL_KEY $UPLOAD_POST_API_KEY
# Debería mostrar dos strings no vacíos
```

### 4. Configurar el modelo de imagen

Crea `data/image_config.yaml`:

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

Si prefieres OpenAI:

```yaml
provider: openai
model_id: gpt-image-1
endpoint: ""
defaults:
  aspect_ratio: "1:1"
  resolution: ""
  output_format: "png"
notes: ""
```

### 5. (Opcional) Crear tu brief de marca a mano

Copia `templates/brief.yaml.template` a `data/briefs/mi-marca.yaml` y rellena los campos. La skill respeta este archivo como fuente de verdad. Si no lo creas, la skill te entrevistará en la primera ejecución.

### 6. Test individual de los tools

```bash
# Test Fal — debe generar un PNG 1:1 y guardarlo
python ~/.claude/skills/content-engine/tools/fal_image.py \
    --prompt "A black labrador swimming in a clear lake, photorealistic" \
    --aspect-ratio 1:1 \
    --output /tmp/fal-test.png

# Test image_engine (delega al backend configurado)
python ~/.claude/skills/content-engine/tools/image_engine.py \
    --prompt "Same labrador, different angle" \
    --aspect-ratio 1:1 \
    --output /tmp/engine-test.png

# Test Groq (graba un audio corto primero)
python ~/.claude/skills/content-engine/tools/groq_transcribe.py \
    --file /tmp/test.m4a --language es

# Test Upload-Post (publica un test en LinkedIn — vas a tener que borrarlo después!)
python ~/.claude/skills/content-engine/tools/upload_post.py \
    --image /tmp/fal-test.png \
    --caption "Probando content-engine. Lo borraré." \
    --platforms linkedin
```

Si los 4 funcionan, todo está bien.

### 7. Usar la skill

```
/content-engine
```

La skill detecta que tienes todo configurado y va directa a generar contenido.

---

## Troubleshooting

### `FAL_KEY no está definida`

Cargas `.env.local` otra vez:
```bash
source ~/.claude/skills/content-engine/.env.local
```

O añade la línea de auto-load a tu `~/.zshrc` (paso 3 de arriba).

### Instagram no aparece en Upload-Post tras conectar

Tu cuenta es Personal. Pasa a Business o Creator desde la app de Instagram (Settings → Account → Switch to Professional Account) y enlázala a una Facebook Page.

### Groq devuelve `file too large`

Free tier es 25 MB por archivo. O subes a dev tier (100 MB) o trozeas el audio. La skill te explica cómo si llegas ahí.

### Fal devuelve timeout

Raro. La skill auto-pollea hasta 120 segundos. Reintenta.

### OpenAI devuelve 403

Tu cuenta no tiene crédito. Mete saldo en https://platform.openai.com/billing.

### El comando `/content-engine` no aparece en Claude Code

Verifica que la skill está en `~/.claude/skills/content-engine/` y reinicia Claude Code (cerrar y volver a abrir terminal).
