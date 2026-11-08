# Bot de Gamer Tags para Discord

Bot en Python para un canal #gamer-tags que evita publicar gamer tags (Activision ID) duplicados. Cuando alguien publica un duplicado, el bot lo borra y le indica dónde está el gamer tag original con un enlace directo. Usa discord.py, python-dotenv y SQLite.

## Requisitos

- Python 3.11 o superior
- Windows 10/11 o Linux (probado en Kali Linux)
- Una cuenta de Discord con permiso para añadir bots al servidor

## Importante antes de usarlo

- Usa un canal exclusivo para gamer tags. El bot solo permite mensajes con formato Activision ID (`Nombre#1234567`).
- Cada vez que el bot arranca, borra del canal todos los mensajes que no sean un gamer tag válido (mensajes normales, comandos y mensajes de bots, también los antiguos). No lo configures en un canal donde quieras conservar otro tipo de mensajes.
- La base de datos (`gamer_tags.db`) es local. Cada servidor debe ejecutar su propia copia del bot con su propio token.

## 1. Crear el bot en Discord

1. Entra a [Discord Developer Portal](https://discord.com/developers/applications) y pulsa New Application.
2. Abre la pestaña Bot y copia el token (Reset Token / Copy). No lo compartas con nadie.
3. En Privileged Gateway Intents activa Message Content Intent. Sin esto el bot no puede leer los mensajes.
4. Ve a OAuth2 → URL Generator, marca el scope `bot` y estos permisos:
   - View Channels
   - Send Messages
   - Manage Messages (para borrar duplicados)
   - Read Message History
5. Abre la URL generada y añade el bot a tu servidor.
6. En Discord activa Ajustes → Avanzado → Modo desarrollador, haz clic derecho en el canal de gamer tags y elige Copiar ID del canal.

## 2. Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/Alex121216/Discord_bot.git
   cd Discord_bot
   ```

### Windows

2. Crear entorno virtual (recomendado):

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Instalar dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:

   - Copia `.env.example` a `.env`:
     ```powershell
     copy .env.example .env
     ```
   - Edita `.env` y rellena:
     - `DISCORD_TOKEN`: token del bot.
     - `CHANNEL_ID`: ID del canal de gamer tags.
     - `BOT_PREFIX`: prefijo de comandos (por defecto `!`).
     - `DB_FILE`: ruta del archivo SQLite (por defecto `gamer_tags.db`).

### Linux / Kali Linux

2. Dependencias del sistema (si aún no las tienes):

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip git
   ```

3. Instalación automática (recomendado):

   ```bash
   chmod +x install.sh run_bot.sh
   ./install.sh
   ```

   El script crea el entorno virtual, instala dependencias y copia `.env.example` a `.env` si no existe.

4. Instalación manual (alternativa):

   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   cp .env.example .env
   ```

5. Configurar `.env` (igual que en Windows):

   ```bash
   nano .env
   ```

   Rellena `DISCORD_TOKEN`, `CHANNEL_ID`, `BOT_PREFIX` y `DB_FILE`.

## 3. Ejecución

### Opción normal (una vez)

Windows (con el entorno virtual activado):

```powershell
python bot.py
```

Linux / Kali:

```bash
./venv/bin/python bot.py
```

### Opción recomendada: reinicio automático (cortes de red)

Para que el bot se reinicie solo si se cae por corte de red o error:

- Windows (PowerShell): `.\run_bot.ps1`
- Windows (CMD): `run_bot.bat` o doble clic en `run_bot.bat`
- Linux / Kali: `./run_bot.sh`

Si el proceso termina, espera 10 segundos y vuelve a lanzar el bot. Para detenerlo, pulsa Ctrl+C (o cierra la ventana en Windows).

### Desconexión de red

- Cortes breves: discord.py reconecta solo; no hace falta hacer nada.
- Cortes largos o si el bot termina: usa `run_bot.ps1`, `run_bot.bat` o `run_bot.sh` para reinicio automático a los 10 segundos.

## Comportamiento

En cada arranque el bot:

- Crea la base de datos y las tablas si no existen.
- Borra del canal los mensajes que no son gamer tags válidos (incluidos los mensajes de bots).
- En la primera ejecución, escanea el historial del canal (del más antiguo al más nuevo), guarda la primera aparición de cada gamer tag y borra los duplicados, dejando solo la copia más antigua.

Durante el uso normal:

- Solo actúa en el canal definido por `CHANNEL_ID`.
- Toma el mensaje completo como gamer tag y exige el formato Activision ID: nombre de 2 a 16 caracteres, un `#` y solo números (ejemplo: `Gamer#1234567`). Cualquier otro mensaje se borra y se avisa al usuario.
- Normaliza antes de comparar: quita espacios al inicio/final, unifica espacios múltiples y compara sin distinguir mayúsculas/minúsculas.
- Si el tag no existe: lo guarda y deja el mensaje.
- Si el tag ya existe: borra el mensaje y responde al usuario con un enlace directo al gamer tag original: *"Este gamer tag ya está en la lista, lo puedes ver aquí: [enlace]"*. El aviso se borra solo a los 15 segundos.
- Si un usuario edita un mensaje y el nuevo texto es un duplicado, también se borra y recibe el mismo aviso con el enlace.
- Si se borra el mensaje que registró un tag, ese tag queda libre de nuevo.
- Ignora los mensajes de otros bots.

## Comandos (solo administradores / gestión del servidor)

Todos usan el prefijo configurado (por defecto `!`), solo funcionan en el canal de gamer tags y el mensaje del comando se borra a los 10 segundos.

| Comando | Descripción |
|---------|-------------|
| `!checktag <tag>` | Indica si ese gamer tag ya está registrado. |
| `!removetag <tag>` | Elimina ese gamer tag de la base de datos (queda libre para publicar de nuevo). |
| `!rebuildtags` | Borra los tags del canal en la BD, vuelve a construirlos leyendo el historial y elimina del canal los mensajes duplicados (deja solo el más antiguo). |
| `!cleanduplicates` | Borra del canal los mensajes duplicados que existan ahora, dejando solo la copia más antigua de cada tag. No modifica la base de datos. |

## Base de datos

- Archivo por defecto: `gamer_tags.db` (configurable con `DB_FILE`).
- Tabla gamer_tags: `message_id`, `normalized_tag`, `original_tag`, `channel_id`, `author_id`, `created_at`.
- Tabla meta: control de si el canal ya fue escaneado al arrancar.

## Estructura del proyecto

```
Discord_bot/
├── bot.py           # Código principal del bot
├── install.sh       # Instalación en Linux / Kali
├── run_bot.sh       # Ejecutar con reinicio automático (Linux / Kali)
├── run_bot.ps1      # Ejecutar con reinicio automático (PowerShell)
├── run_bot.bat      # Ejecutar con reinicio automático (Windows CMD)
├── requirements.txt # Dependencias Python
├── .env.example     # Plantilla de variables de entorno
├── .env             # Tus variables (no subir a Git)
├── gamer_tags.db    # Base SQLite (se crea al ejecutar, no subir a Git)
└── README.md        # Este archivo
```

## Resumen rápido

Windows

1. Crear el bot en el Developer Portal, activar Message Content Intent e invitarlo al servidor con los permisos indicados
2. `git clone https://github.com/Alex121216/Discord_bot.git`
3. `pip install -r requirements.txt`
4. Copiar `.env.example` → `.env` y rellenar `DISCORD_TOKEN` y `CHANNEL_ID`
5. Ejecutar: `python bot.py` o `.\run_bot.ps1`

Linux / Kali

1. Crear el bot en el Developer Portal, activar Message Content Intent e invitarlo al servidor con los permisos indicados
2. `git clone https://github.com/Alex121216/Discord_bot.git && cd Discord_bot`
3. `chmod +x install.sh run_bot.sh && ./install.sh`
4. Editar `.env` con `DISCORD_TOKEN` y `CHANNEL_ID`
5. Ejecutar: `./run_bot.sh`
