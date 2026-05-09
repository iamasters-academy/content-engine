# Installation guide

## 1. Clone the skill

```bash
git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine
cd ~/.claude/skills/content-engine
```

## 2. Get the three API keys

### Fal.ai (image generation)

1. Sign up at https://fal.ai
2. Go to https://fal.ai/dashboard/keys
3. Create a new key
4. Copy it

### Groq (audio transcription)

1. Sign up at https://console.groq.com
2. Go to https://console.groq.com/keys
3. Create a new key
4. Copy it

### Upload-Post (publishing)

1. Sign up at https://upload-post.com — Free plan, 10 uploads/month
2. In the dashboard, connect LinkedIn (5 min OAuth)
3. Connect Instagram (5 min OAuth)
   - **Important**: Instagram requires Business or Creator account with a Facebook Page
4. Go to API section → generate API key
5. Copy it

## 3. Configure environment

```bash
cp .env.example .env.local
```

Edit `.env.local` and fill in your three keys. Then:

```bash
# Load on every shell session — pick one:

# Option A: source manually
source .env.local

# Option B: add to ~/.zshrc or ~/.bashrc
echo 'set -a; source ~/.claude/skills/content-engine/.env.local; set +a' >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
echo $FAL_KEY $GROQ_API_KEY $UPLOAD_POST_API_KEY
# Should show three non-empty strings
```

## 4. Test the tools individually

```bash
# Test Fal — should generate a 1:1 PNG and save it
python ~/.claude/skills/content-engine/tools/fal_image.py \
    --prompt "A black labrador swimming in a clear lake, photorealistic" \
    --aspect-ratio 1:1 \
    --output /tmp/fal-test.png

# Test Groq — record a 5s audio first, then:
python ~/.claude/skills/content-engine/tools/groq_transcribe.py \
    --file /tmp/test.m4a --language en

# Test Upload-Post — publish a test post (will go to your real LinkedIn!)
python ~/.claude/skills/content-engine/tools/upload_post.py \
    --image /tmp/fal-test.png \
    --caption "Testing content-engine. Will delete." \
    --platforms linkedin
```

If all three work, you're set.

## 5. Use it

In Claude Code:

```
/content-engine
```

First run: ~8-10 min to fill in your brand brief. After that, ~2 min per post.

## Troubleshooting

- **`FAL_KEY env var not set`**: source `.env.local` again or add it to your shell rc file.
- **Instagram publish fails**: confirm Business/Creator + Facebook Page connected in Upload-Post.
- **Groq `file too large`**: free tier is 25 MB. Either upgrade to dev tier (100 MB) or chunk the audio.
- **Fal queue timeout**: rare; retry. The skill auto-polls for up to 90 seconds.
