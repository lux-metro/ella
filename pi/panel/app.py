from flask import Flask, render_template, request, redirect, url_for, flash
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

CONFIG_FILE = os.path.expanduser("~/ella/config.env")
WIFI_CRED_FILE = os.path.expanduser("~/ella/credenciales_wifi.txt")

# Los scripts de red viven en el repo, junto al panel (rutas relativas para
# que funcionen tanto con el repo en ~/ella/repo como en ~/ella).
DIR_PANEL = os.path.dirname(os.path.abspath(__file__))
SCRIPT_ACTIVAR_AP = os.path.join(DIR_PANEL, '..', 'setup_pi_access_point.sh')
SCRIPT_REVERTIR_WIFI = os.path.join(DIR_PANEL, '..', 'revertir_wifi.sh')

NOMBRE_AP = "InstalacionElla"

# --- Autenticación ---
def verificar_credenciales(username, password):
    return username == PANEL_USER and password == PANEL_PASS

def pedir_autenticacion():
    return ('Requerido iniciar sesión', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requiere_auth(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        auth = request.authorization
        if not auth or not verificar_credenciales(auth.username, auth.password):
            return pedir_autenticacion()
        return f(*args, **kwargs)
    return decorado

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

def estado_servicio(nombre_servicio):
    try:
        res = subprocess.run(["systemctl", "--user", "is-active", nombre_servicio], capture_output=True, text=True)
        return res.stdout.strip()
    except:
        return "unknown"

def estado_ap():
    """Estado del modo Access Point (NetworkManager)."""
    configurado = False
    activo = False
    try:
        res = subprocess.run(["nmcli", "-t", "-f", "NAME", "con", "show"], capture_output=True, text=True)
        configurado = NOMBRE_AP in res.stdout
        res = subprocess.run(["nmcli", "-t", "-f", "NAME", "con", "show", "--active"], capture_output=True, text=True)
        activo = NOMBRE_AP in res.stdout
    except Exception:
        pass
    return {'configurado': configurado, 'activo': activo}

# --- Rutas ---
@app.route('/')
@requiere_auth
def inicio():
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
    servicios = {
        'reproducir': estado_servicio('reproducir.service'),
        'sentir_presencia': estado_servicio('sentir-presencia.service')
    }

    # Hora vigente de la Raspberry (se muestra y pre-carga en el panel)
    fecha_hora_pi = time.strftime('%Y-%m-%d %H:%M:%S')
    hora_pi_input = time.strftime('%Y-%m-%dT%H:%M:%S')

    return render_template('index.html', config=config, presencia=presencia,
                           intensidad=intensidad, hace_cuanto=hace_cuanto,
                           servicios=servicios, ap=estado_ap(),
                           fecha_hora_pi=fecha_hora_pi, hora_pi_input=hora_pi_input)

@app.route('/config', methods=['POST'])
@requiere_auth
def guardar_config():
    config = leer_configuracion()
    for key in config.keys():
        if key in request.form:
            config[key] = request.form[key]
    guardar_configuracion(config)
    flash("Configuración guardada exitosamente.", "success")
    return redirect(url_for('inicio'))

@app.route('/reiniciar/<nombre_servicio>', methods=['POST'])
@requiere_auth
def reiniciar_servicio(nombre_servicio):
    if nombre_servicio not in ['reproducir', 'sentir-presencia']:
        flash("Servicio inválido.", "error")
        return redirect(url_for('inicio'))

    try:
        subprocess.run(["systemctl", "--user", "restart", f"{nombre_servicio}.service"], check=True)
        flash(f"Servicio {nombre_servicio} reiniciado.", "success")
    except Exception as e:
        flash(f"Error al reiniciar {nombre_servicio}: {e}", "error")

    return redirect(url_for('inicio'))

@app.route('/config/hora', methods=['POST'])
@requiere_auth
def actualizar_hora():
    nueva_hora = request.form.get('hora')
    if nueva_hora:
        try:
            # El input datetime-local envía 'YYYY-MM-DDTHH:MM:SS'
            nueva_hora = nueva_hora.replace('T', ' ')
            subprocess.run(["sudo", "-n", "date", "-s", nueva_hora], check=True)
            flash("Hora actualizada exitosamente.", "success")
        except Exception as e:
            flash(f"Error al actualizar la hora (¿falta configurar sudoers?): {e}", "error")
    return redirect(url_for('inicio'))

@app.route('/config/activar_ap', methods=['POST'])
@requiere_auth
def activar_ap():
    if estado_ap()['activo']:
        flash(f"El Access Point '{NOMBRE_AP}' ya está activo.", "info")
        return redirect(url_for('inicio'))

    contrasena = request.form.get('contrasena', '').strip()
    if len(contrasena) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "error")
        return redirect(url_for('inicio'))

    if not os.path.exists(SCRIPT_ACTIVAR_AP):
        flash("No se encontró el script setup_pi_access_point.sh.", "error")
        return redirect(url_for('inicio'))

    try:
        os.makedirs(os.path.dirname(WIFI_CRED_FILE), exist_ok=True)
        with open(WIFI_CRED_FILE, 'w') as f:
            f.write(contrasena + "\n")

        # Se ejecuta en background: activar el AP corta la conexión actual.
        # Los logs quedan en /tmp/activar_ap.log para diagnóstico.
        with open('/tmp/activar_ap.log', 'w') as log:
            subprocess.Popen(
                ["sudo", "-n", "bash", SCRIPT_ACTIVAR_AP],
                stdout=log, stderr=log, start_new_session=True,
            )
        return "El Access Point se está activando. Conectate a la red WiFi 'InstalacionElla' y entrá a http://192.168.4.1:5000"
    except Exception as e:
        flash(f"Error ejecutando script: {e}", "error")
        return redirect(url_for('inicio'))

@app.route('/config/revertir_wifi', methods=['POST'])
@requiere_auth
def revertir_wifi():
    seguridad = request.form.get('seguridad', '')
    if seguridad.strip() != "estoy muy seguro":
        flash("Mecanismo de seguridad fallido. Debes escribir exactamente la frase solicitada.", "error")
        return redirect(url_for('inicio'))

    if not os.path.exists(SCRIPT_REVERTIR_WIFI):
        flash("No se encontró el script revertir_wifi.sh.", "error")
        return redirect(url_for('inicio'))

    try:
        # Ejecutamos el script en background y ordenamos un reboot en 2 segundos
        subprocess.Popen(f"sudo -n bash {SCRIPT_REVERTIR_WIFI} && sleep 2 && sudo -n reboot", shell=True)
        return "El Access Point se está desactivando y la máquina se reiniciará en unos segundos. Ya puedes cerrar esta ventana."
    except Exception as e:
        flash(f"Error ejecutando script: {e}", "error")
        return redirect(url_for('inicio'))


# --- Bluetooth API ---
def encender_bluetooth():
    # El adaptador puede quedar bloqueado por rfkill (Soft blocked: yes),
    # lo que hace fallar el scan al instante con "NotReady". Lo desbloqueamos
    # y encendemos antes de escanear. El arranque también lo asegura vía
    # ella-bluetooth.service, esto es una red de seguridad extra.
    try:
        subprocess.run(["sudo", "-n", "rfkill", "unblock", "bluetooth"], timeout=10)
    except Exception:
        pass
    try:
        subprocess.run(["bluetoothctl", "power", "on"], timeout=10)
    except Exception:
        pass

@app.route('/bluetooth/escanear', methods=['POST'])
@requiere_auth
def escanear_bluetooth():
    encender_bluetooth()

    # scan on con --timeout corta solo y devuelve un exit code confiable
    # (a diferencia del truco de matar el proceso por timeout).
    scan = subprocess.run(
        ["bluetoothctl", "--timeout", "5", "scan", "on"],
        capture_output=True, text=True, timeout=20,
    )
    if scan.returncode != 0:
        detalle = scan.stderr.strip() or scan.stdout.strip()
        flash(f"Error al escanear Bluetooth: {detalle or 'bluetoothctl no disponible'}", "error")
        return redirect(url_for('inicio'))

    res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True)
    devices_html = "<ul>"
    for line in res.stdout.splitlines():
        if line.startswith("Device "):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                mac, name = parts[1], parts[2]
                devices_html += f"<li>{name} ({mac}) - <form style='display:inline' method='POST' action='/bluetooth/conectar'><input type='hidden' name='mac' value='{mac}'><button type='submit'>Conectar</button></form></li>"
    devices_html += "</ul>"

    if devices_html == "<ul></ul>":
        flash("No se encontraron dispositivos Bluetooth en 5s. Verificá que el parlante esté encendido y en modo descubrible/pareado.", "info")
    else:
        flash(f"Dispositivos encontrados:<br>{devices_html}", "info")
    return redirect(url_for('inicio'))

@app.route('/bluetooth/conectar', methods=['POST'])
@requiere_auth
def conectar_bluetooth():
    mac = request.form.get('mac')
    if mac:
        try:
            subprocess.run(["bluetoothctl", "pair", mac], check=False)
            subprocess.run(["bluetoothctl", "trust", mac], check=True)
            subprocess.run(["bluetoothctl", "connect", mac], check=True)
            flash(f"Conectado exitosamente a {mac}.", "success")
        except Exception as e:
            flash(f"Error conectando a {mac}: {e}", "error")
    return redirect(url_for('inicio'))

@app.route('/bluetooth/desvincular', methods=['POST'])
@requiere_auth
def desvincular_bluetooth():
    mac = request.form.get('mac')
    if mac:
        try:
            subprocess.run(["bluetoothctl", "remove", mac], check=True)
            flash(f"Dispositivo {mac} desvinculado.", "success")
        except Exception as e:
            flash(f"Error desvinculando {mac}: {e}", "error")
    return redirect(url_for('inicio'))

@app.route('/bluetooth/probar', methods=['POST'])
@requiere_auth
def probar_bluetooth():
    try:
        subprocess.Popen(["play", "-n", "synth", "2", "pinknoise"])
        flash("Reproduciendo sonido de prueba (ruido rosa por 2s)...", "success")
    except Exception as e:
        flash(f"Error reproduciendo audio: {e}", "error")
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
