# Examples

Real walkthroughs to learn the skill's behavior.

## Example 1 — Idea → 5 pieces (no image, no publish)

```
> /content-engine
> "Just generate the 5 pieces for this idea, no image, no publishing:
   Spent 2 hours rebuilding our Notion database from scratch and ended
   up cutting it in half. Less is more — confirmed again."
```

The skill:
1. Loads your brief from `data/briefs/<your-slug>.yaml`.
2. Skips phases A, D, D2, E.
3. Runs phase B (input is plain text, no transcription needed).
4. Runs phase C (5 pieces).
5. Shows them. You can copy/paste manually wherever.

## Example 2 — Audio recording → full pipeline

```
> /content-engine
> "Take this audio and turn it into a LinkedIn post + Instagram post
   with an image. Aspect 1:1, no me in the picture, Fal pro.
   Audio: ~/Desktop/morning-thought.m4a"
```

The skill:
1. Loads brief.
2. Phase B: transcribes the audio with Groq (`whisper-large-v3-turbo`) using your brief language.
3. Phase C: 5 pieces (you'll only use LI + IG, but it generates all 5 for the dashboard).
4. Phase D: skipped (you already specified the visual answers in the prompt).
5. Phase D2: builds image prompt, calls Fal `nano-banana-2`, downloads.
6. Phase E: asks "publish to LinkedIn + Instagram?", you confirm, posts go live.
7. Saves everything to `data/inbox-redes/20260510-morning-thought/`.

## Example 3 — YouTube URL → only the X thread

```
> /content-engine
> "Read this YouTube video and pull only an X thread out of it. No image, no publish.
   https://www.youtube.com/watch?v=..."
```

The skill:
1. Phase B: WebFetch on the URL, extracts transcript or page text.
2. Phase C: only the X thread template.
3. Stops. You copy/paste the thread into X manually.

## Example 4 — Re-using brief with different brand voice

If you have multiple personas (e.g. you post as yourself AND as your company), keep multiple briefs:

```
data/briefs/
├── personal-angel.yaml
├── solutech-ia.yaml
└── iamasters-academy.yaml
```

When you run `/content-engine`, ask:

> "Use the iamasters-academy brief for this one"

The skill loads that specific brief and adapts voice accordingly.

## Example 5 — Tuning your brief over time

You can edit `data/briefs/<slug>.yaml` directly any time. Common tweaks:

- Add a new anti-topic the skill keeps slipping into.
- Add a new format preference ("text_heavy: false" if you start preferring shorter posts).
- Adjust the default CTA to a new offer.
- Add a brand reference if you want the voice to lean toward someone specific.

Save the file. Next time you run the skill, it picks up the changes.
