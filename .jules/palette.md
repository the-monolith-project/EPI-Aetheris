## 2024-08-26 - Added tooltips explaining disabled states
**Learning:** Users often encounter disabled buttons (like CSV download or unavailable map layers) without context, leading to confusion about whether the system is broken or just loading/unavailable. Adding a `title` attribute to disabled buttons provides a native, accessible tooltip that explains *why* the action is currently unavailable.
**Action:** Always provide context for disabled interactive elements, either via visual text, `title` attribute, or custom tooltip, so users understand the system state.
