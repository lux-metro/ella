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

La salida de audio es un parlante Bluetooth emparejado con la Pi.
Si hay una MAC configurada (en ~/ella/bluetooth_mac.txt, escrita por el
Panel Web al conectar, o como fallback en 'mac_parlante_bluetooth' de
config.yaml), el motor verifica la conexión antes de reproducir y la
restablece si hace falta.

Uso:
    from audio_engine import MotorDeAudio
    motor = MotorDeAudio(config, lector_serial)
    motor.iniciar()  # Bloquea. Llama desde el hilo principal.
"""

import logging
import math
import os
import random
import re
import subprocess
import threading
import time

logger = logging.getLogger(__name__)


class MotorDeAudio:
    """
    Motor de audio principal de *ella*.

    Toma la configuración del dispositivo y un lector de sensores,
    y genera una performance sonora continua que evoluciona según
    la temperatura, la luz y la presencia de visitantes.
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

        # Conectar el parlante Bluetooth apenas arranca la Pi, sin esperar a
        # que suene un clip (en un hilo aparte para no demorar la reproducción).
        threading.Thread(
            target=self._reconectar_bluetooth_al_inicio,
            name="reconectar-bluetooth-inicio",
            daemon=True,
        ).start()

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

            # Asegurar que el parlante Bluetooth esté conectado
            self._asegurar_conexion_bluetooth()

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

        La presencia (radar ESP32) modula el tempo, la temperatura el
        volumen y la luz la variación de pitch. Si no hay datos de un
        sensor, usa valores por defecto con variación aleatoria sutil.

        Retorna:
            dict con claves 'volumen', 'tempo', 'pitch_shift'
        """
        if self.lector_serial:
            sensores = self.lector_serial.obtener_sensores()
        else:
            # Sin sensores: valores neutros con variación aleatoria
            sensores = {
                'temperature': 0.5,
                'light': 0.5,
            }

        presencia = self._obtener_presencia()
        temperatura = max(0.0, min(1.0, sensores['temperature']))
        luz = max(0.0, min(1.0, sensores['light']))

        # --- Reglas de mapeo sensores → efectos ---
        # Estas son las decisiones artísticas centrales del sistema.
        # Podés cambiarlas para alterar el comportamiento sonoro.

        # PRESENCIA → TEMPO
        # Más presencia = más rápido (la instalación reacciona a los visitantes)
        # Rango: 0.6 (nadie, ambiente lento) a 1.2 (alguien cerca, activo)
        # Sin datos de presencia (radar apagado): tempo aleatorio en el mismo rango
        if presencia is None:
            tempo = random.uniform(0.6, 1.2)
        else:
            tempo = 0.6 + presencia * 0.6

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

        if presencia is not None:
            logger.debug(f"Presencia: {presencia:.2f}")
        else:
            logger.debug("Sin datos de presencia (tempo aleatorio).")

        if self.lector_serial and not self.lector_serial.modo_simulado:
            logger.debug(
                f"Sensores reales — Temp: {temperatura:.2f}, Luz: {luz:.2f}"
            )
        else:
            logger.debug("Usando valores simulados de sensores.")

        logger.debug(
            f"Efectos calculados — Vol: {efectos['volumen']:.2f}, "
            f"Tempo: {efectos['tempo']:.2f}, Pitch: {efectos['pitch_shift']:+.1f}st"
        )

        return efectos

    def _obtener_presencia(self):
        """
        Lee la intensidad de presencia del radar ESP32 (0.0-1.0).

        El servicio 'sentir-presencia' escribe continuamente el valor
        suavizado en /tmp/intensidad.txt.

        Retorna:
            float entre 0.0 y 1.0, o None si no hay datos disponibles
            (por ej: el servicio de presencia no está corriendo).
        """
        try:
            with open('/tmp/intensidad.txt', 'r') as archivo:
                valor = float(archivo.read().strip())
            return max(0.0, min(1.0, valor))
        except Exception:
            return None

    def _mac_parlante(self) -> str:
        """
        MAC del parlante configurado.

        Prioridad a ~/ella/bluetooth_mac.txt (lo escribe el Panel Web al
        conectar, y vive FUERA del repo para no chocar con los 'git pull').
        Como fallback, 'mac_parlante_bluetooth' de config.yaml (config manual).
        """
        try:
            with open(os.path.expanduser("~/ella/bluetooth_mac.txt")) as f:
                mac = f.read().strip()
            if re.fullmatch(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
                return mac
        except Exception:
            pass
        return self.config.get('mac_parlante_bluetooth', '').strip()

    def _esperar_adaptador_bluetooth(self, max_seg: int = 90) -> bool:
        """
        Espera (haciendo poll, sin tocar el adaptador) a que hci0 esté
        registrado con bluetoothd.

        Importante: recién cuando bluetoothd tiene un controlador, la descarga
        de firmware por UART terminó. Antes de eso, mandar 'power on' o cualquier
        comando HCI interfiere con el firmware y deja el adaptador atorado
        ('command tx timeout'), como pasaba con el servicio de boot que se
        eliminó. Por eso acá NO se pokea nada: solo se consulta 'bluetoothctl
        show', que es de solo lectura.

        Retorna:
            True apenas aparece un controlador, o False si se agotó max_seg.
        """
        inicio = time.time()
        while self._corriendo and (time.time() - inicio) < max_seg:
            try:
                salida = subprocess.run(
                    ['bluetoothctl', 'show'],
                    capture_output=True, text=True, timeout=10,
                ).stdout
                if 'Controller' in salida:
                    return True
            except Exception:
                pass
            time.sleep(3)
        logger.warning(
            f"No se detectó el adaptador Bluetooth tras {max_seg} segundos."
        )
        return False

    def _reconectar_bluetooth_al_inicio(self):
        """
        Conecta el parlante Bluetooth al iniciar el motor (y por lo tanto al
        arrancar la Pi). Espera a que el adaptador esté listo y recién entonces
        hace la reconexión, sin interferir con la inicialización del firmware.

        Corre en un hilo daemon: si el parlante está apagado o fuera de
        alcance, loguea y lo reintenta el bucle principal antes de cada clip.
        """
        if not self._corriendo:
            return
        if not self._mac_parlante():
            logger.info("Sin MAC de parlante configurada; omitiendo reconexión al inicio.")
            return
        if self._esperar_adaptador_bluetooth(max_seg=90):
            self._asegurar_conexion_bluetooth()

    def _asegurar_conexion_bluetooth(self) -> bool:
        """
        Verifica que el parlante Bluetooth esté conectado y, si no,
        intenta reconectarlo (patrón del prototipo bash).

        Solo actúa si hay una MAC configurada (archivo runtime o config.yaml).
        Si la conexión falla, el audio saldrá por el dispositivo por defecto.

        Retorna:
            True si el parlante está conectado (o no hay MAC configurada).
        """
        mac = self._mac_parlante()
        if not mac:
            return True

        def esta_conectado() -> bool:
            try:
                info = subprocess.run(
                    ['bluetoothctl', 'info', mac],
                    capture_output=True, text=True, timeout=10,
                ).stdout
                return 'Connected: yes' in info
            except Exception:
                return False

        if esta_conectado():
            return True

        # Espera acotada a que hci0 esté registrado antes de mandar 'power on':
        # si el adaptador está a medio inicializar (firmware por UART), ese
        # comando lo deja atorado. Sin adaptador tras 15 s, seguimos sin
        # bluetooth y el audio sale por el dispositivo por defecto.
        if not self._esperar_adaptador_bluetooth(max_seg=15):
            return False

        logger.info(
            f"Parlante Bluetooth no conectado. Intentando conectar {mac}..."
        )
        # Sin AutoEnable (causaba un tx timeout al pisar el firmware por UART),
        # el adaptador queda apagado tras el boot; el power on de acá lo
        # enciende, ya con hci0 registrado (seguro).
        try:
            subprocess.run(
                ['bluetoothctl', 'power', 'on'],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass

        # Tras un reinicio de la Pi, el parlante suele quedar sin vínculo
        # ('Paired: no'), así que repetimos el flujo del Panel Web:
        # pair (sin exigir éxito) → trust → connect.
        for intento in range(1, 6):
            try:
                subprocess.run(
                    ['bluetoothctl', 'pair', mac],
                    capture_output=True, text=True, timeout=20,
                )
                subprocess.run(
                    ['bluetoothctl', 'trust', mac],
                    capture_output=True, text=True, timeout=10,
                )
                subprocess.run(
                    ['bluetoothctl', 'connect', mac],
                    capture_output=True, text=True, timeout=20,
                )
            except Exception as e:
                logger.warning(
                    f"Error al conectar Bluetooth (intento {intento}/5): {e}"
                )
            time.sleep(3)
            if esta_conectado():
                logger.info(f"Parlante Bluetooth {mac} conectado.")
                return True

        logger.error(
            f"No se pudo conectar el parlante Bluetooth {mac}. "
            "El audio saldrá por el dispositivo por defecto."
        )
        return False

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
