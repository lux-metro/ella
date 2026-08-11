"""
config_loader.py — Carga la configuración de la Raspberry Pi

Este módulo lee el archivo config.yaml de la instalación y lo
pone disponible para el resto del programa.

Uso:
    from config_loader import cargar_config
    config = cargar_config()
    print(config['voz'])  # → 'ella'
"""

import os
import sys
import yaml
import logging

logger = logging.getLogger(__name__)


def cargar_config():
    """
    Carga el archivo de configuración YAML de este dispositivo.

    Busca el archivo en las siguientes ubicaciones (en orden):
    1. Variable de entorno ELLA_CONFIG (para tests o setups no estándar)
    2. pi/config.yaml relativo a la raíz del repositorio (instalación estándar)
    3. Relativo al directorio del script (para desarrollo local)

    Retorna:
        dict: Diccionario con toda la configuración.

    Lanza:
        SystemExit: Si no encuentra ningún archivo de configuración válido.
    """

    # --- Determinar la ruta del archivo de configuración ---

    # Opción 1: variable de entorno (útil para tests)
    ruta_config = os.environ.get('ELLA_CONFIG')

    # Opción 2: buscar el archivo relativo al directorio del proyecto
    if not ruta_config:
        # El script vive en pi/shared/, subimos dos niveles para llegar a la raíz
        directorio_raiz = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )

        candidato = os.path.join(directorio_raiz, 'pi', 'config.yaml')
        if os.path.exists(candidato):
            ruta_config = candidato

    # Si no encontramos ningún config, no podemos continuar
    if not ruta_config or not os.path.exists(ruta_config):
        logger.error(
            "No se encontró ningún archivo config.yaml. "
            "Asegurate de que exista pi/config.yaml. "
            "También podés definir la variable de entorno ELLA_CONFIG con la ruta completa."
        )
        sys.exit(1)

    # --- Leer y parsear el archivo YAML ---
    logger.info(f"Cargando configuración desde: {ruta_config}")

    try:
        with open(ruta_config, 'r', encoding='utf-8') as archivo:
            config = yaml.safe_load(archivo)
    except yaml.YAMLError as e:
        logger.error(f"Error al leer el archivo de configuración: {e}")
        logger.error("Verificá que el archivo config.yaml tenga formato YAML válido.")
        sys.exit(1)

    # --- Validar que tiene los campos obligatorios ---
    campos_obligatorios = ['voz', 'dispositivo_audio', 'directorio_audio']
    for campo in campos_obligatorios:
        if campo not in config:
            logger.error(
                f"El archivo de configuración no tiene el campo obligatorio: '{campo}'. "
                f"Revisá el archivo: {ruta_config}"
            )
            sys.exit(1)

    logger.info(f"Configuración cargada. Voz: {config['voz']}")
    return config
