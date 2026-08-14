# Levantamiento de gaps del stack `web/`

**Estado:** aprobaciones técnicas dentro del stack vigente para adopción futura; este documento no autoriza instalar dependencias ni modifica el runtime actual.

## Alcance y estado actual

El frontend usa Astro, TypeScript, Tailwind CSS v4 y Leaflet, sin React ni Vue. La revisión evalúa herramientas complementarias antes de incorporarlas; una aprobación significa compatibilidad y aprobación técnica dentro del stack vigente, no instalación inmediata.

| Área | Herramienta | Decisión | Momento de adopción |
|---|---|---|---|
| Iconografía | `astro-icon` + Iconify | Aprobada | Cuando se necesiten iconos reutilizables |
| Tipografías | `@fontsource/inter`, `@fontsource/ibm-plex-mono` | Aprobadas | Próxima mejora de UI |
| Métricas | Observable Plot | Aprobada | Al implementar `MetricasModelo.astro` |
| Color | ColorBrewer + `chroma.js` | Aprobados | Al definir la política visual del mapa/gráficas |
| Clasificación cartográfica | `simple-statistics` | Aprobada condicionalmente | Tras cumplir la condición departamental/MINSAL |
| Calidad | `@astrojs/check`, ESLint, Prettier | Aprobados | Próxima fase de tooling/CI |
| E2E y accesibilidad | Playwright + `@axe-core/playwright` | Aprobados | Adopción progresiva al estabilizar el dashboard |
| Internacionalización | i18n nativo de Astro | Aprobada | Implementación diferida hasta requerimiento real |

## Decisiones de UI

### Iconos: `astro-icon` + Iconify

Se aprueba `astro-icon` con conjuntos de Iconify para iconografía reutilizable que se resuelva como SVG, sin introducir un framework cliente. Se elegirá uno o dos conjuntos coherentes —preferentemente Lucide o Tabler— y se verificará su licencia antes de usarlos. Reemplaza SVG copiados de forma aislada e imágenes externas para iconos simples.

### Tipografías: Fontsource

Se aprueban `@fontsource/inter` y `@fontsource/ibm-plex-mono` para sustituir las solicitudes actuales a Google Fonts. La adopción debe importar solamente los pesos usados, medir el tamaño final de assets y retirar los enlaces CDN equivalentes. El objetivo es conservar el despliegue autocontenido y reducir dependencias externas de renderizado.

### Métricas: Observable Plot

Se aprueba Observable Plot para gráficas estadísticas de la salida del modelo: matriz de confusión, precisión, recall, F1 por clase, F1 macro, recall de la clase alta y comparación con la línea base climatológica. Puede trabajar desde JavaScript normal de Astro y generar SVG/HTML; no sustituye Leaflet ni se usará para el mapa.

La primera implementación debe ser estática o tener un selector simple por año. Antes de integrarla debe existir un contrato de datos: endpoint de API, artefacto generado por entrenamiento o fixture verificable.

### Color: ColorBrewer + `chroma.js`

Se aprueban ColorBrewer como base de paletas cartográficas y `chroma.js` para escalas, interpolación, clases y valores sin dato. La política visual debe separar la clasificación de valores de la asignación de colores, mantener una leyenda equivalente y evaluar contraste/percepción de color. No se deben dispersar colores hardcodeados ni usar una semántica verde/amarillo/rojo sin validación de accesibilidad.

## Coroplético descriptivo

Leaflet renderiza la geometría, pero no define los cortes de clase. `simple-statistics` queda aprobado condicionalmente para cuantiles, intervalos o `ckmeans`; no se instala hasta que se cumpla la condición departamental/MINSAL: indicador descriptivo definido y contrato de datos verificado.

Un corte estadístico expresa magnitud relativa dentro del conjunto analizado; no equivale a un umbral epidemiológico ni a riesgo crítico. Si MINSAL u OPS aportan umbrales oficiales, prevalecen. Si no existen, cualquier clasificación relativa debe declararse explícitamente como tal.

El mapa del MVP sigue siendo una capa departamental descriptiva basada en casos MINSAL desacumulados. El riesgo del modelo es nacional y debe mostrarse como elemento separado; ninguna clase del coroplético puede presentarse como riesgo departamental. Sus clases finales no están definidas por este documento.

## Calidad, formato y pruebas

### Type-check, linting y formato

Se aprueban `@astrojs/check`, ESLint con `eslint-plugin-astro`, y Prettier con `prettier-plugin-astro`. Sus responsabilidades no se solapan:

```text
Prettier       → formato consistente
ESLint         → reglas y calidad estática
astro check    → tipos de TypeScript y componentes Astro
```

Su adopción no afecta el bundle de producción. La política de CI puede endurecerse gradualmente, pero primero debe definirse la configuración y los scripts del proyecto.

### Playwright y accesibilidad

Se aprueban Playwright y `@axe-core/playwright`, con adopción progresiva; no se creará una infraestructura de accesibilidad separada. La estrategia de implementación sigue pendiente: configuración, scripts, integración CI y conjunto inicial de smoke tests. La primera suite será Chromium y pocos smoke tests: carga del dashboard, inicialización de Leaflet, presencia de GeoJSON/datos, interacción departamental, filtros críticos y renderizado del gráfico principal.

Los tests deben poder interceptar la API y usar fixtures para validar el frontend sin exigir FastAPI, PostgreSQL ni fuentes externas en CI. Axe ayuda a detectar problemas automatizables, pero no reemplaza revisión manual de teclado, foco, significado sin depender del color y lector de pantalla cuando corresponda.

## Internacionalización

Se aprueba técnicamente i18n nativo de Astro dentro del stack vigente, pero se difiere su implementación: el piloto no tiene un requisito actual de más de un idioma y rutas/locales/traducciones añadirían mantenimiento prematuro. Al añadir textos nuevos, se evitará dispersarlos innecesariamente para facilitar una transición futura.

## Orden de adopción

1. `@astrojs/check`, ESLint y Prettier.
2. Fontsource y `astro-icon`.
3. Observable Plot al implementar las métricas; ColorBrewer/`chroma.js` al cerrar política visual.
4. `simple-statistics` al definir indicador, datos y naturaleza de los cortes del coroplético.
5. Playwright y `@axe-core/playwright`, comenzando con smoke tests.
6. i18n de Astro cuando exista un requisito de producto para otro idioma.

## Fuentes primarias

- [Astro: testing y Playwright](https://docs.astro.build/en/guides/testing/)
- [Astro: TypeScript y `astro check`](https://docs.astro.build/en/guides/typescript/)
- [Astro: i18n](https://docs.astro.build/en/guides/internationalization/)
- [Astro Icon](https://www.astroicon.dev/)
- [Fontsource](https://fontsource.org/docs/getting-started/introduction)
- [Observable Plot](https://observablehq.com/plot/)
- [chroma.js](https://gka.github.io/chroma.js/)
- [simple-statistics](https://simple-statistics.github.io/docs/)
- [`eslint-plugin-astro`](https://github.com/ota-meshi/eslint-plugin-astro)
- [`prettier-plugin-astro`](https://github.com/withastro/prettier-plugin-astro)
- [Playwright: accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [`@axe-core/playwright`](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright)
