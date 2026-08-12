#!/usr/bin/env python3
"""
escucha_radar.py

Este programa corre en la Raspberry Pi y se queda escuchando, todo el
tiempo, los mensajes que le manda el ESP32 por WiFi (protocolo UDP).

Cada vez que llega un mensaje "MOVIMIENTO", el programa empieza a subir
de a poco un número (la "intensidad"), desde 0.0 hasta 1.0. Si dejan de
llegar mensajes de movimiento, ese número empieza a bajar de a poco de
nuevo hasta 0.0.

Ese número se escribe todo el tiempo en el archivo /tmp/intensidad.txt,
que es el que después lee reproducir.sh para cambiar el volumen del
sonido.

No hace falta tocar nada para que funcione, pero podés ajustar los
tiempos de subida/bajada en la sección CONFIGURACIÓN de acá abajo.
"""

import socket
import time

# ===================== CONFIGURACIÓN =====================

PUERTO_UDP = 5005                 # tiene que ser el mismo puerto que usa el ESP32
ARCHIVO_SALIDA = "/tmp/intensidad.txt"

INTENSIDAD_MINIMA = 0.0           # intensidad cuando no hay nadie cerca
INTENSIDAD_MAXIMA = 1.0           # intensidad cuando hay movimiento

TIEMPO_SUBIDA = 2.0                # segundos que tarda en pasar de mínima a máxima
TIEMPO_BAJADA = 4.0                # segundos que tarda en volver de máxima a mínima

TIEMPO_SIN_SENAL = 2.5             # si no llega "MOVIMIENTO" en este tiempo, asumimos que no hay nadie

FRECUENCIA_ACTUALIZACION = 0.1     # cada cuánto (en segundos) actualizamos el archivo

# ============================================================


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PUERTO_UDP))
    sock.setblocking(False)

    intensidad_actual = INTENSIDAD_MINIMA
    ultimo_movimiento = 0.0

    pasos_subida = max(1, TIEMPO_SUBIDA / FRECUENCIA_ACTUALIZACION)
    pasos_bajada = max(1, TIEMPO_BAJADA / FRECUENCIA_ACTUALIZACION)
    paso_subida = (INTENSIDAD_MAXIMA - INTENSIDAD_MINIMA) / pasos_subida
    paso_bajada = (INTENSIDAD_MAXIMA - INTENSIDAD_MINIMA) / pasos_bajada

    print(f"Escuchando al ESP32 en el puerto {PUERTO_UDP}...")
    print(f"Escribiendo la intensidad en {ARCHIVO_SALIDA} cada {FRECUENCIA_ACTUALIZACION}s")

    while True:
        # Leemos todos los mensajes que hayan llegado desde la última vuelta
        while True:
            try:
                datos, direccion = sock.recvfrom(1024)
            except BlockingIOError:
                break
            mensaje = datos.decode("utf-8", errors="ignore").strip()
            if mensaje == "MOVIMIENTO":
                ultimo_movimiento = time.time()

        hay_alguien = (time.time() - ultimo_movimiento) < TIEMPO_SIN_SENAL

        if hay_alguien:
            intensidad_actual = min(INTENSIDAD_MAXIMA, intensidad_actual + paso_subida)
        else:
            intensidad_actual = max(INTENSIDAD_MINIMA, intensidad_actual - paso_bajada)

        try:
            with open(ARCHIVO_SALIDA, "w") as f:
                f.write(f"{intensidad_actual:.3f}")
        except IOError as error:
            print("No se pudo escribir el archivo de intensidad:", error)

        time.sleep(FRECUENCIA_ACTUALIZACION)


if __name__ == "__main__":
    main()
