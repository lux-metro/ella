# Notas de Prototipado y Experimentos

Esta carpeta sirve para documentar pruebas previas.

## 2026-08 - Pruebas iniciales con Pi Zero 2 W y Bluetooth

Se probó usar una Raspberry Pi Zero 2 W para la instalación.

**Conclusiones:**
- Sirvió perfectamente para probar el concepto del script en bash con `sox` y `play`.
- El audio salía sin problema a un parlante Bluetooth.
- **Descartada para la instalación final:** La Pi Zero no tiene salida de audio analógica de 3.5mm nativa. Para conectar el amplificador de los exciters se necesita sí o sí una salida analógica (o agregarle un DAC I2S, lo que complica el hardware).
- **Decisión:** Usar las Raspberry Pi 3 Model B, que ya tienen conector de 3.5mm integrado.

**Actualización posterior (decisión final):** La instalación final usa **una sola Raspberry Pi** y la salida de audio es por **parlante Bluetooth** (no exciters). Las notas de 3.5mm/exciters quedan como registro histórico de esta etapa de prototipado.

## 2026-08 - Pruebas con sox (bash)

El script `play_random.sh` (en esta misma carpeta) validó que:
- Modificar el tempo en tiempo real no interrumpe el flujo.
- Modificar el pitch con `cents` permite variaciones sutiles muy agradables para texturas.
- `sox` es lo suficientemente liviano para correr en la Pi sin consumir toda la CPU.
