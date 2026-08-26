# Indicaciones para configurar Codex y formalizar la documentación de decisiones en EPI-Aetheris

## Propósito

Este documento reúne las decisiones y criterios acordados para integrar Codex y otros agentes de programación al flujo de trabajo de EPI-Aetheris sin crear una estructura documental paralela ni duplicar conocimiento ya existente.

La idea central es:

> El conocimiento del proyecto debe pertenecer al repositorio, no a un agente específico.

ChatGPT, Codex, Claude Code u otros agentes deben consultar y respetar la documentación del proyecto, pero la fuente de verdad debe permanecer en el repositorio.

El flujo de trabajo acordado para nuevas decisiones técnicas será:

**analizar → decidir → documentar → revisar/mergear → implementar**

La documentación de una decisión debe ocurrir antes de su implementación cuando corresponda, y debe quedar claramente diferenciada del código que la materializa.

La seccion #2 y #3 de estas indicaciones no las tomes en cuenta, pues ya esta el AGENTS.md con su contenido en la raiz deel directorio.

---

# 1. Respetar la estructura documental existente

No crear una estructura nueva de documentación si la actual ya cubre la necesidad.

La organización existente debe seguir siendo la base:

```text
EPI-Aetheris/
├── CLAUDE.md
├── README.md
├── docs/
│   ├── adr/
│   │   ├── 0001-plantilla-base.md
│   │   ├── 0002-join-mapa-geojson-por-nombre.md
│   │   ├── 0003-coordenadas-regiones-columnas.md
│   │   ├── 0004-bitacora-boletines-llave-natural-y-estados.md
│   │   ├── 0005-clasificacion-total-opendengue.md
│   │   └── 0006-atribucion-fuente-climatica-era5.md
│   ├── contexto/
│   │   ├── 00-resumen.md
│   │   ├── 01-decisiones-cerradas.md
│   │   ├── 02-decisiones-abiertas.md
│   │   ├── 03-fuentes-de-datos.md
│   │   └── CHANGELOG.md
│   ├── corrida-canal-endemico-nacional.md
│   └── corrida-canal-endemico-nacional-4zonas.md
├── backend/
├── db/
└── web/
```

`docs/contexto/00-resumen.md` ya funciona como punto de entrada para un lector humano o IA.

No debe copiarse todo su contenido dentro de `AGENTS.md`.

---

# 2. Crear un AGENTS.md en la raíz

Debe agregarse un archivo:

```text
AGENTS.md
```

en la raíz del repositorio.

Su función es actuar como guía operativa para Codex y otros agentes.

No debe convertirse en una segunda documentación maestra.

Debe funcionar principalmente como:

- mapa del conocimiento;
- conjunto de reglas operativas;
- indicación de qué documentación consultar;
- definición del flujo antes de modificar código;
- protección contra contradicciones, decisiones inventadas y cambios fuera de alcance.

---

# 3. Contenido recomendado de AGENTS.md

El archivo debe cubrir, como mínimo, las siguientes reglas.

## Punto de entrada

Antes de realizar cambios relevantes, el agente debe leer:

```text
docs/contexto/00-resumen.md
```

No debe cargar por defecto toda la documentación.

Debe consultar fuentes adicionales solo cuando la tarea lo requiera.

## Fuentes de autoridad

### Contexto general

```text
docs/contexto/00-resumen.md
```

Contiene el alcance, propósito, estado y referencias hacia información más detallada.

### Decisiones cerradas

```text
docs/contexto/01-decisiones-cerradas.md
```

Contiene decisiones ya tomadas.

El agente no debe reabrirlas, sustituirlas o contradecirlas sin una instrucción explícita del equipo.

### Decisiones abiertas

```text
docs/contexto/02-decisiones-abiertas.md
```

Contiene puntos que todavía requieren evidencia, validación o decisión.

El agente no debe convertir una hipótesis en una decisión oficial.

Si una tarea depende de una decisión abierta, debe identificar la dependencia y la información faltante.

### Fuentes de datos

```text
docs/contexto/03-fuentes-de-datos.md
```

Debe consultarse antes de modificar o reinterpretar:

- ingestión;
- variables climáticas;
- MINSAL;
- OpenDengue;
- Open-Meteo;
- agregaciones;
- datos faltantes;
- semanas epidemiológicas;
- transformaciones de datos.

### Historial

```text
docs/contexto/CHANGELOG.md
```

Debe utilizarse cuando sea necesario entender:

- por qué existe un comportamiento;
- qué ocurrió en una sesión anterior;
- cuándo cambió una decisión;
- qué experimentos llevaron al estado actual.

No debe leerse completo por defecto.

### ADR

```text
docs/adr/
```

Los ADR aceptados representan decisiones arquitectónicas formales.

La plantilla existente es:

```text
docs/adr/0001-plantilla-base.md
```

---

# 4. Precedencia de información

Cuando distintas fuentes parezcan entrar en conflicto, el agente debe usar esta jerarquía como guía:

1. ADR aceptado aplicable.
2. `docs/contexto/01-decisiones-cerradas.md`.
3. estado vigente de `docs/contexto/00-resumen.md`.
4. evidencia especializada de `docs/contexto/03-fuentes-de-datos.md`.
5. código y configuración actualmente presentes en `main`.
6. `docs/contexto/CHANGELOG.md`.
7. documentación histórica, comentarios antiguos o experimentos.

Si la contradicción no puede resolverse, debe reportarse.

No debe modificarse silenciosamente una fuente para que coincida con otra.

---

# 5. Reglas no negociables para agentes

El `AGENTS.md` debe recordar las restricciones principales del proyecto.

## Datos

- Utilizar únicamente datos reales, públicos y agregados.
- No fabricar datasets.
- No simular datos epidemiológicos para hacer funcionar una demo.
- No rellenar datos ausentes con supuestos no aprobados.
- No interpretar ausencia como cero salvo que la fuente lo establezca explícitamente.
- Mantener trazabilidad y procedencia.

## Interpretación epidemiológica

EPI-Aetheris es una herramienta de apoyo para estimar y comunicar riesgo.

No debe presentarse como:

- diagnóstico;
- certeza clínica;
- predicción infalible;
- recomendación médica;
- descubrimiento epidemiológico novedoso.

El aporte principal es de ingeniería de software, reproducibilidad, integración y acceso abierto.

## Costos y dependencias

Antes de introducir una dependencia:

1. comprobar si ya existe una herramienta equivalente;
2. revisar decisiones cerradas;
3. justificar la necesidad;
4. evaluar mantenimiento, licencia, tamaño y complejidad;
5. evitar servicios de pago, freemium obligatorio o suscripciones necesarias para el core.

## Privacidad

No introducir datos personales.

## Reproducibilidad

Docker forma parte del funcionamiento esperado.

Una solución que solo funciona en la máquina local no se considera completa.

---

# 6. Arquitectura que el agente debe respetar

La arquitectura general actual se basa en:

- PostgreSQL;
- FastAPI/Python en `backend/`;
- Astro + TypeScript en `web/`;
- Leaflet;
- Docker Compose.

No deben introducirse frameworks, ORMs, bases de datos, plataformas o arquitecturas principales alternativas sin comprobar decisiones existentes.

En frontend, no introducir React o Vue salvo una decisión explícita del equipo.

---

# 7. Regla específica para base de datos

Antes de modificar el esquema:

1. revisar ADR existentes;
2. revisar el esquema vigente;
3. identificar dependencias en backend e ingestión;
4. comprobar migraciones;
5. confirmar que existe un ADR aceptado cuando el cambio sea estructural.

Cambios como:

- tablas;
- columnas;
- restricciones;
- relaciones;
- `CHECK`;
- valores controlados a nivel de esquema;

requieren ADR previo según la regla ya adoptada por el proyecto.

No debe escribirse primero la migración para documentarla después.

---

# 8. Forma de trabajo esperada de Codex

Para tareas de implementación, el flujo por defecto debe ser:

**analizar → proponer → implementar → validar → revisar diff**

## Analizar

Antes de cambiar archivos:

- revisar el estado actual;
- inspeccionar archivos relacionados;
- leer documentación aplicable;
- comprobar decisiones cerradas y abiertas.

## Proponer

Cuando la tarea implique una decisión técnica no trivial:

- explicar brevemente el enfoque;
- identificar archivos afectados;
- señalar riesgos y trade-offs.

## Implementar

Realizar el cambio mínimo necesario.

Evitar:

- refactors no solicitados;
- cambios cosméticos masivos;
- dependencias no justificadas;
- renombrados innecesarios;
- tocar archivos ajenos al alcance.

## Validar

Después de implementar:

- ejecutar tests relevantes;
- ejecutar typecheck/lint cuando existan;
- comprobar el comportamiento relacionado;
- declarar cualquier validación que no se haya podido ejecutar.

## Revisar diff

Antes de considerar terminada una tarea:

- inspeccionar el diff;
- comprobar que no haya archivos accidentales;
- identificar cambios no relacionados;
- resumir lo modificado y lo pendiente.

---

# 9. Diferenciar análisis de modificación

Si el usuario solicita:

- revisar;
- analizar;
- investigar;
- comparar;
- auditar;
- explicar;
- evaluar un PR;

el agente no debe modificar archivos automáticamente.

Primero debe entregar hallazgos.

La implementación debe ocurrir cuando se solicite explícitamente corregir, modificar, implementar o equivalente.

---

# 10. Git

El agente debe:

- revisar `git status` antes de modificar;
- no sobrescribir trabajo ajeno;
- no descartar cambios locales que no haya creado;
- no usar comandos destructivos para “limpiar” el árbol sin autorización;
- no hacer commit, push, merge, rebase o force push salvo instrucción explícita.

Al revisar un PR debe distinguir entre:

- estado de `main`;
- rama del PR;
- diff;
- resultado después del merge.

---

# 11. CLAUDE.md

`CLAUDE.md` debe conservarse.

Actualmente contiene mucho conocimiento útil y restricciones del proyecto.

Sin embargo, debe evitarse duplicar nueva información de manera permanente entre:

```text
CLAUDE.md
AGENTS.md
docs/
```

La dirección deseada es:

```text
docs/ = conocimiento neutral del proyecto
AGENTS.md = instrucciones para agentes
CLAUDE.md = instrucciones/contexto específico de Claude cuando sea necesario
```

Cuando una información sea permanente y relevante para todo el equipo o todos los agentes, debe quedar en `docs/`.

---

# 12. Cómo documentar futuras decisiones

A partir de ahora debe distinguirse entre:

- decisión arquitectónica;
- decisión técnica de stack/tooling;
- decisión pendiente;
- evidencia/experimento;
- implementación.

## Decisión arquitectónica

Si cambia arquitectura, estructura o establece una restricción difícil de revertir:

```text
docs/adr/
```

Ejemplos:

- cambio importante de arquitectura;
- cambio de motor geoespacial;
- cambio de API REST a GraphQL;
- cambios de esquema de base de datos;
- cambio importante de estrategia de clasificación;
- cambio del modelo de despliegue.

## Decisión técnica de stack o tooling

Si es una herramienta o librería dentro de una arquitectura ya aceptada:

```text
docs/contexto/01-decisiones-cerradas.md
```

Ejemplos:

- librería de iconos;
- formatter;
- linter;
- librería de visualización;
- herramienta E2E;
- auditoría de accesibilidad.

No toda dependencia necesita ADR.

## Decisión pendiente

```text
docs/contexto/02-decisiones-abiertas.md
```

Debe usarse si todavía falta evidencia, validación o una decisión del equipo.

## Evidencia o comportamiento de fuentes

```text
docs/contexto/03-fuentes-de-datos.md
```

## Historial

```text
docs/contexto/CHANGELOG.md
```

El changelog debe registrar que una decisión ocurrió, pero no duplicar toda su justificación.

---

# 13. Diferenciar decisión de implementación

Toda decisión tecnológica debe indicar, cuando sea útil:

```text
Decisión: aprobada
Implementación: pendiente
```

Esto evita que un agente interprete:

> “aprobado”

como:

> “instalar inmediatamente”.

También deben permitirse estados condicionados.

Ejemplo:

```text
Decisión: aprobada condicionalmente
Implementación: pendiente
Condición: solo aplicar si entra en alcance el mapa departamental
```

---

# 14. Decisiones del stack frontend ya aprobadas

Las siguientes decisiones ya fueron discutidas y aprobadas y deben quedar documentadas formalmente.

## 14.1 Iconografía — astro-icon + Iconify

**Decisión:** aprobada.  
**Implementación:** pendiente.

Utilizar:

```text
astro-icon
Iconify
Lucide / Tabler
```

Motivos:

- actualmente no existe un sistema de iconografía consolidado;
- genera SVG inline durante build;
- evita runtime JS adicional para iconos;
- encaja con Astro;
- no introduce React/Vue;
- permite mantener una iconografía consistente.

No introducir otra librería de iconos salvo que esta solución demuestre una limitación concreta.

---

## 14.2 Fuentes auto-hospedadas — Fontsource

**Decisión:** aprobada.  
**Implementación:** pendiente.

Utilizar:

```text
@fontsource/inter
@fontsource/ibm-plex-mono
```

Objetivo:

sustituir la dependencia actual de Google Fonts vía CDN en `Layout.astro`.

Motivos:

- eliminar dependencia de red externa;
- mejorar reproducibilidad;
- permitir funcionamiento self-hosted;
- mantener coherencia con el principio de costo y dependencia externa mínimos.

---

## 14.3 Observable Plot

**Decisión:** aprobada.  
**Implementación:** pendiente.

Usar Observable Plot para visualizaciones estadísticas como:

```text
MetricasModelo.astro
```

Casos previstos:

- matriz de confusión;
- margen de error;
- métricas del modelo;
- visualizaciones estadísticas que actualmente requerirían SVG manual creciente.

Motivo principal:

evitar extender indefinidamente SVG escritos a mano cuando una librería declarativa de visualización estadística cubre mejor el caso.

---

## 14.4 Paleta accesible para niveles de riesgo

**Decisión:** aprobada.  
**Implementación:** pendiente.

Utilizar una paleta accesible para:

```text
alto
medio
bajo
```

Herramientas consideradas/aprobadas para construir o validar la paleta:

```text
chroma.js
escalas ColorBrewer
```

Debe priorizarse:

- contraste;
- legibilidad;
- seguridad para daltonismo;
- consistencia con `tokens.css`.

La elección concreta de escala debe verificarse visualmente y con criterios de accesibilidad.

---

## 14.5 simple-statistics

**Decisión:** aprobada condicionalmente.  
**Implementación:** pendiente.

Uso previsto:

- Jenks;
- cuantiles;
- cortes estadísticos para un futuro mapa coroplético departamental.

Condición:

su incorporación efectiva está condicionada a que el componente departamental entre realmente en implementación después del reconteo pendiente de MINSAL.

No instalar `simple-statistics` únicamente porque la herramienta haya sido aprobada.

Primero debe cumplirse la necesidad funcional.

---

## 14.6 ESLint + Prettier

**Decisión:** aprobada.  
**Implementación:** pendiente.

Utilizar:

```text
eslint
eslint-plugin-astro
prettier
prettier-plugin-astro
```

Situación actual:

el frontend no dispone de un sistema formal de linting/formatting.

Objetivo:

- consistencia;
- detección temprana de problemas;
- reducir diferencias de estilo entre integrantes;
- preparar validaciones automatizadas.

---

## 14.7 @astrojs/check

**Decisión:** aprobada.  
**Implementación:** pendiente.

Incorporar:

```text
@astrojs/check
```

Objetivo:

type-check de archivos `.astro`.

Debe integrarse de manera coherente con el pipeline de validación/build.

Actualmente no está presente en `package.json`.

---

## 14.8 Playwright

**Decisión:** aprobada.  
**Implementación:** pendiente.

Usar Playwright para pruebas end-to-end del frontend.

Casos prioritarios:

- mapa Leaflet;
- interacción del dashboard;
- visualizaciones;
- flujos críticos;
- renderizado de componentes dependientes del navegador.

Actualmente el frontend no dispone de suite E2E.

La incorporación de Playwright no implica automáticamente que todos los tests deban ejecutarse en cada push; la estrategia exacta de CI puede definirse durante la implementación.

---

## 14.9 axe-core

**Decisión:** aprobada.  
**Implementación:** pendiente.

Usar axe-core para auditoría de accesibilidad.

Objetivos:

- contraste;
- ARIA;
- semántica;
- problemas detectables automáticamente en el dashboard.

Debe integrarse con el flujo de pruebas de frontend cuando corresponda.

---

## 14.10 i18n nativo de Astro

**Decisión:** aprobada.  
**Implementación:** pendiente.

Utilizar la capacidad nativa de internacionalización de Astro en lugar de introducir una librería externa sin necesidad.

Objetivo:

dejar la estructura del contenido preparada para más de un idioma.

Motivos:

- soporte nativo;
- menor dependencia;
- coherencia con la arquitectura;
- alineación conceptual con el diseño agnóstico del proyecto, donde `tipos_evento` y `regiones` funcionan como catálogos extensibles.

No es necesario traducir todo el producto inmediatamente.

La primera implementación puede limitarse a preparar correctamente la estructura.

---

# 15. Cómo registrar estas decisiones

Estas decisiones pertenecen principalmente a:

```text
docs/contexto/01-decisiones-cerradas.md
```

Se recomienda crear una sección similar a:

```text
## Stack frontend — extensiones aprobadas 2026-08-12
```

No crear un ADR individual por cada herramienta.

Debe diferenciarse claramente:

```text
Decisión
Implementación
Condiciones
Motivo
```

cuando corresponda.

---

# 16. Actualización del CHANGELOG

Debe registrarse de forma breve el cierre de la evaluación del stack frontend.

No duplicar toda la argumentación.

Una entrada conceptual podría indicar:

- cierre de evaluación de gaps/tooling del frontend;
- tecnologías aprobadas;
- `simple-statistics` aprobado condicionalmente;
- implementación todavía pendiente.

El changelog debe responder:

> qué ocurrió y cuándo

mientras `01-decisiones-cerradas.md` responde:

> qué se decidió y qué significa.

---

# 17. Separar documentación e implementación

La incorporación de estas decisiones a la documentación no debe mezclarse con la implementación de las herramientas.

La secuencia deseada es:

```text
Decisiones documentadas
        ↓
revisión
        ↓
merge
        ↓
implementación por tareas pequeñas
```

La implementación posterior puede dividirse en cambios manejables, por ejemplo:

```text
iconografía
fuentes
lint/format
type-check
visualizaciones
accesibilidad
tests E2E
i18n
```

No instalar todo el stack de golpe sin necesidad.

---

# 18. Flujo futuro cuando aparezca una nueva decisión

Cuando durante una conversación se llegue a una conclusión técnica explícita, debe seguirse este proceso.

## Paso 1 — Analizar

Comparar alternativas, restricciones, mantenimiento, compatibilidad y necesidad real.

## Paso 2 — Decidir

Debe existir una señal clara de cierre, por ejemplo:

```text
aprobado
cerrado
se adopta
descartado
aprobado condicionalmente
```

Una preferencia provisional no debe tratarse como decisión oficial.

## Paso 3 — Clasificar

Preguntar:

```text
¿Es arquitectónica?
¿Es stack/tooling?
¿Sigue abierta?
¿Es evidencia?
```

y llevarla al archivo correspondiente.

## Paso 4 — Documentar

Registrar:

- contexto;
- decisión;
- motivos;
- consecuencias;
- condición, si existe;
- estado de implementación.

## Paso 5 — Revisar

La documentación debe poder revisarse igual que el código.

## Paso 6 — Implementar

Solo después, cuando corresponda.

---

# 19. Regla práctica para decidir si algo merece ADR

Usar ADR cuando una decisión:

- cambia arquitectura;
- cambia estructura persistente;
- afecta múltiples componentes;
- establece una restricción importante;
- es difícil o costosa de revertir;
- modifica esquema de base de datos.

Ejemplos que sí pueden justificar ADR:

```text
Leaflet → MapLibre
REST → GraphQL
cambio del esquema
cambio de estrategia de clasificación
cambio de modelo de despliegue
```

Ejemplos que normalmente no requieren ADR:

```text
astro-icon
Fontsource
Prettier
ESLint
@astrojs/check
axe-core
```

---

# 20. Comportamiento esperado de Codex después de esta configuración

Ejemplo:

```text
Usuario:
"Implementa iconografía en el frontend."
```

Codex debería:

```text
leer AGENTS.md
↓
leer docs/contexto/00-resumen.md
↓
detectar que es una decisión de stack
↓
consultar docs/contexto/01-decisiones-cerradas.md
↓
encontrar astro-icon + Iconify aprobado
↓
implementar esa solución
```

Otro ejemplo:

```text
Usuario:
"Implementa Jenks para el mapa departamental."
```

Codex debería detectar que:

```text
simple-statistics
= aprobado condicionalmente
```

y verificar primero si la condición que habilita el mapa departamental ya se cumplió.

---

# 21. Principio general

No se busca que Codex memorice todo el proyecto en un único prompt.

Se busca que sepa:

```text
dónde mirar
qué respetar
qué no inventar
cuándo detenerse
cómo validar
```

La arquitectura de conocimiento deseada es:

```text
                    docs/
              fuente de verdad
                    │
         ┌──────────┴──────────┐
         │                     │
     AGENTS.md              CLAUDE.md
       Codex                 Claude
         │                     │
         └────── repositorio ──┘
```

ChatGPT puede utilizarse para analizar y decidir.

Codex puede utilizarse para inspeccionar, implementar, probar y revisar cambios.

Git y la documentación del repositorio funcionan como puente entre ambos.

---

# 22. Resultado deseado

Después de aplicar estas indicaciones, EPI-Aetheris debería contar con:

```text
EPI-Aetheris/
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── docs/
│   ├── adr/
│   ├── contexto/
│   │   ├── 00-resumen.md
│   │   ├── 01-decisiones-cerradas.md
│   │   ├── 02-decisiones-abiertas.md
│   │   ├── 03-fuentes-de-datos.md
│   │   └── CHANGELOG.md
│   └── ...
├── backend/
├── db/
└── web/
```

con una separación clara entre:

```text
conocimiento permanente → docs/
instrucciones de agentes → AGENTS.md / CLAUDE.md
decisiones arquitectónicas → docs/adr/
decisiones cerradas de stack → 01-decisiones-cerradas.md
pendientes → 02-decisiones-abiertas.md
evidencia de datos → 03-fuentes-de-datos.md
historial → CHANGELOG.md
implementación → código
```

El objetivo final es que cualquier agente pueda incorporarse al proyecto sin depender de contexto escondido en un chat y sin contradecir las decisiones ya tomadas por el equipo.
