# Indicaciones para la sección de Alertas de campo

> Archivo de trabajo **no trackeado**. Fuente de contenido para la nueva sección `/alertas`.
> Rama de implementación: `feat/alertas-campo`. Grok hace la implementación; este documento
> define qué debe decir la página y con qué encuadre.

---

## 1. Propósito de la sección

Puente entre quien analiza (nivel de vigilancia / epidemiología) y quien atiende en
terreno (médico de UCSF rural o de campo). El flujo es:

1. Una persona del equipo de vigilancia revisa los módulos de **dengue** o **respiratorio**.
2. Decide emitir una alerta y redacta indicaciones.
3. El médico de campo abre `/alertas` y ve: si hay algo activo, de qué se trata y qué hacer.

La página **no genera alertas automáticamente**. No hay clasificador en producción
(ver `docs/contexto/00-resumen.md`). Toda alerta es una decisión humana, fechada y firmada
por el equipo.

## 2. Encuadre obligatorio (va visible en la página)

- **Aviso de honestidad**, fijo en la cabecera de `/alertas`:

  > Herramienta académica en desarrollo (INSAMT, Equipo 4). Las alertas y sus indicaciones
  > las redacta manualmente el equipo de vigilancia del proyecto a partir de datos públicos
  > históricos (MINSAL, OpenDengue, Open-Meteo). **No sustituyen los lineamientos oficiales
  > del MINSAL ni el criterio clínico.** No son tiempo real. La coexistencia temporal de
  > eventos no demuestra causalidad.

- Cada alerta muestra: `tipo`, `nivel`, `título`, fecha de emisión, vigencia, **fuente**
  del dato que la motivó, y autor (iniciales o rol del equipo).
- Empty state honesto cuando no hay nada activo:
  *"No hay alertas activas. Última revisión del equipo: DD/MM/AAAA."*
- Nunca usar lenguaje de predicción ("va a haber brote"). Usar lenguaje descriptivo
  ("los datos históricos de las últimas N semanas muestran…").

## 3. Modelo de datos sugerido (`alertas`)

| campo            | tipo        | notas                                             |
|-----------------|-------------|---------------------------------------------------|
| `id`            | pk          |                                                   |
| `tipo`          | enum        | `dengue` \| `respiratorio`                         |
| `nivel`         | enum        | `informativo` \| `atencion` \| `intensificacion`  |
| `titulo`        | texto corto | una línea                                          |
| `contexto`      | markdown    | qué muestran los datos, con la fuente             |
| `indicaciones`  | markdown    | qué hacer en la unidad (lista accionable)         |
| `fuente`        | texto       | dataset + rango de semanas/años                    |
| `autor`         | texto       | rol o iniciales del equipo de vigilancia          |
| `vigente_desde` | fecha       |                                                   |
| `vigente_hasta` | fecha       | nullable                                           |
| `activa`        | bool        | filtro principal de la vista pública               |

**Creación de alertas para la Expotécnica:** inserción manual en la base / seed. No construir
autenticación ni formulario de administración en este alcance.

## 4. Niveles

| nivel             | significado                                                                 |
|-------------------|----------------------------------------------------------------------------|
| `informativo`     | Sin señal relevante en los datos. Recordatorio de vigilancia rutinaria.    |
| `atencion`        | Los datos históricos recientes están por encima de lo esperado para la época. Reforzar notificación y búsqueda de casos. |
| `intensificacion` | Señal sostenida varias semanas y/o concentración territorial. Activar medidas locales y coordinar con SIBASI. |

El nivel lo asigna el equipo al emitir; no se recalcula solo.

---

## 5. Catálogo de indicaciones

Texto base reutilizable. El equipo lo ajusta al redactar cada alerta concreta; no es
protocolo cerrado. Todo se subordina a los lineamientos vigentes del MINSAL.

### 5.1 Dengue

**Nivel `informativo`**

- Mantener la notificación semanal de casos sospechosos a VIGEPES sin cambios.
- Verificar existencias de pruebas rápidas, acetaminofén y sales de rehidratación oral.
- Reforzar mensaje comunitario de eliminación de criaderos (recipientes, llantas, canaletas).

**Nivel `atencion`**

- Aplicar la definición de caso sospechoso a todo paciente febril sin foco aparente; no
  esperar signos de alarma para notificar.
- Registrar y notificar en las primeras 24 h de la consulta.
- A todo caso probable: hemograma basal y clasificación (dengue sin signos de alarma /
  con signos de alarma / grave) según guía MINSAL vigente.
- Entregar hoja de signos de alarma al paciente y su acompañante; citar a control en 24-48 h
  durante la fase febril y al cese de la fiebre.
- Reportar al SIBASI la sospecha de aumento para que valore inspección entomológica y
  control de foco en la zona de residencia de los casos.
- No indicar AINE ni intramusculares en febriles sin diagnóstico.

**Nivel `intensificacion`**

- Priorizar triage de febriles; disponer de un área para observación e hidratación.
- Asegurar ruta de referencia definida y transporte para casos con signos de alarma o grave.
- Coordinar con SIBASI/promotor para intervención vectorial focal y comunicación de riesgo
  casa a casa en las localidades con más casos.
- Considerar búsqueda activa comunitaria de febriles con apoyo de promotores de salud.
- Consolidar el reporte de casos a diario mientras dure la alerta.

### 5.2 Respiratorio (IRA / neumonías / vigilancia de virus)

Recordatorio: la vigilancia laboratorial de virus respiratorios del proyecto es **nacional**,
por muestras y positividad, no por casos ni por departamento. Las indicaciones territoriales
se apoyan en IRA/neumonías de MINSAL.

**Nivel `informativo`**

- Mantener notificación semanal de IRA y neumonías.
- Revisar disponibilidad de oxígeno, oxímetros, broncodilatadores y antibióticos de primer nivel.
- Promover vacunación vigente (influenza y esquema según norma) en grupos de riesgo:
  menores de 5 años, embarazadas, adultos mayores, comorbilidades.

**Nivel `atencion`**

- Aplicar clasificación de IRA y buscar activamente signos de dificultad respiratoria en
  menores de 5 años (tiraje, taquipnea, incapacidad de beber).
- Usar oximetría de pulso en todo paciente con dificultad respiratoria; documentar SatO2.
- Reforzar criterios de neumonía y de referencia según guía MINSAL vigente.
- Indicar medidas de higiene respiratoria en sala de espera (ventilación, separación de
  sintomáticos, mascarilla al sintomático).
- Notificar al SIBASI el incremento de consultas por IRA para valoración.

**Nivel `intensificacion`**

- Organizar circuito diferenciado para sintomáticos respiratorios.
- Verificar cadena de oxígeno y ruta de referencia para casos con SatO2 baja o neumonía grave.
- Registro diario de consultas por IRA y neumonía mientras dure la alerta.
- Coordinar con SIBASI comunicación de riesgo y refuerzo de vacunación.
- Reportar desabastecimiento de oxígeno o insumos críticos de inmediato.

---

## 6. Enlaces cruzados en la app

- Desde la sección de **dengue** y la de **respiratorio**: enlace "¿Alerta activa? →" hacia `/alertas`
  con filtro por ese `tipo`.
- Desde cada alerta: enlace de vuelta al módulo (dengue/respiratorio) que muestra los datos
  que la motivaron, para que el médico pueda ver la serie él mismo.

## 7. Qué probar en el piloto con la médica

- ¿Identifica que hay una alerta activa y de qué tipo?
- ¿Entiende el nivel sin que se lo expliquen?
- ¿Sabe decir, con sus palabras, qué haría en su unidad?
- ¿De dónde cree que viene la alerta? ¿Quién la emitió?
- ¿Confiaría en ella para reforzar la vigilancia? ¿Qué le falta para confiar?
- Toda confusión es hallazgo para el informe, no fallo de la persona.
