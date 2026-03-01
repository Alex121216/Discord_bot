# Bot de Gamer Tags para Discord

Bot en Python para un canal **#gamer-tags** que evita publicar gamer tags duplicados. Usa **discord.py**, **python-dotenv** y **SQLite**.

## Requisitos

- Python 3.11 o superior
- Windows (probado en Windows 10/11)

## Instalación

1. **Clonar o copiar** la carpeta del bot en tu equipo.

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

## Ejecución

### Opción normal (una vez)

Con el entorno virtual activado:

```powershell
python bot.py
```

### Opción recomendada: reinicio automático (cortes de red)

Para que el bot se **reinicie solo** si se cae por corte de red o error:

- **PowerShell:** ejecuta `.\run_bot.ps1`
- **Símbolo del sistema:** ejecuta `run_bot.bat` o haz doble clic en `run_bot.bat`

Si el proceso termina, espera 10 segundos y vuelve a lanzar el bot. Para detenerlo, cierra la ventana o pulsa Ctrl+C.

### Desconexión de red

- **Cortes breves:** discord.py **reconecta solo**; no hace falta hacer nada.
- **Cortes largos o si el bot termina:** si usas `run_bot.ps1` o `run_bot.bat`, el bot se reiniciará a los 10 segundos. Si no, abre de nuevo PowerShell en la carpeta del bot y ejecuta `python bot.py` (o `.\venv\Scripts\python.exe bot.py`).

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
├── run_bot.ps1      # Ejecutar con reinicio automático (PowerShell)
├── run_bot.bat      # Ejecutar con reinicio automático (doble clic)
├── requirements.txt # Dependencias Python
├── .env.example     # Plantilla de variables de entorno
├── .env             # Tus variables (no subir a Git)
├── gamer_tags.db    # Base SQLite (se crea al ejecutar)
└── README.md        # Este archivo
```

## Resumen rápido

1. Instalar dependencias: `pip install -r requirements.txt`
2. Copiar `.env.example` → `.env` y rellenar `DISCORD_TOKEN` y `CHANNEL_ID`
3. Activar **Message Content Intent** en el Developer Portal
4. Dar al bot: View Channels, Send Messages, Manage Messages, Read Message History
5. Ejecutar: `python bot.py`
