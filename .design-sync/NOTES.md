# design-sync — notas de EPI-Aetheris

## Forma del repo
- Proyecto **Astro puro** (`web/`), sin componentes React ni Storybook. El
  converter (`package-build.mjs`) no aplica: esbuild no tiene loader `.astro`
  y no hay `dist/` de librería.
- Sync **solo-tokens**. El layout de `ds-bundle/` se autor-genera a mano:
  `styles.css` → `@import` de `fonts/fonts.css`, `tokens/tokens.css`,
  `tokens/base.css`. `_ds_bundle.js` es un IIFE vacío (`window.Aetheris`).
- `componentCount: 0` en `.ds-build-meta.json` → validate lo trata como
  tokens-only y no exige previews.

## Fuentes
- Inter / IBM Plex Mono / Fraunces las auto-hospeda la Fonts API de Astro.
  Los `.woff2` (subconjunto latino) se copiaron de `web/dist/_astro/fonts/`
  tras `pnpm build`:
  - `inter-latin.woff2` = `e868cdf4720e9ea5.woff2` (normal 400–700, VF)
  - `inter-latin-italic.woff2` = `91753f8d8da3aeb7.woff2` (italic)
  - `ibm-plex-mono-latin.woff2` = `45f5561f938fa232.woff2` (400)
  - `fraunces-latin.woff2` = `caaebc34c5213078.woff2` (600/700, opsz 144)
- `fonts/fonts.css` re-declara `@font-face` con familias limpias
  (`Inter` / `IBM Plex Mono` / `Fraunces`). En `tokens/tokens.css` las tres
  líneas `--font-*` se reescribieron de `var(--font-inter), …` (var de build
  de Astro, inexistente fuera) a las familias reales.

## Regla de negocio que solo vive en un comentario del código
- Fraunces (`--font-display`): **solo** H1 de página y los 2 H2 de sección de
  la landing. Nunca en subtítulos de tarjeta ni UI funcional. Está en
  `conventions.md`; origen: comentario en `web/src/styles/tokens.css`.

## Marca / logo
- `ds-bundle/guidelines/` lleva `brand.md` + los dos SVG existentes
  (`logo-wordmark-on-dark.svg` = `web/public/logo/logo-dark-bg.svg`,
  `logo-monogram.svg` = `web/public/favicon.svg`). El encargo del usuario es
  generar más variantes de logo en Claude Design a partir de estos.
- **Coral `#ff5a45`** aparece en los SVG del logo pero NO es un token del
  sistema (la paleta de UI es verde+lavanda). Documentado como solo-marca en
  `brand.md` y `conventions.md` para que el agente no lo use en botones.
- Si cambian los SVG en `web/public/`, re-copiarlos a `guidelines/`.

## Re-sync risks
- Si el coordinador cambia la paleta o las fuentes en `web/src/styles/`,
  hay que **regenerar `ds-bundle/` a mano** (no hay converter). Pasos:
  1. `cd web && pnpm build`
  2. re-copiar los `.woff2` de `dist/_astro/fonts/` (los hashes cambian)
  3. re-copiar valores de `web/src/styles/tokens.css` a
     `ds-bundle/tokens/tokens.css` (dejando las 3 líneas `--font-*` reales)
  4. re-copiar la parte no-Tailwind de `global.css` a `tokens/base.css`
  5. `node <skill>/package-validate.mjs ./ds-bundle --no-render-check`
  6. re-subir con DesignSync (proyecto pinneado en `config.json`)
- `_ds_sync.json` se omite a propósito (layout off-script) → cada sync
  re-verifica todo, que con 0 componentes es gratis.
- El pane "Design system" en claude.ai/design queda **sin componentes**: el
  agente recibe la paleta/tipografía y construye sus propios elementos.
