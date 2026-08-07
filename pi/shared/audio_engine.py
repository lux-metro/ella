"""
audio_engine.py — Motor de reproducción de audio para *ella*

Este módulo maneja toda la lógica de reproducción:
- Seleccionar clips de audio al azar
- Aplicar efectos en tiempo real (velocidad, volumen)
- Recibir datos de sensores y hacer que influyan en el sonido
- Gestionar la evolución sonora durante la exhibición

El audio se reproduce usando 'sox' (el comando 'play') a través de
subprocess. Esto es consistente con el prototipo bash original y
es muy robusto: si una reproducción falla, simplemente pasa a la siguiente.

Uso:
    from audio_engine import MotorDeAudio
    motor = MotorDeAudio(config, lector_serial)
    motor.iniciar()  # Bloquea. Llama desde el hilo principal.
"""

import logging
import math
import os
import random
import subprocess
import time

logger = logging.getLogger(__name__)


class MotorDeAudio:
    """
    Motor de audio principal de *ella*.

    Toma la configuración del dispositivo y un lector de sensores,
    y genera una performance sonora continua que evoluciona según
    los datos biológicos de la instalación.
    """

    def __init__(self, config: dict, lector_serial=None):
        """
        Args:
            config:        Diccionario de configuración cargado desde config.yaml
            lector_serial: Instancia de LectorSerial (opcional). Si es None,
                           los efectos no van a responder a sensores.
        """
        self.config = config
        self.lector_serial = lector_serial
        self.directorio_audio = os.path.expanduser(config['directorio_audio'])

        # Parámetros de reproducción con valores por defecto
        self.volumen_base = config.get('volumen_base', 0.7)
        self.pausa_min_seg = config.get('pausa_min_seg', 2)
        self.pausa_max_seg = config.get('pausa_max_seg', 15)

        # Estado interno
        self._corriendo = False
        self._proceso_actual = None  # El subprocess de sox en curso

    def iniciar(self):
        """
        Inicia el bucle de reproducción. BLOQUEA el hilo actual.

        Para detener, llamar detener() desde otro hilo o con Ctrl+C.
        """
        self._corriendo = True
        logger.info(f"Motor de audio iniciado. Directorio: {self.directorio_audio}")

        try:
            self._bucle_principal()
        except KeyboardInterrupt:
            logger.info("Interrupción de usuario recibida.")
        finally:
            self.detener()

    def detener(self):
        """Detiene el motor y termina cualquier reproducción en curso."""
        self._corriendo = False
        if self._proceso_actual and self._proceso_actual.poll() is None:
            self._proceso_actual.terminate()
            self._proceso_actual.wait(timeout=3)
        logger.info("Motor de audio detenido.")

    def _bucle_principal(self):
        """Bucle principal: seleccionar archivo → aplicar efectos → reproducir → pausa → repetir."""
        while self._corriendo:
            # Obtener lista de archivos de audio disponibles
            archivos = self._listar_archivos_audio()

            if not archivos:
                logger.warning(
                    f"No hay archivos de audio en: {self.directorio_audio}. "
                    f"Esperando 30 segundos..."
                )
                time.sleep(30)
                continue

            # Seleccionar un archivo al azar
            archivo = random.choice(archivos)

            # Calcular efectos basados en los sensores actuales
            efectos = self._calcular_efectos()

            # Reproducir el archivo con los efectos
            self._reproducir(archivo, efectos)

            # Pausa entre clips
            if self._corriendo:
                pausa = self._calcular_pausa(efectos)
                logger.debug(f"Pausa de {pausa:.1f} segundos...")
                time.sleep(pausa)

    def _listar_archivos_audio(self) -> list:
        """
        Lista todos los archivos de audio en el directorio configurado.

        Retorna:
            Lista de rutas completas a archivos de audio (.wav, .flac, .ogg, .mp3)
        """
        extensiones_validas = {'.wav', '.flac', '.ogg', '.mp3', '.aiff'}
        archivos = []

        if not os.path.isdir(self.directorio_audio):
            logger.error(f"El directorio de audio no existe: {self.directorio_audio}")
            return []

        for nombre in os.listdir(self.directorio_audio):
            _, ext = os.path.splitext(nombre.lower())
            if ext in extensiones_validas:
                archivos.append(os.path.join(self.directorio_audio, nombre))

        return sorted(archivos)  # sorted para reproducibilidad

    def _calcular_efectos(self) -> dict:
        """
        Calcula los parámetros de efectos de audio basados en los sensores.

        Si hay datos de sensores reales, los usa para modular los efectos.
        Si no, usa valores por defecto con variación aleatoria sutil.

        Retorna:
            dict con claves 'volumen', 'tempo', 'pitch_shift'
        """
        if self.lector_serial:
            sensores = self.lector_serial.obtener_sensores()
        else:
            # Sin sensores: valores neutros con variación aleatoria
            sensores = {
                'humidity': 0.5 + 0.1 * random.gauss(0, 1),
                'temperature': 0.5,
                'light': 0.5,
            }

        humedad = max(0.0, min(1.0, sensores['humidity']))
        temperatura = max(0.0, min(1.0, sensores['temperature']))
        luz = max(0.0, min(1.0, sensores['light']))

        # --- Reglas de mapeo sensores → efectos ---
        # Estas son las decisiones artísticas centrales del sistema.
        # Podés cambiarlas para alterar el comportamiento sonoro.

        # HUMEDAD → TEMPO
        # Más húmedo = más lento (la arcilla pesada y húmeda es más lenta)
        # Rango: 0.6 (muy húmedo, muy lento) a 1.2 (muy seco, más rápido)
        tempo = 0.6 + (1.0 - humedad) * 0.6

        # TEMPERATURA → VOLUMEN
        # Más caliente = ligeramente más volumen (activación)
        # Rango: volumen_base × 0.8 a volumen_base × 1.2
        volumen = self.volumen_base * (0.8 + temperatura * 0.4)

        # LUZ → VARIACIÓN ALEATORIA DE PITCH
        # Más oscuro = sonido más estable (menos variación)
        # Más luminoso = más imprevisibilidad
        variacion_pitch = luz * 2.0  # ±0 a ±2 semitonos

        # Agregar aleatoriedad dentro del rango permitido por la luz
        pitch_shift = random.uniform(-variacion_pitch, variacion_pitch)

        efectos = {
            'volumen': max(0.1, min(1.5, volumen)),
            'tempo': max(0.4, min(1.5, tempo)),
            'pitch_shift': pitch_shift,
        }

        if self.lector_serial and not self.lector_serial.modo_simulado:
            logger.debug(
                f"Sensores reales — Humedad: {humedad:.2f}, "
                f"Temp: {temperatura:.2f}, Luz: {luz:.2f}"
            )
        else:
            logger.debug("Usando valores simulados de sensores.")

        logger.debug(
            f"Efectos calculados — Vol: {efectos['volumen']:.2f}, "
            f"Tempo: {efectos['tempo']:.2f}, Pitch: {efectos['pitch_shift']:+.1f}st"
        )

        return efectos

    def _reproducir(self, ruta_archivo: str, efectos: dict):
        """
        Reproduce un archivo de audio con los efectos especificados usando sox.

        Args:
            ruta_archivo: Ruta completa al archivo de audio
            efectos:      Dict con 'volumen', 'tempo', 'pitch_shift'
        """
        nombre = os.path.basename(ruta_archivo)
        logger.info(f"Reproduciendo: {nombre}")

        # Construir el comando sox
        # play [archivo] vol [volumen] tempo [velocidad] pitch [semitonos_en_cents]
        pitch_cents = int(efectos['pitch_shift'] * 100)  # semitonos → cents

        comando = [
            'play',
            ruta_archivo,
            'vol', str(efectos['volumen']),          # Volumen (0.0-1.5)
            'tempo', str(round(efectos['tempo'], 2)), # Velocidad sin cambiar pitch
        ]

        # Agregar pitch shift solo si es significativo (evita procesamiento innecesario)
        if abs(pitch_cents) > 10:
            comando.extend(['pitch', str(pitch_cents)])

        try:
            self._proceso_actual = subprocess.Popen(
                comando,
                stdout=subprocess.DEVNULL,  # No mostrar output de sox
                stderr=subprocess.DEVNULL,
            )
            self._proceso_actual.wait()  # Esperar a que termine la reproducción

        except FileNotFoundError:
            logger.error(
                "'play' (sox) no está instalado. "
                "Instalá sox con: sudo apt install sox"
            )
            time.sleep(5)  # Esperar antes de reintentar para no saturar el log

        except Exception as e:
            logger.error(f"Error reproduciendo {nombre}: {e}")

    def _calcular_pausa(self, efectos: dict) -> float:
        """
        Calcula la duración de la pausa entre clips.

        La pausa se modula según el tempo: sonido más lento → pausas más largas.

        Args:
            efectos: Los efectos calculados para el clip que acaba de terminar

        Retorna:
            Duración de la pausa en segundos
        """
        # Pausa base aleatoria
        pausa_base = random.uniform(self.pausa_min_seg, self.pausa_max_seg)

        # Modular por el inverso del tempo: más lento → más pausa
        factor_tempo = 1.0 / max(efectos['tempo'], 0.5)
        pausa = pausa_base * factor_tempo

        return max(1.0, min(60.0, pausa))  # Entre 1 segundo y 1 minuto
