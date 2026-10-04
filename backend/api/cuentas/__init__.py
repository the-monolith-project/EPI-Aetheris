"""Cuentas de usuario, sesiones y auditoría (ADR 0024).

Los módulos de este paquete reciben una conexión psycopg2 ya abierta y no
hacen commit: la transacción la cierra quien llama, de modo que una operación
y su registro de auditoría se confirman o se deshacen juntos.
"""
