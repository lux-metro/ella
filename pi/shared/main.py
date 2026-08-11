"""
main.py — Punto de entrada principal de *ella*

Este es el script que arranca el sistema completo.
Es lo que systemd ejecuta cuando enciende la Raspberry Pi.

Qué hace:
  1. Carga la configuración del dispositivo (¿soy Voz A o Voz B?)
  2. Inicia el lector de sensores del Arduino (en hilo separado)
  3. Inicia el motor de audio (en hilo principal)
  4. Si algo falla, lo registra y permite que systemd reinicie el servicio

Para correr manualmente (para testear):
  cd ~/ella/repo
  .venv/bin/python pi/shared/main.py

Para ver los logs cuando corre como servicio:
  journalctl --user -u reproducir -f
"""

import logging
import signal
import sys
import time
import os

# Asegurarse de que Python encuentre los módulos del proyecto
# (necesario tanto para ejecución manual como para systemd)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import cargar_config
from serial_reader import LectorSerial
from audio_engine import MotorDeAudio


# =============================================================
# Configuración del sistema de logs
# =============================================================
# Los logs se mandan a stdout, que systemd captura automáticamente.
# Para verlos: journalctl --user -u reproducir -f

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('ella')


# =============================================================
# Manejo de señales de sistema (para apagado limpio)
# =============================================================
_motor = None
_lector = None

def manejar_señal_salida(signum, frame):
    """
    Se llama cuando el sistema le pide al proceso que termine.
    (SIGTERM es lo que manda systemd al detener el servicio)
    """
    logger.info(f"Señal de salida recibida (señal {signum}). Cerrando limpiamente...")
    if _motor:
        _motor.detener()
    if _lector:
        _lector.detener()
    sys.exit(0)

signal.signal(signal.SIGTERM, manejar_señal_salida)
signal.signal(signal.SIGINT, manejar_señal_salida)


# =============================================================
# Función principal
# =============================================================
def main():
    global _motor, _lector

    logger.info("=" * 50)
    logger.info("ella — instalación sonora")
    logger.info("Iniciando sistema...")
    logger.info("=" * 50)

    # Paso 1: Cargar configuración del dispositivo
    try:
        config = cargar_config()
        logger.info(f"Dispositivo: Voz {config['voz'].upper()}")
    except SystemExit:
        logger.error("No se pudo cargar la configuración. Abortando.")
        sys.exit(1)

    # Paso 2: Iniciar lector de sensores
    # Si el Arduino no está conectado, el lector usa modo simulado automáticamente.
    puerto_serial = config.get('puerto_serial', '/dev/ttyS0')
    baudrate = config.get('baudrate', 9600)

    _lector = LectorSerial(puerto=puerto_serial, baudrate=baudrate)
    _lector.iniciar()

    # Pequeña pausa para que el lector se establezca
    time.sleep(2)
    logger.info(
        f"Lector serial: {'modo simulado' if _lector.modo_simulado else 'conectado al Arduino'}"
    )

    # Paso 3: Iniciar motor de audio
    # Esta llamada BLOQUEA hasta que se detiene el motor.
    _motor = MotorDeAudio(config=config, lector_serial=_lector)

    logger.info("Sistema listo. Iniciando reproducción...")
    _motor.iniciar()  # ← Bloquea acá hasta que se llame detener()

    # Si llegamos acá, el motor se detuvo normalmente
    logger.info("Motor de audio detenido. Cerrando programa.")
    _lector.detener()


if __name__ == '__main__':
    main()
