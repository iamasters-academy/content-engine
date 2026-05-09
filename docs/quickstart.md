# Quickstart — your first post in 10 minutes

Assumes you finished [installation.md](installation.md).

## 1. Open Claude Code in any project

```bash
cd ~/some-project
claude
```

## 2. Trigger the skill

```
/content-engine
```

## 3. First-run brand brief (8-10 min, only the first time)

The skill asks you 8-10 questions. Answer naturally. Examples:

- *"Who is your ideal client?"* → "B2B SMB owners of 10-50 people who feel their team wastes time on repetitive tasks"
- *"What's your differentiator?"* → "I implement the fix and stay until the team adopts it. Results in 90 days or refund."
- *"Tone?"* → "Direct, with data. Zero hype."
- *"Anti-topics?"* → "Generic motivation, AI hype without use case"
- *"Default CTA?"* → "DM me for a 15-min check, no charge"

The skill generates a YAML brief, shows it to you, you validate, it saves it to `data/briefs/your-name.yaml`.

## 4. Give it your input

Pass anything:

```
"Take this idea and make me content for LinkedIn and Instagram:
Today a client of 18 people who manually invoiced 200 invoices/month
saved 26 hours by automating it with AI. The admin assistant moved
those hours to chasing payments and brought down receivables from
90 to 65 days."
```

Or pass a file:

```
"Transcribe this audio and turn it into content: ./morning-recording.m4a"
```

Or a URL:

```
"Read this article and turn the key insight into content:
https://example.com/article-i-liked"
```

## 5. Review the 5 pieces

The skill generates LinkedIn / X / Instagram / YouTube short / TikTok pieces and shows them all. Edit any of them by saying:

> "Make the LinkedIn post 30% shorter and remove the third lesson."

## 6. Choose your visual

The skill asks:

- 1 image, carousel of 3, or reel script?
- Aspect ratio? (1:1 IG, 9:16 reels, 16:9 LinkedIn cover)
- Are you in the image?
- Pro (Fal.ai automatic) or free (ChatGPT manual)?

If you pick Pro, the skill calls Fal.ai's `nano-banana-2`, waits ~10 seconds, and shows you the image.

## 7. Publish

The skill asks which networks to publish to (checkboxes). It calls Upload-Post API and gives you the post URLs.

## 8. Hand off the rest

Open the generated `dashboard.html` in your `data/inbox-redes/<date>-<slug>/` folder. Share with your community manager via WhatsApp. They have everything ready: copy-to-clipboard buttons, schedule suggestions, hashtags.

---

## What's next

- See [examples.md](examples.md) for real walkthroughs.
- Tune your brief over time — edit `data/briefs/your-name.yaml` directly any time.
- Share the skill: it's MIT licensed.
