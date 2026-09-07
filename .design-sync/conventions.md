# EPI-Aetheris — sistema de diseño

Sistema **solo-tokens**: no hay componentes React que importar. Este paquete
aporta la **identidad visual** de EPI-Aetheris (una plataforma de vigilancia
epidemiológica: dashboards, mapas, curvas epidémicas). Al diseñar, construí
tus propios elementos (botones, tarjetas, tablas) usando estos tokens y
reglas — así todo sale con la paleta y la tipografía del proyecto.

## Setup

No hace falta ningún provider ni wrapper. Enlazá `styles.css` una vez en la
raíz del documento; define `@font-face` de las tres familias, todos los
tokens en `:root`, y las reglas base (cuerpo, `::selection`, scrollbar,
enlace, anillo de foco, `.card-elevated`, `.skeleton`).

## El idioma: `var(--*)`, no clases utilitarias

En la app real estos tokens se exponen además como utilidades de Tailwind
v4, pero **acá no hay Tailwind**. Estilá con las custom properties CSS
directamente (`color: var(--color-ink)`, `background: var(--color-surface)`).
No inventes clases tipo `bg-surface` ni `text-lg`: no resuelven.

## Color — y la regla de emparejamiento fondo↔texto

Cada token de fondo tiene su propio token de texto. **Usá siempre el par**:
poner texto arbitrario sobre un fondo rompe el contraste (todos los pares
cumplen AA o mejor).

| Fondo | Token fondo | Token texto encima | Uso |
|---|---|---|---|
| Lienzo | `--color-bg` (`#f0f0f0`) | `--color-ink` (`#040316`) · atenuado `--color-ink-muted` (`#4c5a56`) | fondo de página |
| Tarjeta | `--color-surface` (`#ffffff`) | `--color-ink` / `--color-ink-muted` | tarjetas, paneles, superficies elevadas |
| Primario | `--color-accent` (`#183e39`, verde) | `--color-accent-ink` (`#ffffff`) | botones activos, header, enlaces, estado "on" |
| Secundario | `--color-secondary` (`#dddbff`, lavanda) | `--color-secondary-ink` (`#183e39`) | chips, badges, estados suaves/informativos |
| Contraste alto | `--color-deep` (`#011e1e`, verde casi negro) | `--color-deep-ink` (`#dddbff`) · atenuado `--color-deep-ink-muted` | footer, secciones archivadas, paneles de máximo contraste |
| Borde | `--color-border` (`#e0e0e6`) | — | divisores, bordes de tarjeta, track del scrollbar |

`--color-accent` es también el color de enlace (lo fija `base.css` en `a`).

## Tipografía — tres voces

| Token | Familia | Para |
|---|---|---|
| `--font-sans` | Inter | cuerpo y **toda la UI funcional** (botones, labels, inputs, subtítulos de tarjeta) |
| `--font-mono` | IBM Plex Mono | etiquetas de ejes, valores numéricos, código inline, datos tabulares |
| `--font-display` | Fraunces (opsz 144, serif editorial de alto contraste) | **solo** H1 de página y los 2 H2 de sección de la landing |

**Restricción de Fraunces (importante):** nunca en subtítulos de tarjeta,
encabezados de sección internos, ni ningún elemento de UI funcional. Es una
voz de titular reservada. Fuera de esos 3 lugares, los headings usan
`--font-sans` con peso 600.

## Sombra y foco

- **Elevación:** `box-shadow: var(--shadow-card)` en reposo, `var(--shadow-card-hover)`
  en hover. La clase `.card-elevated` ya lo hace (incluye la transición y la
  combinación con el anillo de foco).
- **Foco de teclado:** `base.css` da un `:focus-visible` de doble anillo
  (outline lavanda + box-shadow oscuro exterior) que cumple ≥3:1 sobre
  cualquier superficie. No lo pises con `outline: none`.
- Radios: las tarjetas/skeleton usan `0.375rem`. No hay token de radio;
  seguí ese valor.

## Marca / logo

Hay dos piezas en `guidelines/`: el **imagotipo horizontal**
(`logo-wordmark-on-dark.svg` — wordmark "EPI / Aetheris" en blanco + una curva
epidémica coral, para fondo oscuro) y el **monograma** (`logo-monogram.svg` —
cuadrado verde con "EA", E blanca + A coral). `guidelines/brand.md` tiene la
descripción completa, las reglas y la lista de variantes a producir.

- **Coral de marca `#ff5a45`: solo logo.** No es un token de UI. No usarlo
  para botones, enlaces ni estados — vive únicamente en la curva epidémica y
  en la "A" del monograma. Para acento operativo va `--color-accent`.
- El dispositivo de la **curva epidémica coral** es la constante de la
  identidad: cualquier variante nueva del logo lo conserva.
- El verde del logo es el mismo `--color-accent` (`#183e39`).

## Ejemplo idiomático

```html
<article class="card-elevated" style="
  background: var(--color-surface);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  padding: 1.25rem;
  font-family: var(--font-sans);
">
  <h3 style="font-family: var(--font-sans); font-weight: 600; margin: 0 0 .5rem;">
    Casos notificados
  </h3>
  <p style="font-family: var(--font-mono); font-size: 2rem; margin: 0;">2 742</p>
  <p style="color: var(--color-ink-muted); margin: .5rem 0 0;">
    Semana epidemiológica 34
  </p>
  <span style="
    display: inline-block; margin-top: .75rem; padding: .125rem .5rem;
    background: var(--color-secondary); color: var(--color-secondary-ink);
    border-radius: 999px; font-size: .8125rem;
  ">estable</span>
</article>
```
