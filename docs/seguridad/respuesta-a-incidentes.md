# Respuesta a incidentes de seguridad

**Estado:** Borrador (2026-10-04). Lo respalda el ADR 0024. Los pasos que dependen del sistema de cuentas (interruptor de emergencia, revocación de sesiones, retirada masiva) se vuelven ejecutables cuando se entreguen las etapas de identidad y administración; hasta entonces rige lo que el sistema actual permite, indicado en cada paso.

## Roles

- Quien coordina decide la contención y la comunicación.
- Quien comunica redacta los avisos públicos y escribe a las personas afectadas.
- Quien revisa pruebas conserva registros y verifica la cadena de auditoría.

Cada rol tiene una persona suplente. Se necesitan al menos dos personas capaces de actuar, de modo que un incidente no dependa de que una sola esté disponible.

## Detección

- Alertas de la propia plataforma: registros de la API, avisos de CI, correos de seguridad.
- Reportes externos por el contacto de `/.well-known/security.txt`.
- Una alerta publicada que alguien del equipo no reconoce, o una cuenta con actividad que su titular no hizo.

## Contención, por orden

1. Activar el interruptor de emergencia de publicación, que corta toda publicación nueva sin afectar la lectura.
2. Revocar las sesiones de la cuenta implicada.
3. Suspender la cuenta.
4. Si hay sospecha de compromiso general, rotar el secreto de sesiones, que invalida todas las sesiones, y la pimienta de contraseñas por versión.

Hasta que existan las cuentas, el equivalente es retirar la alerta con la orden de consola y rotar el secreto de escritura en Render.

## Erradicación y recuperación

- Retirar lo publicado por la persona implicada desde la fecha del incidente, con un motivo público neutro.
- Restaurar la última copia verificada si hubo daño en la base, y comprobar la cadena de auditoría después.
- Reemitir los factores de las cuentas afectadas.

## Comunicación

- Si una alerta falsa estuvo visible, el aviso de retirada con su motivo es el aviso público.
- Se avisa a las personas afectadas.
- La notificación a la autoridad o a las personas cuyos datos se expusieron sigue lo que determine el especialista legal. Este documento no fija plazos legales.

## Después

Un informe sin atribución de culpas en un plazo de 7 días, con línea de tiempo, causa raíz y cambios. Se enlaza en la Biblioteca solo si el incidente afectó a quienes leen el sitio.

## Simulacro

Una vez al año, una persona del equipo actúa como atacante con una cuenta de prueba. Se mide el tiempo hasta retirar lo publicado y revocar las sesiones, y el resultado queda en el informe del simulacro.
