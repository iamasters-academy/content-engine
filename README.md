# content-engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made by IA Masters Academy](https://img.shields.io/badge/made%20by-IA%20Masters%20Academy-3FB8C9)](https://iamastersacademy.com)
[![Skill for Claude Code](https://img.shields.io/badge/skill%20for-Claude%20Code-E85A2C)](https://docs.claude.com/en/docs/claude-code)

> **Agentic skill for Claude Code that turns any input into 5 social-media-ready pieces, generates an image with Google's nano-banana-2, and publishes to LinkedIn + Instagram. One conversation. Zero n8n nodes.**

---

## What it does

You give it any of these:
- A short idea
- Long text or an article
- An audio file (any format)
- A video file
- A URL (YouTube, Instagram, podcast, blog)
- A PDF

It does this:

1. Builds your personal brand brief once (8-10 questions, saved as YAML).
2. Processes the input (transcribes if audio/video, fetches if URL).
3. Researches what's working in 2026 on each network.
4. Generates 5 pieces of text adapted by channel (LinkedIn / X / Instagram / YouTube short / TikTok).
5. Asks you about the visual (single image / carousel / reel · aspect ratio · with you in it or not · Fal automatic or ChatGPT manual).
6. If you chose Fal, it generates the image agentically with `fal-ai/nano-banana-2`.
7. Publishes to LinkedIn and Instagram via Upload-Post API.
8. Generates a dashboard HTML you can hand off to a community manager.

---

## Why it exists

Most content workflows live in n8n: 25 nodes, the same text on every network, and an external image step that breaks the flow. This skill replaces the entire workflow with a conversation. You talk to it. It thinks. It posts.

It was built as a reference implementation for the [IA Masters Academy](https://iamastersacademy.com) Sunday class on May 10, 2026 — the last open class before the community opens on May 17.

---

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- Python 3.9+ (uses stdlib only — zero pip dependencies).
- A free [Fal.ai](https://fal.ai) account → API key.
- A free [Groq](https://console.groq.com) account → API key (audio transcription).
- A free [Upload-Post](https://upload-post.com) account → API key + LinkedIn + Instagram connected.

---

## Install

```bash
# 1. Clone into your Claude Code skills directory
git clone https://github.com/iamasters-academy/content-engine.git ~/.claude/skills/content-engine

# 2. Set up environment variables
cd ~/.claude/skills/content-engine
cp .env.example .env.local
# Edit .env.local and add your real keys
```

For Instagram: your account must be Business or Creator with a Facebook Page connected.

---

## Use

In Claude Code:

```
/content-engine
```

The skill walks you through everything. First run: 8-10 minutes to set up your brand brief. After that: ~2 minutes per post.

### Manual mode

Each tool can be called directly via Bash:

```bash
# Transcribe audio
python ~/.claude/skills/content-engine/tools/groq_transcribe.py \
    --file my-audio.mp3 --language es

# Generate an image
python ~/.claude/skills/content-engine/tools/fal_image.py \
    --prompt "A professional minimalist scene of..." \
    --aspect-ratio 1:1 \
    --output _assets/imagen.png

# Publish to LinkedIn + Instagram
python ~/.claude/skills/content-engine/tools/upload_post.py \
    --image _assets/imagen.png \
    --caption "Your caption..." \
    --platforms linkedin,instagram
```

---

## Architecture

```
content-engine/
├── SKILL.md                    # Skill instructions (read by Claude Code)
├── tools/
│   ├── fal_image.py            # Fal.ai client (nano-banana-2)
│   ├── groq_transcribe.py      # Groq Whisper API client
│   └── upload_post.py          # Upload-Post API client
├── templates/
│   ├── brief.yaml.template     # Brand brief schema
│   ├── linkedin.md
│   ├── instagram.md
│   ├── x-thread.md
│   ├── youtube-short.md
│   ├── tiktok.md
│   └── dashboard.html.template
├── data/
│   ├── briefs/                 # Your brand briefs (git-ignored)
│   └── inbox-redes/            # Generated outputs (git-ignored)
├── docs/
│   ├── installation.md
│   ├── quickstart.md
│   └── examples.md
└── .env.example
```

---

## Cost (real)

- Fal.ai `nano-banana-2`: pay-per-image, see [pricing](https://fal.ai/models/fal-ai/nano-banana-2/api).
- Groq Whisper: free tier covers normal personal use comfortably.
- Upload-Post: free tier = 10 uploads/month.

For typical use (1-2 posts/week), expect **under €5/month total**.

---

## Limits and honest non-features

- ❌ Does NOT auto-publish at scheduled times. Your Mac must be on and Claude Code running.
- ❌ Does NOT replace your community manager — it produces handoff material.
- ❌ Does NOT connect directly to LinkedIn/Instagram — Upload-Post acts as the certified aggregator.
- ❌ Does NOT invent stats or quotes. Cites sources.
- ❌ Does NOT cross-post the same text. Adapts per channel by design.

---

## Contributing

This is a reference implementation. Forks welcome. PRs welcome if they keep the skill in the same lane (agentic, conversational, zero-deps where possible).

---

## License

MIT. See [LICENSE](LICENSE).

---

## Citation

If you build on top of this, cite it via [CITATION.cff](CITATION.cff).

---

<sub>Built by [Angel Aparicio](https://www.linkedin.com/in/angel-aparicio92) · [IA Masters Academy](https://iamastersacademy.com) · [AASC Associates](https://github.com/iamasters-academy) · `aaparicio@iamastersacademy.com`</sub>
