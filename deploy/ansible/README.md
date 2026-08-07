# Ansible para Deploy Remoto

> Ansible te permite instalar o actualizar todas las Raspberry Pi de tu instalación al mismo tiempo, desde tu propia computadora, sin tener que entrar por SSH a cada una.

---

## Cuándo usar esto

- Tenés más de una Pi funcionando.
- Querés actualizar el código en todas a la vez sin repetir pasos.
- Querés mantener un registro centralizado de las IPs de todas tus Pi.

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

   # 2. Copiar la clave a la Voz A (cambiá la IP por la real)
   ssh-copy-id pi@192.168.1.100
   ```

## Cómo usarlo

1. Editá el archivo `inventory.ini` en esta carpeta y poné las IPs reales de tus Pi.
2. Editá `playbook.yml` y asegurate de que `repo_url` tenga tu usuario de GitHub.
3. Abrí una terminal en esta carpeta y corré:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Ansible se va a conectar a todas las Pi listadas en el inventario, va a verificar qué falta instalar o actualizar, y lo va a hacer automáticamente. Si algo ya está instalado y bien configurado, no hace nada (es "idempotente").
