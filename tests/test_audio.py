"""
test_audio.py — Script de prueba de la salida de audio

Este script verifica que:
1. sox/play estén instalados
2. Haya archivos de audio válidos
3. La salida de audio funcione

Uso:
  python3 test_audio.py
"""

import os
import subprocess
import time

def testear():
    print("=== Test de Salida de Audio ===")
    
    # 1. Verificar instalación de sox
    print("Verificando 'sox' (play)...")
    try:
        resultado = subprocess.run(['play', '--version'], capture_output=True, text=True)
        if resultado.returncode != 0:
            print("❌ sox falló. El comando 'play' está instalado pero no funciona.")
            return
        print("✅ sox está instalado y funciona.")
    except FileNotFoundError:
        print("❌ 'play' no se encontró. Necesitás instalar sox:")
        print("   sudo apt-get install sox libsox-fmt-all")
        return

    # 2. Generar un tono de prueba con synth
    print("\nGenerando tono de prueba (440Hz) durante 2 segundos...")
    print("Deberías escuchar un sonido continuo tipo pitido por el 3.5mm.")
    try:
        subprocess.run(['play', '-n', 'synth', '2', 'sine', '440', 'vol', '0.5'], check=True)
        print("✅ Tono reproducido.")
    except Exception as e:
        print(f"❌ Falló al reproducir el tono de prueba: {e}")
        print("Revisá tu configuración ALSA (~/.asoundrc o asound.conf).")
        return
        
    # 3. Buscar un archivo real en la carpeta audio
    directorio = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'audio'))
    print(f"\nBuscando archivos de audio reales en {directorio}...")
    
    if not os.path.isdir(directorio):
        print(f"❌ El directorio no existe.")
        return
        
    archivos = [f for f in os.listdir(directorio) if f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac'))]
    
    if not archivos:
        print("⚠️ No se encontraron archivos de audio en la carpeta.")
        print("Para un test completo, copiá al menos un .wav o .mp3 ahí.")
    else:
        archivo_prueba = os.path.join(directorio, archivos[0])
        print(f"✅ Se encontró: {archivos[0]}.")
        print("\nReproduciendo 5 segundos de este archivo...")
        
        try:
            # Reproducir, cortarlo a los 5 segundos con sox (trim)
            subprocess.run(['play', archivo_prueba, 'trim', '0', '5', 'vol', '0.7'], check=True)
            print("✅ Reproducción exitosa.")
        except Exception as e:
            print(f"❌ Falló al reproducir el archivo: {e}")
            
    print("\nTest finalizado.")

if __name__ == '__main__':
    testear()
