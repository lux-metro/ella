"""
serial_reader.py — Lee datos del Arduino por comunicación serial

Este módulo corre en un hilo separado (en paralelo con el audio)
y actualiza continuamente los valores de los sensores.

Tiene un MODO SIMULADO: si el Arduino no está conectado,
genera valores aleatorios que cambian lentamente. Así podés
trabajar y testear el audio sin necesitar el hardware.

Uso:
    from serial_reader import LectorSerial
    lector = LectorSerial(puerto='/dev/ttyS0', baudrate=9600)
    lector.iniciar()

    # En cualquier momento:
    sensores = lector.obtener_sensores()
    print(sensores['humidity'])  # → 0.65 (normalizado entre 0.0 y 1.0)

    lector.detener()
"""

import json
import logging
import math
import random
import threading
import time

logger = logging.getLogger(__name__)


class LectorSerial:
    """
    Lee datos de sensores del Arduino por puerto serial.

    Los valores se normalizan automáticamente al rango 0.0-1.0
    para que el motor de audio no necesite saber nada sobre
    los valores crudos del hardware.

    Si el Arduino no está conectado, corre en modo simulado.
    """

    def __init__(self, puerto: str, baudrate: int = 9600):
        """
        Args:
            puerto:   Ruta al puerto serial. Ej: '/dev/ttyS0' o '/dev/ttyUSB0'
            baudrate: Velocidad de comunicación. Tiene que coincidir con
                      el valor en config.h del Arduino. Por defecto: 9600.
        """
        self.puerto = puerto
        self.baudrate = baudrate
        self.modo_simulado = False

        # Valores actuales de los sensores, normalizados entre 0.0 y 1.0
        # Estos valores se actualizan continuamente desde el hilo de lectura
        self._sensores = {
            'humidity': 0.5,      # Humedad de la arcilla
            'temperature': 0.5,   # Temperatura ambiente
            'light': 0.5,         # Luz ambiental
        }

        # Lock para acceso thread-safe a _sensores
        # (evita que el hilo de audio lea mientras el hilo serial escribe)
        self._lock = threading.Lock()

        # Control del hilo de lectura
        self._corriendo = False
        self._hilo = None

    def iniciar(self):
        """Inicia la lectura de sensores en un hilo de fondo."""
        self._corriendo = True
        self._hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
        self._hilo.start()
        logger.info(f"LectorSerial iniciado. Puerto: {self.puerto}")

    def detener(self):
        """Detiene la lectura de sensores."""
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=3)
        logger.info("LectorSerial detenido.")

    def obtener_sensores(self) -> dict:
        """
        Retorna una copia de los valores actuales de los sensores.

        Los valores son floats entre 0.0 y 1.0.

        Retorna:
            dict con claves 'humidity', 'temperature', 'light'
        """
        with self._lock:
            return dict(self._sensores)

    def _bucle_lectura(self):
        """
        Hilo principal de lectura. Se ejecuta en paralelo con el audio.
        Intenta conectarse al Arduino; si falla, usa modo simulado.
        """
        # Intentar importar pyserial
        try:
            import serial
            tiene_serial = True
        except ImportError:
            logger.warning("pyserial no está instalado. Activando modo simulado.")
            tiene_serial = False

        if tiene_serial:
            self._bucle_serial()
        else:
            self._bucle_simulado()

    def _bucle_serial(self):
        """Lee datos reales del Arduino por puerto serial."""
        import serial

        while self._corriendo:
            try:
                logger.info(f"Conectando al Arduino en {self.puerto}...")
                with serial.Serial(self.puerto, self.baudrate, timeout=2) as ser:
                    self.modo_simulado = False
                    logger.info(f"Conectado al Arduino. Modo: REAL")

                    while self._corriendo:
                        linea = ser.readline().decode('utf-8', errors='ignore').strip()
                        if linea:
                            self._procesar_linea(linea)

            except serial.SerialException as e:
                logger.warning(
                    f"No se pudo conectar al Arduino ({e}). "
                    f"Activando modo simulado. Reintentando en 10 segundos..."
                )
                self.modo_simulado = True
                self._bucle_simulado(duracion_segundos=10)

    def _procesar_linea(self, linea: str):
        """Parsea una línea JSON del Arduino y actualiza los sensores."""
        try:
            datos = json.loads(linea)

            # Verificar que el Arduino esté funcionando bien
            if not datos.get('ok', False):
                logger.warning(f"Arduino reportó estado no-OK: {linea}")
                return

            # Normalizar valores crudos (0-1023) a rango 0.0-1.0
            with self._lock:
                if 'humidity' in datos:
                    self._sensores['humidity'] = datos['humidity'] / 1023.0

                if 'temperature' in datos:
                    # Temperatura: interpretamos 0-400 (0-40°C) como 0.0-1.0
                    temp_celsius = datos['temperature'] / 10.0
                    self._sensores['temperature'] = min(max(temp_celsius / 40.0, 0.0), 1.0)

                if 'light' in datos:
                    self._sensores['light'] = datos['light'] / 1023.0

        except json.JSONDecodeError:
            # Ignorar líneas que no son JSON válido (por ej: mensajes de inicio)
            if linea and not linea.startswith('{'):
                logger.debug(f"Línea no-JSON del Arduino ignorada: {linea[:50]}")

    def _bucle_simulado(self, duracion_segundos: float = None):
        """
        Genera valores simulados que cambian lentamente.

        Los valores siguen una onda sinusoidal con ruido, para que
        el audio evolucione de forma natural durante las pruebas.

        Args:
            duracion_segundos: Si se especifica, corre solo por ese tiempo.
                               Si es None, corre hasta que se llame detener().
        """
        self.modo_simulado = True
        logger.info("Modo simulado activo — generando datos de sensores ficticios.")

        inicio = time.time()
        t = 0.0

        while self._corriendo:
            # Verificar si hay que detenerse por duración
            if duracion_segundos and (time.time() - inicio) >= duracion_segundos:
                break

            # Generar valores que cambian lentamente con ondas sinusoidales
            # Cada sensor tiene una frecuencia diferente para que no vayan sincronizados
            with self._lock:
                self._sensores['humidity'] = (
                    0.5 + 0.3 * math.sin(t * 0.1) + 0.05 * random.gauss(0, 1)
                )
                self._sensores['temperature'] = (
                    0.5 + 0.2 * math.sin(t * 0.07 + 1.0) + 0.02 * random.gauss(0, 1)
                )
                self._sensores['light'] = (
                    0.5 + 0.4 * math.sin(t * 0.05 + 2.5) + 0.03 * random.gauss(0, 1)
                )

                # Clampear entre 0.0 y 1.0
                for clave in self._sensores:
                    self._sensores[clave] = max(0.0, min(1.0, self._sensores[clave]))

            t += 1.0
            time.sleep(1.0)
