-- ============================================================================
-- EPI-Aetheris — Migración 0011
-- Respalda: ADR 0015 (alertas operables: etiquetas y contenido clínico citado)
--
-- Agrega alertas.etiqueta (NULL | test | simulacro | historica). NULL es el
-- caso normal de producción; cualquier valor no nulo queda fuera del GET
-- público por defecto.
--
-- Llena los cinco campos clínicos (ADR 0014) con transcripción de documentos
-- públicos, keyeada por tipo (no por id): dengue recibe definición, signos,
-- criterios OPS y qué notificar; respiratorio recibe definición y qué
-- notificar; signos_alarma y criterios_referencia de respiratorio quedan
-- NULL (VIGEPES no es guía de manejo). contacto_vigilancia es la ruta
-- SIBASI/VIGEPES-01, sin teléfono ni correo.
--
-- No regenera db/seed/seed_datos_reales.sql (ADR 0010).
-- ============================================================================

BEGIN;

ALTER TABLE alertas
    ADD COLUMN etiqueta TEXT;

ALTER TABLE alertas
    ADD CONSTRAINT alertas_etiqueta_check
        CHECK (
            etiqueta IS NULL
            OR etiqueta IN ('test', 'simulacro', 'historica')
        );

COMMENT ON COLUMN alertas.etiqueta IS
    'NULL = alerta de producción (caso normal). test | simulacro | historica quedan fuera del GET público salvo incluir_etiquetadas=true. ADR 0015.';

UPDATE alertas SET
    definicion_caso = $dengue_def$Dengue sin signos de alarma. Toda persona que presente fiebre de 2 a 7 días de evolución y 2 o más de los 5 criterios siguientes: Criterio 1. Cefalea y dolor retro ocular. Criterio 2. Exantema. Criterio 3. Mialgias y artralgias. Criterio 4. Sangrado de mucosas. Criterio 5. Conteo de glóbulos blancos menor de 5,000 por mm3.

Dengue con signos de alarma. Caso sospechoso de dengue sin signos de alarma que presente uno o más de los hallazgos listados en "signos de alarma".

Fuente: MINSAL, Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024), secciones 33 y 34.$dengue_def$,
    signos_alarma = $dengue_sa$- Dolor abdominal intenso y sostenido o dolor a la palpación del abdomen.
- Vómitos persistentes.
- Acumulación de líquidos.
- Sangrado espontáneo.
- Letargo o inquietud.
- Hepatomegalia mayor a dos centímetros bajo el reborde costal.
- Incremento del hematocrito y plaquetopenia (ambas condiciones deben estar presentes al mismo tiempo).

Fuente: MINSAL, Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024), sección 34.$dengue_sa$,
    criterios_referencia = $dengue_cr$Se sugiere hospitalizar aquellos pacientes que presenten dengue más cualquiera de lo siguiente:
- Dengue con signos de alarma
- Dengue grave
- Intolerancia a la vía oral
- Dificultad respiratoria
- Acortamiento de la presión de pulso
- Prolongación de llenado capilar (mayor de 2 segundos)
- Hipotensión arterial
- Insuficiencia renal aguda
- Embarazo
- Coagulopatía

Consideraciones adicionales: otros factores que pueden determinar la necesidad de hospitalización incluyen la presencia de comorbilidades, los extremos de la vida y condiciones sociales y/o ambientales. La decisión de admitir pacientes con las mencionadas condiciones deberá individualizarse.

Fuente: OPS/OMS, Algoritmos para el Manejo Clínico de los Casos de Dengue (junio 2020), p. 10. Estos criterios provienen de una revisión sistemática y metaanálisis de 2019 (217 estudios, 237.191 pacientes).$dengue_cr$,
    que_notificar = $dengue_qn$Notificación individual e inmediata al sistema VIGEPES, en los tres casos:
- Caso sospechoso de dengue sin signos de alarma.
- Caso sospechoso de dengue con signos de alarma.
- Caso sospechoso de dengue grave.

Se usa el formulario de notificación individual VIGEPES-01. La estrategia de confirmación es de laboratorio.

Fuente: MINSAL, Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024), Tabla 1 (p. 18) y secciones 33 a 35. Formulario VIGEPES-01 según [ARBO], Anexo 5.$dengue_qn$,
    contacto_vigilancia = $contacto$Notificación al SIBASI correspondiente mediante el formulario VIGEPES-01 (notificación individual de enfermedades objetivo de vigilancia sanitaria). La consolidación semanal la realiza la UVET/UVETV, que revisa y aprueba el boletín epidemiológico semanal.

Fuente: MINSAL, Procedimiento para vigilancia y control de arbovirosis (M02-VS-DISAM-PRO-42, Acuerdo Ejecutivo 2771, 28-10-2025), Anexo 5 y sección de responsabilidades.$contacto$
WHERE tipo = 'dengue';

UPDATE alertas SET
    definicion_caso = $resp_def$Neumonías (incluye bronconeumonía). Caso confirmado por clínica: enfermedad respiratoria aguda febril con tos productiva, dificultad respiratoria, taquipnea y dos o más de los siguientes signos: limitación de la entrada de aire, matidez y estertores crepitantes (estertores finos al final de la inspiración), o que muestre por estudio radiológico infiltrado lobar o segmentario y/o derrame pleural.

Caso confirmado con aislamiento etiológico: caso clínico con detección de virus respiratorios a través del hisopado nasofaríngeo y aislamiento etiológico de bacteria en secreciones bronquiales, derrame pleural y en hemocultivo.

Fuente: MINSAL, Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024), sección 32.$resp_def$,
    que_notificar = $resp_qn$- Neumonías (incluye bronconeumonía): caso confirmado, notificación individual e inmediata. Confirmación clínica o de laboratorio.
- Infecciones respiratorias agudas de vías superiores (IRAS): caso confirmado, notificación agrupada y semanal. Confirmación clínica.
- Infección respiratoria aguda inusitada (IRAGI): caso sospechoso, notificación individual e inmediata. Confirmación de laboratorio.

Fuente: MINSAL, Lineamientos técnicos VIGEPES (Acuerdo Ejecutivo 1300, 03-12-2024), Tabla 1, p. 18.$resp_qn$,
    signos_alarma = NULL,
    criterios_referencia = NULL,
    contacto_vigilancia = $contacto$Notificación al SIBASI correspondiente mediante el formulario VIGEPES-01 (notificación individual de enfermedades objetivo de vigilancia sanitaria). La consolidación semanal la realiza la UVET/UVETV, que revisa y aprueba el boletín epidemiológico semanal.

Fuente: MINSAL, Procedimiento para vigilancia y control de arbovirosis (M02-VS-DISAM-PRO-42, Acuerdo Ejecutivo 2771, 28-10-2025), Anexo 5 y sección de responsabilidades.$contacto$
WHERE tipo = 'respiratorio';

COMMIT;
