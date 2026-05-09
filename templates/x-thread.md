# Plantilla — Hilo en X (Twitter)

5-9 tweets. Cada tweet ≤ 280 caracteres. El primero es el hook.

## Estructura

1. **Tweet 1 — Hook**. Promete algo concreto. Crea curiosity gap.
2. **Tweet 2 — Setup**. Contexto para la historia.
3. **Tweets 3-7 — Cuerpo**. Una idea por tweet. Cada tweet debe leerse solo.
4. **Tweet 8 — Lección**. Takeaway destilado.
5. **Tweet 9 — CTA**. Del brief. Más una línea "follow me for more".

## Reglas duras

- 280 caracteres MAX por tweet (límite duro).
- Sin emoji al inicio de ningún tweet.
- Máximo 1-2 saltos de línea dentro de un tweet (X colapsa whitespace largo).
- Respeta `tone.primary` del brief, tirando más corto y punzante que en otros canales.
- Output en el `language` del brief.
- NO numeres los tweets en el texto — X auto-numera en vista de hilo.
- El último tweet debe funcionar standalone si alguien lo cita.

## Variables

- `{{thread}}` — array de tweets
- `{{schedule_suggestion}}` — ej. "Jueves 14:00 CET"
- `{{tweet_count}}` — auto
