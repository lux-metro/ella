"""
test_serial.py — Script de prueba para la comunicación serial

Este script verifica si la Raspberry Pi puede leer datos del Arduino.
Es útil correrlo manualmente durante el setup para ver que todo
esté bien conectado antes de iniciar el motor de audio completo.

Uso:
  python3 test_serial.py
"""

import os
import sys
import time
import logging

# Asegurarse de que Python encuentre los módulos de pi/shared
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pi', 'shared')))

from serial_reader import LectorSerial

# Configurar logging para ver todo en consola
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def testear():
    print("=== Test de Comunicación Serial con Arduino ===")
    
    # Intentar usar el puerto UART por defecto, pero permitir probar con USB
    puertos_a_probar = ['/dev/ttyS0', '/dev/ttyUSB0', '/dev/ttyACM0']
    puerto_elegido = None
    
    for puerto in puertos_a_probar:
        if os.path.exists(puerto):
            puerto_elegido = puerto
            break
            
    if not puerto_elegido:
        print("❌ No se detectó ningún puerto serial activo (ttyS0, ttyUSB0, etc).")
        print("   Asegurate de que el puerto UART esté habilitado en raspi-config,")
        print("   o que el Arduino esté conectado por USB.")
        print("   El sistema usará el MODO SIMULADO de todas formas.")
        puerto_elegido = '/dev/ttyS0' # Valor por defecto para forzar el simulado

    print(f"Probando conexión en: {puerto_elegido}")
    
    lector = LectorSerial(puerto=puerto_elegido)
    lector.iniciar()
    
    print("\nLeyendo sensores durante 10 segundos...")
    print("Presioná Ctrl+C para interrumpir.\n")
    
    try:
        for i in range(10):
            sensores = lector.obtener_sensores()
            modo = "SIMULADO" if lector.modo_simulado else "REAL"
            
            print(f"[{modo}] Temp: {sensores['temperature']:.2f} | "
                  f"Luz: {sensores['light']:.2f}")
                  
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrumpido por el usuario.")
        
    finally:
        lector.detener()
        print("\nTest finalizado.")

if __name__ == '__main__':
    testear()
