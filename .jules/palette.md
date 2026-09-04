## 2026-08-21 - First palette learning
**Learning:** Adding empty states makes it easier for users to know what to do next.
**Action:** Always provide empty states.

## 2026-08-28 - Inline Action Feedback on Buttons
**Learning:** For asynchronous actions (like generating a CSV or copying a URL), relying only on a decoupled status text can lead to poor UX because the user might miss the feedback if they are focused on the button they just clicked.
**Action:** Always provide inline, temporary feedback directly on the button text (e.g. changing "Copiar enlace" to "¡Copiado!") alongside a decoupled status text. Use a visual change (like `text-accent`) that resets after a short delay (e.g., 2000ms) to provide immediate positive reinforcement.

## 2026-09-02 - Unified form element styles
**Learning:** This application lacks a global, unified style rule for interactive form elements like checkboxes (e.g. `type="checkbox"`). Some components, like `FiltrosAnalisis.astro` use `accent-accent` appropriately to visually integrate inputs with the system's aesthetic, while other components like `SelectorPaneles.astro` fell back to default browser blue, leading to visual inconsistencies.
**Action:** When adding new form inputs or reviewing older components, ensure they utilize the `accent-accent` class (or another appropriate design token) to maintain visual cohesion with the broader design system. Alternatively, consider abstracting a `<Checkbox />` component to enforce consistency at the design-system level.
