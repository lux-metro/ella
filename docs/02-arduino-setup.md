# Arduino — Setup y carga del firmware

> El Arduino es el "oído" del sistema: lee los sensores físicos (humedad de la arcilla, temperatura, luz) y manda esa información a la Raspberry Pi. Esta guía explica cómo cargar el programa en el Arduino desde cero.

---

## Qué vas a necesitar

- Arduino Uno (del Starter Kit)
- Cable USB tipo A a tipo B (el mismo que usás para impresoras viejas — viene en el Starter Kit)
- Tu computadora Linux
- Los sensores (opcional para empezar — podés probar sin ellos primero)

---

## Opción A — Arduino IDE (recomendada para empezar)

Arduino IDE es un programa gráfico con un botón grande que dice "Subir". Es la forma más fácil.

### Instalar Arduino IDE

1. En tu computadora, abrí una terminal y escribí:
   ```bash
   # Descargar el instalador
   wget https://downloads.arduino.cc/arduino-ide/arduino-ide_2.3.2_Linux_64bit.AppImage
   
   # Darle permisos de ejecución
   chmod +x arduino-ide_2.3.2_Linux_64bit.AppImage
   
   # Ejecutarlo
   ./arduino-ide_2.3.2_Linux_64bit.AppImage
   ```
   
   > Si no funciona `wget`, podés descargarlo manualmente desde [arduino.cc/en/software](https://www.arduino.cc/en/software) y elegir "Linux AppImage".

2. La primera vez que abrís Arduino IDE, puede pedir que instales controladores adicionales para el Arduino Uno. Aceptá todo.

### Abrir el firmware de ella

1. En Arduino IDE, ir a: **File → Open**
2. Navegar hasta la carpeta del proyecto: `ella/hardware/sensor_hub/`
3. Abrir el archivo `sensor_hub.ino`

### Conectar el Arduino y subir el firmware

1. Conectá el Arduino Uno a tu computadora con el cable USB
2. En Arduino IDE, verificar que esté seleccionado:
   - **Tools → Board → Arduino Uno**
   - **Tools → Port → /dev/ttyUSB0** (o similar — el que aparezca)
3. Hacé click en el botón **Upload** (flecha hacia la derecha →)
4. Esperá unos segundos. Si todo salió bien, vas a ver:
   ```
   Done uploading.
   ```

### Verificar que el Arduino está enviando datos

1. En Arduino IDE, abrí: **Tools → Serial Monitor**
2. Abajo a la derecha, verificá que la velocidad diga **9600 baud**
3. Deberías ver líneas de texto como:
   ```json
   {"humidity":65,"temperature":22,"light":180}
   {"humidity":64,"temperature":22,"light":181}
   ```
   
   Eso significa que el Arduino está leyendo sensores y mandando datos. ✅

---

## Opción B — arduino-cli desde terminal (más automatizable)

`arduino-cli` es una herramienta de línea de comandos. Permite subir firmware con un solo comando, lo que facilita re-deploys futuros.

### Instalar arduino-cli

```bash
# Descargar e instalar
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Mover al path del sistema
sudo mv bin/arduino-cli /usr/local/bin/

# Verificar instalación
arduino-cli version
```

### Configurar para Arduino Uno

```bash
# Inicializar configuración
arduino-cli config init

# Agregar índice de placas de Arduino
arduino-cli core update-index

# Instalar soporte para Arduino Uno (AVR)
arduino-cli core install arduino:avr
```

### Subir el firmware

```bash
# Desde la raíz del proyecto ella:
arduino-cli compile --fqbn arduino:avr:uno hardware/sensor_hub/
arduino-cli upload  --fqbn arduino:avr:uno --port /dev/ttyUSB0 hardware/sensor_hub/
```

> Reemplazá `/dev/ttyUSB0` por el puerto que muestra tu sistema. Para verlo:
> ```bash
> ls /dev/ttyUSB* /dev/ttyACM*
> ```
> Conectá y desconectá el Arduino para ver cuál aparece y desaparece.

---

## ¿Qué hace el firmware?

El programa en el Arduino (`sensor_hub.ino`) hace tres cosas:

1. **Lee los sensores** cada 500 milisegundos
2. **Manda los datos** por el cable USB (o luego por los pines UART) en formato JSON
3. **Nunca se bloquea** — usa `millis()` en lugar de `delay()` para no perder lecturas

El formato de los datos es:
```json
{"humidity":65,"temperature":22,"light":180,"ok":true}
```

Donde:
- `humidity`: 0-1023 (valor crudo del sensor analógico)
- `temperature`: temperatura en décimas de grado (220 = 22.0°C)
- `light`: 0-1023 (0 = oscuridad total, 1023 = luz máxima)
- `ok`: siempre `true` si el Arduino está funcionando (útil para detectar si se colgó)

---

## Conexión física de los sensores

Los sensores se conectan a los pines analógicos del Arduino (A0, A1, A2).

| Sensor | Pin del Arduino | Color de cable recomendado |
|--------|----------------|---------------------------|
| Sensor humedad suelo (señal) | A0 | Amarillo |
| Sensor temperatura LM35 (señal) | A1 | Naranja |
| Fotoresistor / LDR (señal) | A2 | Verde |
| Alimentación (todos) | 5V | Rojo |
| Tierra (todos) | GND | Negro |

> Ver diagrama detallado con colores en [04-wiring.md](04-wiring.md)

---

## Resolución de problemas

**El puerto `/dev/ttyUSB0` no aparece:**
```bash
# Verificar que el usuario tiene permisos para acceder al puerto serial
sudo usermod -a -G dialout $USER
# Cerrar sesión y volver a entrar para que tome efecto
```

**El Arduino IDE dice "Board not found":**
- Probá otro cable USB (muchos cables de Arduino solo cargan pero no transmiten datos)
- Verificá que el Arduino esté bien conectado

**Los datos en el Serial Monitor son caracteres extraños:**
- Verificar que la velocidad en Serial Monitor sea 9600 baud (no 115200 ni otro valor)

---

*← [01-raspberry-pi-setup.md](01-raspberry-pi-setup.md) | Siguiente: [03-audio-setup.md](03-audio-setup.md) →*
