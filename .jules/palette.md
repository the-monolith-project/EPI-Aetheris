## 2026-08-21 - First palette learning
**Learning:** Adding empty states makes it easier for users to know what to do next.
**Action:** Always provide empty states.

## 2026-08-28 - Inline Action Feedback on Buttons
**Learning:** For asynchronous actions (like generating a CSV or copying a URL), relying only on a decoupled status text can lead to poor UX because the user might miss the feedback if they are focused on the button they just clicked.
**Action:** Always provide inline, temporary feedback directly on the button text (e.g. changing "Copiar enlace" to "¡Copiado!") alongside a decoupled status text. Use a visual change (like `text-accent`) that resets after a short delay (e.g., 2000ms) to provide immediate positive reinforcement.

## 2026-09-02 - Unified form element styles
**Learning:** This application lacks a global, unified style rule for interactive form elements like checkboxes (e.g. `type="checkbox"`). Some components, like `FiltrosAnalisis.astro` use `accent-accent` appropriately to visually integrate inputs with the system's aesthetic, while other components like `SelectorPaneles.astro` fell back to default browser blue, leading to visual inconsistencies.
**Action:** When adding new form inputs or reviewing older components, ensure they utilize the `accent-accent` class (or another appropriate design token) to maintain visual cohesion with the broader design system. Alternatively, consider abstracting a `<Checkbox />` component to enforce consistency at the design-system level.

## 2026-09-03 - [Accessibility & Micro-UX] Explicit states on icon-only buttons
**Learning:** Icon-only interactive elements lacking explicit hover styles, disabled styles (opacity/cursor feedback), and tooltip (`title`) attributes suffer from poor discoverability and ambiguity, reducing overall application accessibility and user confidence.
**Action:** When adding or auditing icon-only buttons (like zoom controls or action triggers), ensure they include distinct visual feedback for hover (`hover:bg-secondary/30`), disabled states (`disabled:opacity-50 disabled:cursor-not-allowed`), and a descriptive `title` attribute for tooltips, independent of screen-reader-only `aria-label` attributes.
## 2026-09-05 - Range Sliders Accessibility
**Learning:** Multiple range sliders (e.g., dual thumbs for min/max) inside a single wrapping `<label>` tag lack individual context for screen readers. The wrapper text becomes an ambiguous group label.
**Action:** Always add explicit `aria-label` attributes to each `<input type="range">` when multiple inputs share the same visible label to distinguish their specific functions (e.g., 'Semana inicial' vs 'Semana final').
## 2026-09-06 - Accessible Popover Overlays
**Learning:** When building custom popovers (like the workspace analysis filters or the panels menu), trigger buttons that control these menus often fail screen reader tests if they lack explicit `aria-haspopup` attributes, leaving users unaware of the interactive nature of the control. Furthermore, when these popovers are dismissed using a standard interaction (like the Escape key), focus isn't always restored to the original trigger.
**Action:** When building or auditing custom popover patterns, ensure that the trigger button always includes the `aria-haspopup` attribute (set to `dialog` or `menu` as appropriate), and that keyboard dismissal handlers (e.g. Escape key) explicitly call `.focus()` on the trigger element to maintain a logical and usable tab order.
