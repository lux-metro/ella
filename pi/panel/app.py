from flask import Flask, render_template, request, redirect, url_for, flash
import os
import re
import subprocess
import threading
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

# La MAC del parlante configurado la guarda el panel FUERA del repo, en
# ~/ella/bluetooth_mac.txt, para que los 'git pull' nunca choquen con un
# archivo trackeado. El motor de audio (audio_engine.py) lee ese archivo con
# prioridad sobre 'mac_parlante_bluetooth' en pi/config.yaml.
MAC_PARLANTE_FILE = os.path.expanduser("~/ella/bluetooth_mac.txt")
# La MAC en pi/config.yaml queda como fallback (config manual).
CONFIG_YAML = os.path.join(DIR_PANEL, '..', 'config.yaml')

NOMBRE_AP = "InstalacionElla"

# Escaneo Bluetooth interactivo: el scan corre en un hilo de fondo y el panel
# lo polea vía GET /bluetooth/estado. 'dispositivos' es un dict MAC->nombre que
# se va completando en vivo; el usuario detiene el proceso cuando ve el que
# busca (si no, hay un auto-stop de seguridad).
BLUETOOTH_SCAN_MAX_SEG = 60
_bt_lock = threading.Lock()
_bt_estado = {'activo': False, 'error': '', 'dispositivos': {}, 'ts': 0.0}
_bt_proc = None

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

def _mac_valida(mac):
    return bool(re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac or ''))

def mac_parlante_configurado():
    """MAC del parlante configurado: prioridad a ~/ella/bluetooth_mac.txt y,
    como fallback, a 'mac_parlante_bluetooth' de pi/config.yaml."""
    try:
        with open(MAC_PARLANTE_FILE) as f:
            mac = f.read().strip()
        if _mac_valida(mac):
            return mac
    except Exception:
        pass
    try:
        with open(CONFIG_YAML) as f:
            for linea in f:
                if linea.strip().startswith('mac_parlante_bluetooth:'):
                    valor = linea.split(':', 1)[1].strip().strip('"\'')
                    if _mac_valida(valor):
                        return valor
    except Exception:
        pass
    return ''

def guardar_mac_parlante(mac):
    """Guarda la MAC del parlante en ~/ella/bluetooth_mac.txt (fuera del repo).

    Es lo que hace permanente la conexión: el motor de audio (audio_engine.py)
    lee este archivo al arrancar y reconecta el parlante solo tras un reinicio.
    Guardarlo fuera del repo evita que un 'git pull' choque con config.yaml.
    """
    mac = mac.strip()
    try:
        os.makedirs(os.path.dirname(MAC_PARLANTE_FILE), exist_ok=True)
        with open(MAC_PARLANTE_FILE, 'w') as f:
            f.write((mac + '\n') if _mac_valida(mac) else '')
    except Exception:
        pass

def info_dispositivo(mac):
    """Consulta 'bluetoothctl info <mac>' y devuelve (nombre, conectado)."""
    try:
        info = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return '', False
    nombre = ''
    conectado = False
    for linea in info.splitlines():
        linea = linea.strip()
        if linea.startswith('Name:'):
            nombre = linea.split(':', 1)[1].strip()
        elif linea.startswith('Connected:'):
            conectado = linea.split(':', 1)[1].strip() == 'yes'
    return nombre, conectado

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

    # Parlante Bluetooth configurado (pi/config.yaml) + su estado
    mac_parlante = mac_parlante_configurado()
    parlante = None
    if mac_parlante:
        nombre, conectado = info_dispositivo(mac_parlante)
        parlante = {'mac': mac_parlante, 'nombre': nombre, 'conectado': conectado}

    return render_template('index.html', config=config, presencia=presencia,
                           intensidad=intensidad, hace_cuanto=hace_cuanto,
                           servicios=servicios, ap=estado_ap(),
                           fecha_hora_pi=fecha_hora_pi, hora_pi_input=hora_pi_input,
                           parlante=parlante)

# El radar se considera "con señal" si recibió un aviso hace menos de esta
# cantidad de segundos (la ESP32 envía actualizaciones periódicas).
RADAR_SIN_SEÑAL_SEG = 10

@app.route('/presencia/estado')
@requiere_auth
def estado_presencia():
    """Estado de presencia en tiempo real (lo polea el panel con fetch).

    Lee los archivos que escribe sentir-presencia.py y devuelve JSON:
      - presencia:   0/1 (señal bruta del radar)
      - intensidad:  0.0-1.0 (valor suavizado)
      - hace_cuanto: segundos desde el último aviso, o None si nunca hubo
      - viva:        True si el radar está emitiendo (aviso reciente)
    """
    presencia = leer_estado('/tmp/presencia.txt', 'N/A')
    intensidad = leer_estado('/tmp/intensidad.txt', 'N/A')
    ultimo_aviso_ts = leer_estado('/tmp/ultimo_aviso.txt', '0')

    hace_cuanto = None
    viva = False
    try:
        ts = float(ultimo_aviso_ts)
        if ts > 0:
            hace_cuanto = int(time.time() - ts)
            viva = hace_cuanto <= RADAR_SIN_SEÑAL_SEG
    except Exception:
        pass

    return {
        'presencia': presencia,
        'intensidad': intensidad,
        'hace_cuanto': hace_cuanto,
        'viva': viva,
    }

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

@app.route('/config/reboot', methods=['POST'])
@requiere_auth
def reiniciar_pi():
    try:
        # En background: el panel muere con el reboot, la respuesta sale antes.
        subprocess.Popen("sleep 2 && sudo -n reboot", shell=True)
        return "La Raspberry Pi se está reiniciando. El panel volverá en unos 30 segundos."
    except Exception as e:
        flash(f"Error al reiniciar: {e}", "error")
        return redirect(url_for('inicio'))


# --- Bluetooth API ---
def encender_bluetooth():
    # El adaptador puede quedar bloqueado por rfkill (Soft blocked: yes),
    # lo que hace fallar el scan al instante con "NotReady". Lo desbloqueamos
    # y encendemos antes de escanear. El arranque lo deja desbloqueado vía la
    # regla udev; el power on de acá es una red de seguridad extra.
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
    with _bt_lock:
        if _bt_estado['activo']:
            flash("Ya hay un escaneo Bluetooth en curso.", "info")
            return redirect(url_for('inicio'))
        _bt_estado['activo'] = True
        _bt_estado['error'] = ''
        _bt_estado['dispositivos'] = {}
        _bt_estado['ts'] = time.time()

    # El scan corre en un hilo de fondo: el POST vuelve al toque y el panel
    # muestra los dispositivos en vivo poleando /bluetooth/estado.
    threading.Thread(target=_escaneo_bluetooth_worker, daemon=True).start()
    flash("Escaneando Bluetooth… Detené el escaneo cuando veas tu dispositivo.", "info")
    return redirect(url_for('inicio'))

@app.route('/bluetooth/detener', methods=['POST'])
@requiere_auth
def detener_bluetooth():
    _detener_scan_proceso()
    with _bt_lock:
        n = len(_bt_estado['dispositivos'])
        activo = _bt_estado['activo']
    if not activo:
        flash("No hay un escaneo Bluetooth en curso.", "info")
    else:
        flash(f"Escaneo detenido. {n} dispositivo(s) encontrado(s).", "info")
    return redirect(url_for('inicio'))

@app.route('/bluetooth/estado')
@requiere_auth
def estado_bluetooth():
    with _bt_lock:
        return {
            'activo': _bt_estado['activo'],
            'error': _bt_estado['error'],
            'ts': _bt_estado['ts'],
            'dispositivos': [
                {'mac': mac, 'nombre': nombre}
                for mac, nombre in _bt_estado['dispositivos'].items()
            ],
        }

def _detener_scan_proceso():
    global _bt_proc
    proc = _bt_proc
    if proc is not None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    _bt_proc = None

def _nombre_parece_mac(nombre, mac):
    """True si el 'nombre' es en realidad la MAC sin resolver (guiones vs ':').

    BlueZ muestra el alias; si el nombre no se resolvió, el alias ES la MAC
    formateada con guiones. Esos son los que vale la pena reintentar resolver.
    """
    if nombre in ('', mac):
        return True
    return nombre.replace('-', ':').lower() == mac.lower()

def _finalizar_nombres():
    """Resolución de nombres asíncrona tras detener el scan.

    'bluetoothctl devices' lista los ya conocidos y 'info <MAC>' dispara la
    petición de nombre (que BlueZ resuelve de forma asíncrona).
    """
    res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if line.startswith("Device "):
            parts = line.split(" ", 2)
            if len(parts) >= 3:
                with _bt_lock:
                    _bt_estado['dispositivos'].setdefault(parts[1], parts[2])

    with _bt_lock:
        pendientes = [
            mac for mac, nombre in _bt_estado['dispositivos'].items()
            if _nombre_parece_mac(nombre, mac)
        ]
    for mac in pendientes:
        try:
            subprocess.run(
                ["bluetoothctl", "info", mac],
                capture_output=True, text=True, timeout=5,
            )
        except Exception:
            pass
    if pendientes:
        time.sleep(2)
    for mac in pendientes:
        try:
            info = subprocess.run(
                ["bluetoothctl", "info", mac],
                capture_output=True, text=True, timeout=5,
            ).stdout
            for linea in info.splitlines():
                if linea.startswith("Name:"):
                    nombre = linea.split(":", 1)[1].strip()
                    if nombre:
                        with _bt_lock:
                            _bt_estado['dispositivos'][mac] = nombre
                    break
        except Exception:
            pass

def _escaneo_bluetooth_worker():
    try:
        _escaneo_bluetooth_worker_inner()
    except Exception:
        # Red de seguridad: un fallo inesperado no puede dejar el estado
        # 'activo' colgado (bloquearía futuros escaneos para siempre).
        _detener_scan_proceso()
        with _bt_lock:
            _bt_estado['activo'] = False
            _bt_estado['ts'] = time.time()

def _fusionar_devices():
    """Lista los dispositivos conocidos por el adaptador.

    Es la fuente confiable de tiempo real: 'bluetoothctl devices' refleja los
    descubrimientos apenas pasan (a diferencia de parsear el stdout del scan,
    que bluetoothctl bufferéa y suelta recién al terminar). También arrastra
    los nombres a medida que se resuelven (el alias se actualiza solo).
    """
    try:
        res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True)
    except Exception:
        return
    with _bt_lock:
        for line in res.stdout.splitlines():
            if not line.startswith("Device "):
                continue
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            mac, alias = parts[1], parts[2]
            actual = _bt_estado['dispositivos'].get(mac)
            if actual is None:
                _bt_estado['dispositivos'][mac] = alias
            elif _nombre_parece_mac(actual, mac):
                _bt_estado['dispositivos'][mac] = alias

def _leer_salida_scan(proc, error_holder):
    """Hilo lector del stdout del scan.

    Fast path (si stdbuf logra line-bufferear, los [NEW]/[CHG] se ven al
    instante) y captura de errores tipo "Failed to start discovery".
    """
    patron_nuevo = re.compile(r"\[NEW\] Device\s+([0-9A-F:]{17})\s+(.+)")
    patron_nombre = re.compile(r"\[CHG\] Device ([0-9A-F:]{17}) Name: (.+)")
    try:
        for linea in proc.stdout:
            texto = linea.strip()
            if ("Failed" in texto or "Error" in texto) and not error_holder['linea']:
                error_holder['linea'] = texto
            m = patron_nuevo.match(texto)
            if m:
                with _bt_lock:
                    _bt_estado['dispositivos'].setdefault(m.group(1), m.group(2))
                continue
            m = patron_nombre.match(texto)
            if m:
                with _bt_lock:
                    _bt_estado['dispositivos'][m.group(1)] = m.group(2)
    except Exception:
        pass

def _escaneo_bluetooth_worker_inner():
    global _bt_proc
    encender_bluetooth()

    # En modo one-shot, "scan on" SIN "--timeout" retorna apenas imprime
    # "Discovery started": el --timeout (igual al auto-stop) mantiene el scan
    # vivo y lo corta solo si el usuario no lo detiene antes.
    cmd = ["stdbuf", "-oL", "bluetoothctl", "--timeout", str(BLUETOOTH_SCAN_MAX_SEG), "scan", "on"]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except FileNotFoundError:
        # Fallback sin stdbuf (no debería pasar en Debian/Raspberry Pi OS).
        cmd = ["bluetoothctl", "--timeout", str(BLUETOOTH_SCAN_MAX_SEG), "scan", "on"]
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
        except Exception as e:
            with _bt_lock:
                _bt_estado['error'] = f"No se pudo iniciar el scan: {e}"
                _bt_estado['activo'] = False
            return
    _bt_proc = proc

    # Auto-stop de seguridad: un scan olvidado no puede correr para siempre.
    timer = threading.Timer(BLUETOOTH_SCAN_MAX_SEG, _detener_scan_proceso)
    timer.daemon = True
    timer.start()

    error_holder = {'linea': ''}
    reader = threading.Thread(
        target=_leer_salida_scan, args=(proc, error_holder), daemon=True
    )
    reader.start()

    # Mientras el scan siga vivo, fusionamos los dispositivos conocidos cada
    # segundo: es lo que hace que se vean aparecer en tiempo real.
    try:
        while proc.poll() is None:
            _fusionar_devices()
            time.sleep(1)
    finally:
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        reader.join(timeout=5)
        _bt_proc = None
        timer.cancel()

    # Pasada final de resolución de nombres con el scan ya detenido.
    _finalizar_nombres()
    with _bt_lock:
        if error_holder['linea'] and not _bt_estado['dispositivos']:
            _bt_estado['error'] = error_holder['linea']
        _bt_estado['activo'] = False
        _bt_estado['ts'] = time.time()

@app.route('/bluetooth/conectar', methods=['POST'])
@requiere_auth
def conectar_bluetooth():
    mac = request.form.get('mac')
    if not mac:
        flash("Falta la MAC del dispositivo.", "error")
        return redirect(url_for('inicio'))

    # Conectarse con el scan activo compite por el adaptador: el connect suele
    # colgar o fallar. Cortamos el scan y dejamos que bluetoothd suelte el
    # discovery antes de intentar el par.
    _detener_scan_proceso()
    time.sleep(1)

    try:
        subprocess.run(
            ["bluetoothctl", "pair", mac],
            capture_output=True, text=True, timeout=20,
        )
        subprocess.run(
            ["bluetoothctl", "trust", mac],
            capture_output=True, text=True, timeout=10,
        )
        conn = subprocess.run(
            ["bluetoothctl", "connect", mac],
            capture_output=True, text=True, timeout=20,
        )
        if conn.returncode != 0:
            detalle = (conn.stderr.strip() or conn.stdout.strip()
                       or "sin detalles. Verificá que el parlante esté encendido y en modo emparejamiento.")
            flash(f"Error conectando a {mac}: {detalle}", "error")
        else:
            # Conexión permanente: guardamos la MAC en config.yaml para que el
            # motor de audio la reconecte sola tras un reinicio.
            guardar_mac_parlante(mac)
            try:
                subprocess.run(["systemctl", "--user", "restart", "reproducir.service"],
                               capture_output=True, timeout=30, check=True)
            except Exception:
                pass  # Si el servicio no está corriendo, toma efecto en el próximo arranque.
            flash(f"Conectado exitosamente a {mac}. Queda configurado para reconectarse solo.", "success")
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

@app.route('/bluetooth/desconectar', methods=['POST'])
@requiere_auth
def desconectar_bluetooth():
    mac = request.form.get('mac')
    if not mac:
        flash("Falta la MAC del dispositivo.", "error")
        return redirect(url_for('inicio'))
    try:
        res = subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, text=True, timeout=15)
        salida = (res.stdout or '').strip()
        if res.returncode == 0 or 'not connected' in salida.lower():
            flash(f"Parlante {mac} desconectado.", "success")
        else:
            flash(f"Error desconectando {mac}: {salida or 'sin detalles'}", "error")
    except Exception as e:
        flash(f"Error desconectando {mac}: {e}", "error")
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
