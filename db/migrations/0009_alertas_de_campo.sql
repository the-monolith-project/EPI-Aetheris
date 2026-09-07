-- ============================================================================
-- EPI-Aetheris — Migración 0009
-- Respalda: ADR 0013 (tabla alertas de campo humanas)
-- Demo Expotécnica: INSERT de una alerta activa de dengue, una activa de
-- respiratorio, y una inactiva de dengue (esta última no sale en la vista
-- pública; sirve para que el filtro `activa` sea comprobable).
-- No regenera db/seed/seed_datos_reales.sql (ADR 0010).
-- ============================================================================

BEGIN;

CREATE TABLE alertas (
    id              BIGSERIAL PRIMARY KEY,
    tipo            TEXT        NOT NULL,
    nivel           TEXT        NOT NULL,
    titulo          TEXT        NOT NULL,
    contexto        TEXT        NOT NULL,
    indicaciones    TEXT        NOT NULL,
    fuente          TEXT        NOT NULL,
    autor           TEXT        NOT NULL,
    vigente_desde   DATE        NOT NULL,
    vigente_hasta   DATE,
    activa          BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT alertas_tipo_check
        CHECK (tipo IN ('dengue', 'respiratorio')),
    CONSTRAINT alertas_nivel_check
        CHECK (nivel IN ('informativo', 'atencion', 'intensificacion'))
);

COMMENT ON TABLE alertas IS
    'Alertas de campo redactadas por el equipo de vigilancia. Decisiones humanas persistidas: no se calculan desde M1–M3 ni desde el clasificador retirado. La vista pública filtra activa=TRUE. ADR 0013.';

COMMENT ON COLUMN alertas.tipo IS
    'dengue | respiratorio. Lo asigna quien emite; no se infiere del módulo.';

COMMENT ON COLUMN alertas.nivel IS
    'informativo | atencion | intensificacion. Lo asigna quien emite; no se recalcula.';

COMMENT ON COLUMN alertas.activa IS
    'Filtro principal de la vista pública. No se deriva de vigente_hasta.';

INSERT INTO alertas (
    tipo, nivel, titulo, contexto, indicaciones, fuente, autor,
    vigente_desde, vigente_hasta, activa
) VALUES
(
    'dengue',
    'atencion',
    'Casos probables de dengue por encima de años comparables en 2023',
    $alerta$Los datos históricos de 2023 (casos probables desacumulados de boletines MINSAL) muestran un volumen por encima de lo observado en las mismas semanas epidemiológicas de 2018, 2021 y 2022. 2019 sigue siendo el año de mayor volumen de la ventana cargada. Esta lectura describe lo ya publicado en fuentes públicas; no afirma lo que ocurrirá ni sustituye el criterio clínico.$alerta$,
    $alerta$En las unidades de la red, mientras esta alerta esté vigente:

- Aplicar la definición de caso sospechoso a todo paciente febril sin foco aparente; no esperar signos de alarma para notificar.
- Registrar y notificar en las primeras 24 h de la consulta.
- A todo caso probable: hemograma basal y clasificación (dengue sin signos de alarma / con signos de alarma / grave) según guía MINSAL vigente.
- Entregar hoja de signos de alarma al paciente y su acompañante; citar a control en 24-48 h durante la fase febril y al cese de la fiebre.
- Reportar al SIBASI la sospecha de aumento para que valore inspección entomológica y control de foco en la zona de residencia de los casos.
- No indicar AINE ni intramusculares en febriles sin diagnóstico.$alerta$,
    'Boletines MINSAL, casos probables desacumulados, 2018-2023 (sin 2020). Serie nacional OpenDengue (clasificacion total) como contexto. Semanas epidemiológicas de 2023 comparadas con las mismas semanas de 2018, 2021 y 2022.',
    'Equipo de vigilancia EPI-Aetheris (INSAMT, Equipo 4)',
    DATE '2026-09-01',
    NULL,
    TRUE
),
(
    'respiratorio',
    'atencion',
    'IRA y detecciones virales por encima de años comparables en 2023',
    $alerta$Los datos históricos de 2023 muestran semanas de IRA notificada y de vigilancia laboratorial nacional (influenza y VSR) por encima de la mediana de los años base 2018, 2019, 2021 y 2022. La vigilancia de virus es nacional — muestras y detecciones, no casos ni departamento. La coexistencia temporal de esas series no demuestra que un virus cause el aumento de IRA o neumonías.$alerta$,
    $alerta$En las unidades de la red, mientras esta alerta esté vigente:

- Aplicar clasificación de IRA y buscar activamente signos de dificultad respiratoria en menores de 5 años (tiraje, taquipnea, incapacidad de beber).
- Usar oximetría de pulso en todo paciente con dificultad respiratoria; documentar SatO2.
- Reforzar criterios de neumonía y de referencia según guía MINSAL vigente.
- Indicar medidas de higiene respiratoria en sala de espera (ventilación, separación de sintomáticos, mascarilla al sintomático).
- Notificar al SIBASI el incremento de consultas por IRA para valoración.$alerta$,
    'Boletines MINSAL: IRA y neumonías notificadas por departamento (2018-2023, sin 2020) y vigilancia laboratorial nacional de virus (muestras, detecciones, positividad publicada por la fuente).',
    'Equipo de vigilancia EPI-Aetheris (INSAMT, Equipo 4)',
    DATE '2026-09-01',
    NULL,
    TRUE
),
(
    'dengue',
    'informativo',
    'Vigilancia rutinaria de dengue (cerrada el 31/08/2026)',
    $alerta$Recordatorio de vigilancia rutinaria emitido y cerrado por el equipo. Permanece en la tabla como histórico; no debe aparecer en la vista pública.$alerta$,
    $alerta$- Mantener la notificación semanal de casos sospechosos a VIGEPES sin cambios.
- Verificar existencias de pruebas rápidas, acetaminofén y sales de rehidratación oral.
- Reforzar mensaje comunitario de eliminación de criaderos (recipientes, llantas, canaletas).$alerta$,
    'Boletines MINSAL, ventana 2018-2023 (sin 2020). Alerta de ensayo cerrada; no usar como vigente.',
    'Equipo de vigilancia EPI-Aetheris (INSAMT, Equipo 4)',
    DATE '2026-08-01',
    DATE '2026-08-31',
    FALSE
);

COMMIT;
