#!/usr/bin/env python3
import socket
import time
import os
import threading

# Archivos de estado
ARCHIVO_PRESENCIA = "/tmp/presencia.txt"
ARCHIVO_INTENSIDAD = "/tmp/intensidad.txt"
ARCHIVO_ULTIMO_AVISO = "/tmp/ultimo_aviso.txt"

# Archivo de configuración
CONFIG_FILE = os.path.expanduser("~/ella/config.env")

# Valores por defecto (tiempos en segundos para pasar de 0 a 1.0 o viceversa)
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
TIEMPO_SUBIDA_SEG = 2.0
TIEMPO_BAJADA_SEG = 5.0
UMBRAL_PRESENCIA = 0.5
# Mínimo aceptable para evitar división por cero y rampas instantáneas.
TIEMPO_MINIMO_SEG = 0.1

# Las claves legacy 'VELOCIDAD_SUBIDA'/'VELOCIDAD_BAJADA' eran por tick (10 ticks/s).
# Si el config.env tiene esas claves pero no las nuevas en segundos, se convierten
# (el tiempo para llegar a 1.0 es 1/(velocidad*10)). Esto preserva el tuning de
# instalaciones anteriores al migrar.
def _velocidad_a_segundos(velocidad_por_tick):
    return 1.0 / (velocidad_por_tick * 10.0)

def leer_configuracion():
    """Lee el archivo config.env y actualiza las variables globales si existen."""
    global TIEMPO_SUBIDA_SEG, TIEMPO_BAJADA_SEG, UMBRAL_PRESENCIA
    try:
        if os.path.exists(CONFIG_FILE):
            # Las claves legacy ('VELOCIDAD_*') se leen pasivamente: solo se
            # aplican si las nuevas (en segundos) no están definidas. Así una
            # instalación previa no pierde su tuning al migrar.
            vel_subida_legacy = None
            vel_bajada_legacy = None
            tiene_tiempo_subida = False
            tiene_tiempo_bajada = False
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key == "TIEMPO_SUBIDA_SEG":
                            TIEMPO_SUBIDA_SEG = max(TIEMPO_MINIMO_SEG, float(value))
                            tiene_tiempo_subida = True
                        elif key == "TIEMPO_BAJADA_SEG":
                            TIEMPO_BAJADA_SEG = max(TIEMPO_MINIMO_SEG, float(value))
                            tiene_tiempo_bajada = True
                        elif key == "VELOCIDAD_SUBIDA":
                            vel_subida_legacy = float(value)
                        elif key == "VELOCIDAD_BAJADA":
                            vel_bajada_legacy = float(value)
                        elif key == "UMBRAL_PRESENCIA":
                            UMBRAL_PRESENCIA = float(value)

            if not tiene_tiempo_subida and vel_subida_legacy and vel_subida_legacy > 0:
                TIEMPO_SUBIDA_SEG = max(TIEMPO_MINIMO_SEG, _velocidad_a_segundos(vel_subida_legacy))
            if not tiene_tiempo_bajada and vel_bajada_legacy and vel_bajada_legacy > 0:
                TIEMPO_BAJADA_SEG = max(TIEMPO_MINIMO_SEG, _velocidad_a_segundos(vel_bajada_legacy))
    except Exception as e:
        print(f"Error leyendo configuración: {e}")

# Variables de estado
estado_presencia_actual = 0 # 1 o 0 (según sensor)
intensidad_suavizada = 0.0

def procesar_intensidad():
    """Calcula la intensidad suavizada gradualmente y escribe los archivos en /tmp."""
    global intensidad_suavizada
    contador = 0
    ultimo_instante = time.monotonic()
    while True:
        # Releer config cada ~1s para que un cambio de velocidades en el panel
        # se aplique en vivo, sin reiniciar el servicio (el panel ya no
        # necesita tocar nada tras guardar).
        if contador % 10 == 0:
            leer_configuracion()
        contador += 1

        # Incremento basado en tiempo real: con TIEMPO_*_SEG en segundos,
        # la intensidad pasa de 0 a 1.0 (o de 1.0 a 0) en exactamente ese
        # tiempo, sin depender de la frecuencia real del bucle.
        ahora = time.monotonic()
        dt = ahora - ultimo_instante
        ultimo_instante = ahora

        if estado_presencia_actual == 1:
            intensidad_suavizada += dt / TIEMPO_SUBIDA_SEG
            if intensidad_suavizada > 1.0:
                intensidad_suavizada = 1.0
        else:
            intensidad_suavizada -= dt / TIEMPO_BAJADA_SEG
            if intensidad_suavizada < 0.0:
                intensidad_suavizada = 0.0

        # Escribir a archivos
        try:
            with open(ARCHIVO_PRESENCIA, "w") as f:
                f.write(str(estado_presencia_actual))
            
            with open(ARCHIVO_INTENSIDAD, "w") as f:
                f.write(f"{intensidad_suavizada:.2f}")
        except Exception as e:
            print(f"Error escribiendo estado: {e}")

        time.sleep(0.1) # Actualizar a 10Hz

def escuchar_udp():
    """Escucha avisos de presencia en el puerto UDP desde el ESP32."""
    global estado_presencia_actual
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    
    print(f"Escuchando presencia en UDP {UDP_IP}:{UDP_PORT}...")
    
    while True:
        data, addr = sock.recvfrom(1024)
        mensaje = data.decode('utf-8').strip()
        
        # Guardar timestamp del último aviso recibido
        try:
            with open(ARCHIVO_ULTIMO_AVISO, "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            pass

        if mensaje == "1" or mensaje.lower() == "presencia":
            estado_presencia_actual = 1
        elif mensaje == "0" or mensaje.lower() == "ausencia":
            estado_presencia_actual = 0

if __name__ == "__main__":
    leer_configuracion()
    
    # Iniciar el hilo de procesamiento de intensidad (subida/bajada gradual)
    hilo_procesador = threading.Thread(target=procesar_intensidad, daemon=True)
    hilo_procesador.start()
    
    # El hilo principal escucha UDP
    escuchar_udp()
