from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import subprocess
import time
from functools import wraps
from dotenv import load_dotenv

# Cargar credenciales del panel
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
PANEL_USER = os.environ.get('PANEL_USER', 'admin')
PANEL_PASS = os.environ.get('PANEL_PASS', 'admin')

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_flash_messages'

CONFIG_FILE = os.path.expanduser("~/ruidosa/config.env")

# --- Autenticación ---
def check_auth(username, password):
    return username == PANEL_USER and password == PANEL_PASS

def authenticate():
    return ('Requerido iniciar sesión', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- Utilidades ---
def leer_configuracion():
    config = {
        'VOL_MIN': '0.3', 'VOL_MAX': '1.0',
        'SPEED_MIN': '0.85', 'SPEED_MAX': '1.35',
        'VELOCIDAD_SUBIDA': '0.1', 'VELOCIDAD_BAJADA': '0.05',
        'UMBRAL_PRESENCIA': '0.5'
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k in config:
                        config[k] = v
    return config

def guardar_configuracion(config_dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        f.write("# Archivo de configuración compartido\n")
        for k, v in config_dict.items():
            f.write(f"{k}={v}\n")

def leer_estado(archivo, por_defecto="N/A"):
    if os.path.exists(archivo):
        try:
            with open(archivo, 'r') as f:
                return f.read().strip()
        except:
            return por_defecto
    return por_defecto

def get_service_status(service_name):
    try:
        res = subprocess.run(["systemctl", "--user", "is-active", service_name], capture_output=True, text=True)
        return res.stdout.strip()
    except:
        return "unknown"

# --- Rutas ---
@app.route('/')
@requires_auth
def index():
    config = leer_configuracion()
    
    # Leer estados
    presencia = leer_estado('/tmp/presencia.txt', 'N/A')
    intensidad = leer_estado('/tmp/intensidad.txt', 'N/A')
    ultimo_aviso_ts = leer_estado('/tmp/ultimo_aviso.txt', '0')
    
    # Calcular tiempo desde el último aviso
    hace_cuanto = "Nunca"
    try:
        ts = float(ultimo_aviso_ts)
        if ts > 0:
            segundos = int(time.time() - ts)
            hace_cuanto = f"Hace {segundos} segundos"
    except:
        pass

    # Estado de servicios
    estado_servicios = {
        'reproducir': get_service_status('reproducir.service'),
        'sentir_presencia': get_service_status('sentir-presencia.service')
    }

    return render_template('index.html', config=config, presencia=presencia, 
                           intensidad=intensidad, hace_cuanto=hace_cuanto,
                           servicios=estado_servicios)

@app.route('/config', methods=['POST'])
@requires_auth
def update_config():
    config = leer_configuracion()
    for key in config.keys():
        if key in request.form:
            config[key] = request.form[key]
    guardar_configuracion(config)
    flash("Configuración guardada exitosamente.", "success")
    return redirect(url_for('index'))

@app.route('/restart/<service_name>', methods=['POST'])
@requires_auth
def restart_service(service_name):
    if service_name not in ['reproducir', 'sentir-presencia']:
        flash("Servicio inválido.", "error")
        return redirect(url_for('index'))
    
    try:
        subprocess.run(["systemctl", "--user", "restart", f"{service_name}.service"], check=True)
        flash(f"Servicio {service_name} reiniciado.", "success")
    except Exception as e:
        flash(f"Error al reiniciar {service_name}: {e}", "error")
        
    return redirect(url_for('index'))

@app.route('/config/hora', methods=['POST'])
@requires_auth
def update_time():
    nueva_hora = request.form.get('hora')
    if nueva_hora:
        try:
            subprocess.run(["sudo", "date", "-s", nueva_hora], check=True)
            flash("Hora actualizada exitosamente.", "success")
        except Exception as e:
            flash(f"Error al actualizar la hora (¿falta configurar sudoers?): {e}", "error")
    return redirect(url_for('index'))

# --- Bluetooth API (Sin JS) ---
@app.route('/bluetooth/scan', methods=['POST'])
@requires_auth
def bt_scan():
    try:
        subprocess.run(["bluetoothctl", "scan", "on"], timeout=5)
    except subprocess.TimeoutExpired:
        subprocess.run(["bluetoothctl", "scan", "off"])
    
    res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True)
    devices_html = "<ul>"
    for line in res.stdout.splitlines():
        if line.startswith("Device "):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                mac, name = parts[1], parts[2]
                devices_html += f"<li>{name} ({mac}) - <form style='display:inline' method='POST' action='/bluetooth/connect'><input type='hidden' name='mac' value='{mac}'><button type='submit'>Conectar</button></form></li>"
    devices_html += "</ul>"
    
    if devices_html == "<ul></ul>":
        flash("No se encontraron dispositivos Bluetooth.", "info")
    else:
        flash(f"Dispositivos encontrados:<br>{devices_html}", "info")
    return redirect(url_for('index'))

@app.route('/bluetooth/connect', methods=['POST'])
@requires_auth
def bt_connect():
    mac = request.form.get('mac')
    if mac:
        try:
            subprocess.run(["bluetoothctl", "pair", mac], check=False)
            subprocess.run(["bluetoothctl", "trust", mac], check=True)
            subprocess.run(["bluetoothctl", "connect", mac], check=True)
            flash(f"Conectado exitosamente a {mac}.", "success")
        except Exception as e:
            flash(f"Error conectando a {mac}: {e}", "error")
    return redirect(url_for('index'))

@app.route('/bluetooth/disconnect', methods=['POST'])
@requires_auth
def bt_disconnect():
    mac = request.form.get('mac')
    if mac:
        try:
            subprocess.run(["bluetoothctl", "remove", mac], check=True)
            flash(f"Dispositivo {mac} desvinculado.", "success")
        except Exception as e:
            flash(f"Error desvinculando {mac}: {e}", "error")
    return redirect(url_for('index'))

@app.route('/bluetooth/test', methods=['POST'])
@requires_auth
def bt_test():
    try:
        subprocess.Popen(["play", "-n", "synth", "2", "pinknoise"])
        flash("Reproduciendo sonido de prueba (ruido rosa por 2s)...", "success")
    except Exception as e:
        flash(f"Error reproduciendo audio: {e}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
