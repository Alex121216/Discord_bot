# Bot de Gamer Tags para Discord

Bot en Python para un canal **#gamer-tags** que evita publicar gamer tags duplicados. Usa **discord.py**, **python-dotenv** y **SQLite**.

## Requisitos

- Python 3.11 o superior
- Windows 10/11 o Linux (probado en Kali Linux)

## Instalación

1. **Clonar o copiar** la carpeta del bot en tu equipo.

### Windows

2. **Crear entorno virtual** (recomendado):

   ```powershell
   cd "C:\Users\alexe\My Drive\Programming\Discord_bot"
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Instalar dependencias**:

   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:

   - Copia `.env.example` a `.env`:
     ```powershell
     copy .env.example .env
     ```
   - Edita `.env` y rellena:
     - `DISCORD_TOKEN`: token del bot (Developer Portal → Application → Bot → Reset Token / Copy).
     - `CHANNEL_ID`: ID del canal #gamer-tags (clic derecho en el canal → Copiar ID; si no ves la opción, activa "Modo desarrollador" en Discord).
     - `BOT_PREFIX`: prefijo de comandos (por defecto `!`).
     - `DB_FILE`: ruta del archivo SQLite (por defecto `gamer_tags.db`).

### Linux / Kali Linux

2. **Dependencias del sistema** (si aún no las tienes):

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip git
   ```

3. **Instalación automática** (recomendado):

   ```bash
   cd Discord_bot
   chmod +x install.sh run_bot.sh
   ./install.sh
   ```

   El script crea el entorno virtual, instala dependencias y copia `.env.example` a `.env` si no existe.

4. **Instalación manual** (alternativa):

   ```bash
   cd Discord_bot
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   cp .env.example .env
   ```

5. **Configurar `.env`** (igual que en Windows):

   ```bash
   nano .env
   ```

   Rellena `DISCORD_TOKEN`, `CHANNEL_ID`, `BOT_PREFIX` y `DB_FILE`.

## Ejecución

### Opción normal (una vez)

**Windows** (con el entorno virtual activado):

```powershell
python bot.py
```

**Linux / Kali**:

```bash
./venv/bin/python bot.py
```

### Opción recomendada: reinicio automático (cortes de red)

Para que el bot se **reinicie solo** si se cae por corte de red o error:

- **Windows (PowerShell):** `.\run_bot.ps1`
- **Windows (CMD):** `run_bot.bat` o doble clic en `run_bot.bat`
- **Linux / Kali:** `./run_bot.sh`

Si el proceso termina, espera 10 segundos y vuelve a lanzar el bot. Para detenerlo, pulsa Ctrl+C (o cierra la ventana en Windows).

### Desconexión de red

- **Cortes breves:** discord.py **reconecta solo**; no hace falta hacer nada.
- **Cortes largos o si el bot termina:** usa `run_bot.ps1`, `run_bot.bat` o `run_bot.sh` para reinicio automático a los 10 segundos.

---

En la primera ejecución el bot:

- Crea la base de datos y las tablas si no existen.
- Escanea el historial del canal (del más antiguo al más nuevo) y guarda la primera aparición de cada gamer tag.

## Permisos del bot en Discord

En el servidor, el bot debe tener en el canal #gamer-tags (o a nivel de servidor si aplica):

- **View Channels** (ver canales)
- **Send Messages** (enviar mensajes)
- **Manage Messages** (gestionar mensajes, para borrar duplicados)
- **Read Message History** (leer historial, para el escaneo inicial y comandos)

## Developer Portal: Message Content Intent

En [Discord Developer Portal](https://discord.com/developers/applications):

1. Entra a tu aplicación → **Bot**.
2. En **Privileged Gateway Intents** activa **Message Content Intent**.

Si no está activado, el bot no podrá leer el contenido de los mensajes y no funcionará correctamente.

## Comportamiento

- Solo actúa en el canal definido por `CHANNEL_ID`.
- Toma el mensaje completo como gamer tag.
- Normaliza antes de comparar: quita espacios al inicio/final, unifica espacios múltiples y compara sin distinguir mayúsculas/minúsculas.
- Si el tag *no existe*: lo guarda y deja el mensaje.
- Si el tag *ya existe*: borra el mensaje y envía un aviso breve.
- En el *escaneo inicial* (y con `!rebuildtags`): además de registrar los tags, *borra del canal* los mensajes duplicados y deja solo la *copia más antigua* de cada tag.
- Si un usuario *edita* un mensaje y el nuevo texto es un duplicado, también se borra.
- Si se *borra* el mensaje que registró un tag, ese tag queda libre de nuevo.
- *Ignora* mensajes de otros bots y mensajes vacíos.

## Comandos (solo administradores / gestión del servidor)

Todos usan el prefijo configurado (por defecto `!`) y solo en el canal de gamer tags:

| Comando               | Descripción                                                                 |
|----------------------------------------------------------------------------------------|
| `!checktag <tag>`    | Indica si ese gamer tag ya está registrado.                                  |
| `!removetag <tag>`   | Elimina ese gamer tag de la base de datos (queda libre para publicar de nuevo). |
| `!rebuildtags`       | Borra los tags del canal en la BD, vuelve a construirlos leyendo el historial y *elimina del canal* los mensajes duplicados (deja solo el más antiguo). |
| `!cleanduplicates`  | Borra del canal los mensajes duplicados que existan ahora, dejando solo la copia más antigua de cada tag. No modifica la base de datos. |

## Base de datos

- Archivo por defecto: `gamer_tags.db` (configurable con `DB_FILE`).
- Tabla **gamer_tags**: `message_id`, `normalized_tag`, `original_tag`, `channel_id`, `author_id`, `created_at`.
- Tabla **meta**: control de si el canal ya fue escaneado al arrancar.

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
├── gamer_tags.db    # Base SQLite (se crea al ejecutar)
└── README.md        # Este archivo
```

## Resumen rápido

**Windows**

1. `pip install -r requirements.txt`
2. Copiar `.env.example` → `.env` y rellenar `DISCORD_TOKEN` y `CHANNEL_ID`
3. Activar **Message Content Intent** en el Developer Portal
4. Dar al bot: View Channels, Send Messages, Manage Messages, Read Message History
5. Ejecutar: `python bot.py` o `.\run_bot.ps1`

**Linux / Kali**

1. `chmod +x install.sh run_bot.sh && ./install.sh`
2. Editar `.env` con `DISCORD_TOKEN` y `CHANNEL_ID`
3. Activar **Message Content Intent** en el Developer Portal
4. Dar al bot los mismos permisos en Discord
5. Ejecutar: `./run_bot.sh`
