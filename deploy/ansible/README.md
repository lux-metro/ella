# Ansible para Deploy Remoto

> Ansible te permite instalar o actualizar la Raspberry Pi de tu instalación desde tu propia computadora, sin tener que entrar por SSH.

---

## Cuándo usar esto

- Querés instalar o actualizar el código de la Pi sin repetir pasos.
- Querés mantener un registro centralizado de las IPs de tus Pi.

## Prerrequisitos (en tu PC con Linux)

1. Instalar Ansible:
   ```bash
   sudo apt update
   sudo apt install ansible
   ```

2. Configurar acceso SSH sin contraseña (SSH Keys):
   Ansible necesita poder entrar a las Pi sin que le pida la contraseña cada vez.
   ```bash
   # 1. Generar una clave en tu PC (si no tenés una, apretá Enter a todo)
   ssh-keygen -t rsa -b 4096

   # 2. Copiar la clave a la Pi (cambiá la IP por la real)
   ssh-copy-id pi@192.168.1.100
   ```

## Cómo usarlo

1. Editá el archivo `inventory.ini` en esta carpeta y poné la IP real de tu Pi.
2. Editá `playbook.yml` y asegurate de que `repo_url` tenga tu usuario de GitHub.
3. Abrí una terminal en esta carpeta y corré:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Ansible se va a conectar a la Pi listada en el inventario, va a verificar qué falta instalar o actualizar, y lo va a hacer automáticamente. Si algo ya está instalado y bien configurado, no hace nada (es "idempotente").

---

## ⚠️ Importante: no mezclar con `provision.sh`

`provision.sh` y Ansible son **flujos alternativos** de instalación:

- **`provision.sh`** instala los servicios como *servicios de usuario* (`panel`, `reproducir`, `sentir-presencia`) y es el flujo recomendado.
- **Ansible** instala el motor de audio como *servicio de sistema* (`ella-voice.service`).

Si configurás una Pi con `provision.sh` y después corrés Ansible, vas a terminar con **dos motores de audio a la vez**. Elegí un solo flujo por máquina.
