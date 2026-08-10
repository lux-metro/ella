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

# Valores por defecto
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
VELOCIDAD_SUBIDA = 0.1
VELOCIDAD_BAJADA = 0.05
UMBRAL_PRESENCIA = 0.5

def leer_configuracion():
    """Lee el archivo config.env y actualiza las variables globales si existen."""
    global VELOCIDAD_SUBIDA, VELOCIDAD_BAJADA, UMBRAL_PRESENCIA
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key == "VELOCIDAD_SUBIDA":
                            VELOCIDAD_SUBIDA = float(value)
                        elif key == "VELOCIDAD_BAJADA":
                            VELOCIDAD_BAJADA = float(value)
                        elif key == "UMBRAL_PRESENCIA":
                            UMBRAL_PRESENCIA = float(value)
    except Exception as e:
        print(f"Error leyendo configuración: {e}")

# Variables de estado
estado_presencia_actual = 0 # 1 o 0 (según sensor)
intensidad_suavizada = 0.0

def procesar_intensidad():
    """Calcula la intensidad suavizada gradualmente y escribe los archivos en /tmp."""
    global intensidad_suavizada
    while True:
        # Calcular nueva intensidad
        if estado_presencia_actual == 1:
            intensidad_suavizada += VELOCIDAD_SUBIDA
            if intensidad_suavizada > 1.0:
                intensidad_suavizada = 1.0
        else:
            intensidad_suavizada -= VELOCIDAD_BAJADA
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
