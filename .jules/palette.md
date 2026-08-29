## 2026-08-21 - First palette learning
**Learning:** Adding empty states makes it easier for users to know what to do next.
**Action:** Always provide empty states.

## 2026-08-28 - Inline Action Feedback on Buttons
**Learning:** For asynchronous actions (like generating a CSV or copying a URL), relying only on a decoupled status text can lead to poor UX because the user might miss the feedback if they are focused on the button they just clicked.
**Action:** Always provide inline, temporary feedback directly on the button text (e.g. changing "Copiar enlace" to "¡Copiado!") alongside a decoupled status text. Use a visual change (like `text-accent`) that resets after a short delay (e.g., 2000ms) to provide immediate positive reinforcement.
