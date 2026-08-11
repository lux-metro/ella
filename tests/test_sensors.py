"""
test_sensors.py — Script para validar los datos que llegan de los sensores

Este script se enfoca exclusivamente en imprimir continuamente los
valores normalizados de los sensores (temperatura, luz).
Útil para calibración física (ej: tapar el sensor de luz y ver si cambia).

Uso:
  python3 test_sensors.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pi', 'shared')))
from serial_reader import LectorSerial

def barra(valor, longitud=20):
    """Genera una barra de texto [====    ] para visualizar mejor el valor"""
    llenar = int(valor * longitud)
    return f"[{'=' * llenar}{' ' * (longitud - llenar)}]"

def testear():
    print("=== Monitor de Sensores en Tiempo Real ===")
    print("Moviendo la mano sobre el sensor de luz o cambiando la")
    print("temperatura debería verse reflejado inmediatamente acá.")
    print("-" * 50)
    
    # Intentar varios puertos
    puertos = ['/dev/ttyS0', '/dev/ttyUSB0', '/dev/ttyACM0']
    puerto_elegido = '/dev/ttyS0'
    for p in puertos:
        if os.path.exists(p):
            puerto_elegido = p
            break
            
    lector = LectorSerial(puerto=puerto_elegido)
    lector.iniciar()
    
    time.sleep(1) # Dejar que conecte
    
    modo = "SIMULADO (Arduino no detectado)" if lector.modo_simulado else f"REAL ({puerto_elegido})"
    print(f"Modo: {modo}")
    print("Presioná Ctrl+C para salir.\n")
    
    try:
        while True:
            sensores = lector.obtener_sensores()
            
            t = sensores['temperature']
            l = sensores['light']
            
            # Imprimir con carriage return (\r) para sobreescribir la misma línea
            linea = (
                f"\rTem: {t:.2f} {barra(t)} | "
                f"Luz: {l:.2f} {barra(l)}"
            )
            # Imprimir al final para forzar la actualización de la pantalla
            sys.stdout.write(linea)
            sys.stdout.flush()
            
            time.sleep(0.1) # Refresco rápido para la terminal
            
    except KeyboardInterrupt:
        print("\n\nSaliendo...")
        
    finally:
        lector.detener()

if __name__ == '__main__':
    testear()
