"""
Bot de Discord para el canal #gamer-tags.
Evita gamer tags duplicados usando SQLite y escaneo del historial.
"""

import os
import sqlite3
import re
import asyncio
from datetime import datetime
from contextlib import contextmanager

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
DB_FILE = os.getenv("DB_FILE", "gamer_tags.db")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN no está definido en .env")

# Intents necesarios: mensajes, contenido de mensajes, guilds
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


# ---------------------------------------------------------------------------
# Base de datos SQLite
# ---------------------------------------------------------------------------

@contextmanager
def get_db():
    """Context manager para conexiones a la base de datos."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gamer_tags (
                message_id TEXT PRIMARY KEY,
                normalized_tag TEXT NOT NULL,
                original_tag TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Índice para búsquedas por canal y tag normalizado
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_gamer_tags_channel_normalized
            ON gamer_tags(channel_id, normalized_tag)
        """)


def is_channel_scanned(channel_id: int) -> bool:
    """Comprueba si el canal ya fue escaneado al arrancar."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = ?",
            (f"scanned_{channel_id}",)
        ).fetchone()
        return row is not None and row["value"] == "1"


def set_channel_scanned(channel_id: int):
    """Marca el canal como escaneado."""
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (f"scanned_{channel_id}", "1")
        )


def tag_exists(channel_id: int, normalized_tag: str) -> bool:
    """Indica si ya existe un gamer tag (normalizado) en el canal."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM gamer_tags WHERE channel_id = ? AND normalized_tag = ?",
            (channel_id, normalized_tag)
        ).fetchone()
        return row is not None


def insert_tag(message_id: int, normalized_tag: str, original_tag: str,
               channel_id: int, author_id: int) -> None:
    """Guarda un nuevo gamer tag."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO gamer_tags
               (message_id, normalized_tag, original_tag, channel_id, author_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(message_id),
                normalized_tag,
                original_tag,
                channel_id,
                author_id,
                datetime.utcnow().isoformat(),
            ),
        )


def remove_tag_by_message_id(message_id: int) -> bool:
    """Elimina un tag por ID de mensaje. Devuelve True si se eliminó algo."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM gamer_tags WHERE message_id = ?", (str(message_id),))
        return cur.rowcount > 0


def remove_tag_by_normalized(channel_id: int, normalized_tag: str) -> bool:
    """Elimina el registro del gamer tag normalizado en el canal. Devuelve True si se eliminó."""
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM gamer_tags WHERE channel_id = ? AND normalized_tag = ?",
            (channel_id, normalized_tag),
        )
        return cur.rowcount > 0


def clear_channel_tags(channel_id: int) -> None:
    """Borra todos los gamer tags del canal."""
    with get_db() as conn:
        conn.execute("DELETE FROM gamer_tags WHERE channel_id = ?", (channel_id,))


def get_tag_info(channel_id: int, normalized_tag: str) -> sqlite3.Row | None:
    """Obtiene la primera fila del tag normalizado en el canal (si existe)."""
    with get_db() as conn:
        return conn.execute(
            """SELECT message_id, original_tag, author_id, created_at
               FROM gamer_tags WHERE channel_id = ? AND normalized_tag = ?
               LIMIT 1""",
            (channel_id, normalized_tag),
        ).fetchone()


def upsert_tag_for_message(message_id: int, normalized_tag: str, original_tag: str,
                           channel_id: int, author_id: int) -> None:
    """Inserta o actualiza el gamer tag asociado a un message_id."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO gamer_tags
               (message_id, normalized_tag, original_tag, channel_id, author_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(message_id) DO UPDATE SET
                 normalized_tag = excluded.normalized_tag,
                 original_tag = excluded.original_tag""",
            (
                str(message_id),
                normalized_tag,
                original_tag,
                channel_id,
                author_id,
                datetime.utcnow().isoformat(),
            ),
        )


# ---------------------------------------------------------------------------
# Validación y normalización de gamer tags
# ---------------------------------------------------------------------------

# Formato según requisitos de Call of Duty / Activision ID: nombre de 2-16 caracteres.
# Caracteres permitidos: letras, números, guión bajo, guión, punto.
# Opcionalmente "#" y dígitos para el identificador único (ej. Usuario#1234567).
GAMER_TAG_PATTERN = re.compile(
    r"^[a-zA-Z0-9_\-.]{2,16}(?:#[0-9]+)?$"
)
GAMER_TAG_MIN_LEN = 2   # Call of Duty / Activision: mínimo 2 caracteres
GAMER_TAG_MAX_LEN = 16  # Call of Duty / Activision: máximo 16 caracteres (solo el nombre)


def is_valid_gamer_tag(text: str) -> bool:
    """
    Comprueba si el texto es un gamer tag válido según requisitos de Call of Duty.
    El nombre (parte antes de #) debe tener entre 2 y 16 caracteres.
    """
    if not text or not isinstance(text, str):
        return False
    cleaned = text.strip()
    # La parte del nombre (antes de #) debe tener 2-16 caracteres
    name_part = cleaned.split("#")[0] if "#" in cleaned else cleaned
    if len(name_part) < GAMER_TAG_MIN_LEN or len(name_part) > GAMER_TAG_MAX_LEN:
        return False
    return bool(GAMER_TAG_PATTERN.fullmatch(cleaned))


def normalize_tag(text: str) -> str:
    """
    Normaliza el texto del gamer tag:
    - Quita espacios al inicio y al final
    - Convierte múltiples espacios en uno solo
    - Minúsculas para comparación
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


# ---------------------------------------------------------------------------
# Escaneo del historial
# ---------------------------------------------------------------------------

async def scan_channel_history(channel: discord.TextChannel, delete_duplicates: bool = True) -> int:
    """
    Recorre el historial del canal del más viejo al más nuevo y guarda
    la primera aparición de cada gamer tag. Si delete_duplicates es True,
    borra en el canal los mensajes duplicados (deja solo la copia más antigua).
    Devuelve la cantidad de tags registrados en este escaneo.
    """
    count = 0
    try:
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                continue
            content = (message.content or "").strip()
            if not content:
                continue
            if not is_valid_gamer_tag(content):
                continue
            normalized = normalize_tag(content)
            if not normalized:
                continue
            if tag_exists(channel.id, normalized):
                # Ya existe una copia más antigua: borrar este mensaje duplicado del canal
                if delete_duplicates:
                    info = get_tag_info(channel.id, normalized)
                    if info and str(info["message_id"]) != str(message.id):
                        try:
                            await message.delete()
                            await asyncio.sleep(0.6)  # evitar rate limit de Discord
                        except discord.Forbidden:
                            pass
                        except discord.HTTPException:
                            pass
                continue
            insert_tag(
                message.id,
                normalized,
                content,
                channel.id,
                message.author.id,
            )
            count += 1
    except discord.Forbidden:
        raise
    except Exception as e:
        print(f"Error durante el escaneo del historial: {e}")
    return count


async def clean_non_gamertag_messages(channel: discord.TextChannel) -> int:
    """
    Recorre el canal y borra todos los mensajes que NO son gamer tags válidos:
    - Todos los mensajes enviados por bots (incluidos los del propio bot).
    - Todos los mensajes de usuarios que no cumplan el formato de gamer tag.
    Se ejecuta en cada arranque del bot. Devuelve cuántos mensajes se borraron.
    """
    deleted = 0
    try:
        async for message in channel.history(limit=None, oldest_first=True):
            # Borrar siempre los mensajes de cualquier bot (servicio, avisos, etc.)
            if message.author.bot:
                try:
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.6)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
                continue
            # Mensajes de usuarios: borrar si están vacíos o no son gamer tag válido
            content = (message.content or "").strip()
            if not content or not is_valid_gamer_tag(content):
                try:
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.6)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
    except discord.Forbidden:
        raise
    except Exception as e:
        print(f"Error al limpiar mensajes que no son gamer tags: {e}")
    return deleted


async def clean_duplicate_messages(channel: discord.TextChannel) -> int:
    """
    Recorre el canal y borra los mensajes que son duplicados (mismo tag que uno
    ya registrado), dejando solo la copia más antigua. Devuelve cuántos se borraron.
    """
    deleted = 0
    try:
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                continue
            content = (message.content or "").strip()
            if not content:
                continue
            normalized = normalize_tag(content)
            if not normalized:
                continue
            info = get_tag_info(channel.id, normalized)
            if info is None:
                continue
            # Este tag ya está registrado; si este mensaje no es el que guardamos, es duplicado
            if str(info["message_id"]) != str(message.id):
                try:
                    await message.delete()
                    deleted += 1
                    await asyncio.sleep(0.6)
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
    except discord.Forbidden:
        raise
    except Exception as e:
        print(f"Error al limpiar duplicados: {e}")
    return deleted


# ---------------------------------------------------------------------------
# Eventos del bot
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    """Al conectar, inicializar DB y escanear el canal si es la primera vez."""
    if bot.user:
        print(f"Conectado como {bot.user} (ID: {bot.user.id})")
    else:
        print("Bot conectado pero usuario no disponible aún.")
    init_db()
    if CHANNEL_ID:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            try:
                channel = await bot.fetch_channel(CHANNEL_ID)
            except discord.NotFound:
                print(f"Advertencia: no se encontró el canal con ID {CHANNEL_ID}")
                return
        if channel and isinstance(channel, discord.TextChannel):
            # Cada vez que arranca el bot: borrar mensajes que no son gamer tags (incl. mensajes del bot)
            try:
                n_deleted = await clean_non_gamertag_messages(channel)
                if n_deleted > 0:
                    print(f"Limpieza al arranque: {n_deleted} mensajes eliminados (no gamer tags o del bot).")
            except discord.Forbidden:
                print("Sin permiso para leer/borrar mensajes en el canal.")
            except Exception as e:
                print(f"Error en limpieza al arranque: {e}")
            # Primera vez: escanear historial y registrar gamer tags
            if not is_channel_scanned(CHANNEL_ID):
                print(f"Primera ejecución: escaneando historial de #{channel.name}...")
                try:
                    n = await scan_channel_history(channel)
                    set_channel_scanned(CHANNEL_ID)
                    print(f"Escaneo completado. {n} gamer tags registrados.")
                except discord.Forbidden:
                    print("Sin permiso para leer el historial del canal.")
                except Exception as e:
                    print(f"Error en escaneo inicial: {e}")


@bot.event
async def on_message(message: discord.Message):
    # No actuar en otros canales: solo procesar comandos y salir
    if message.channel.id != CHANNEL_ID:
        await bot.process_commands(message)
        return

    # Ignorar otros bots
    if message.author.bot:
        return

    # Procesar comandos con prefijo en el canal permitido
    if message.content and message.content.strip().startswith(BOT_PREFIX):
        await bot.process_commands(message)
        return

    # Mensajes vacíos
    content = (message.content or "").strip()
    if not content:
        return

    # Borrar cualquier mensaje que no sea un gamer tag válido
    if not is_valid_gamer_tag(content):
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.channel.send(
                "Solo se permiten gamer tags de Call of Duty (2-16 caracteres, ej: MiUsuario o Gamer#1234567).",
                delete_after=10,
            )
        except discord.HTTPException:
            pass
        return

    normalized = normalize_tag(content)
    if not normalized:
        return

    if tag_exists(message.channel.id, normalized):
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        try:
            await message.channel.send(
                "Ese gamer tag ya fue publicado antes.",
                delete_after=10,
            )
        except discord.HTTPException:
            pass
        return

    # Nuevo tag: guardar y dejar pasar
    try:
        insert_tag(
            message.id,
            normalized,
            content,
            message.channel.id,
            message.author.id,
        )
    except Exception as e:
        print(f"Error al guardar gamer tag: {e}")
        try:
            await message.channel.send("Error al registrar el tag. Intenta más tarde.")
        except discord.HTTPException:
            pass

    await bot.process_commands(message)


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Si se edita un mensaje: borrar si no es gamer tag válido o si es duplicado."""
    if after.channel.id != CHANNEL_ID:
        return
    if after.author.bot:
        return

    content = (after.content or "").strip()
    if not content:
        return

    # Si el mensaje editado ya no es un gamer tag válido, borrarlo
    if not is_valid_gamer_tag(content):
        remove_tag_by_message_id(after.id)
        try:
            await after.delete()
        except discord.Forbidden:
            pass
        try:
            await after.channel.send(
                "Solo se permiten gamer tags de Call of Duty (2-16 caracteres, ej: MiUsuario o Gamer#1234567).",
                delete_after=10,
            )
        except discord.HTTPException:
            pass
        return

    normalized = normalize_tag(content)
    if not normalized:
        return

    # Si el mensaje editado ya existía con ese contenido, no es duplicado por sí mismo
    # Comprobamos si existe otro registro (otro message_id) con el mismo tag
    with get_db() as conn:
        existing = conn.execute(
            """SELECT message_id FROM gamer_tags
               WHERE channel_id = ? AND normalized_tag = ? AND message_id != ?""",
            (after.channel.id, normalized, str(after.id)),
        ).fetchone()

    if existing is not None:
        # Liberar el tag que tenía este mensaje antes de borrarlo
        remove_tag_by_message_id(after.id)
        try:
            await after.delete()
        except discord.Forbidden:
            pass
        try:
            await after.channel.send(
                "Ese gamer tag ya fue publicado antes.",
                delete_after=10,
            )
        except discord.HTTPException:
            pass
        return

    # No es duplicado: insertar o actualizar el registro de este mensaje
    try:
        upsert_tag_for_message(
            after.id,
            normalized,
            content,
            after.channel.id,
            after.author.id,
        )
    except Exception as e:
        print(f"Error al actualizar gamer tag editado: {e}")


@bot.event
async def on_message_delete(message: discord.Message):
    """Si se borra un mensaje, liberar ese gamer tag."""
    if message.channel.id != CHANNEL_ID:
        return
    remove_tag_by_message_id(message.id)


# ---------------------------------------------------------------------------
# Comandos de administrador
# ---------------------------------------------------------------------------

def is_admin_or_manage_guild(ctx: commands.Context) -> bool:
    """Comprueba si el usuario tiene permiso de administrador o gestionar servidor."""
    if not ctx.author.guild_permissions.administrator:
        if not ctx.author.guild_permissions.manage_guild:
            return False
    return True


@bot.command(name="checktag")
@commands.guild_only()
async def cmd_checktag(ctx: commands.Context, *, tag: str = ""):
    """
    Comprueba si un gamer tag ya existe en el canal.
    Uso: !checktag <tag>
    Solo administradores o gestión del servidor.
    """
    if not is_admin_or_manage_guild(ctx):
        await ctx.send("No tienes permiso para usar este comando.", delete_after=8)
        return
    if ctx.channel.id != CHANNEL_ID:
        await ctx.send("Este comando solo puede usarse en el canal de gamer tags.", delete_after=8)
        return

    tag = tag.strip()
    if not tag:
        await ctx.send("Debes indicar un tag. Ejemplo: `!checktag MiGamerTag`", delete_after=10)
        return

    normalized = normalize_tag(tag)
    if not normalized:
        await ctx.send("El tag no puede estar vacío.", delete_after=8)
        return

    info = get_tag_info(CHANNEL_ID, normalized)
    if info is None:
        await ctx.send(f"El gamer tag **{discord.utils.escape_markdown(normalized)}** no está registrado.")
        return

    await ctx.send(
        f"El gamer tag **{discord.utils.escape_markdown(normalized)}** ya existe "
        f"(registrado el {info['created_at'][:10]})."
    )


@bot.command(name="removetag")
@commands.guild_only()
async def cmd_removetag(ctx: commands.Context, *, tag: str = ""):
    """
    Elimina manualmente un gamer tag de la base de datos.
    Uso: !removetag <tag>
    Solo administradores o gestión del servidor.
    """
    if not is_admin_or_manage_guild(ctx):
        await ctx.send("No tienes permiso para usar este comando.", delete_after=8)
        return
    if ctx.channel.id != CHANNEL_ID:
        await ctx.send("Este comando solo puede usarse en el canal de gamer tags.", delete_after=8)
        return

    tag = tag.strip()
    if not tag:
        await ctx.send("Debes indicar un tag. Ejemplo: `!removetag MiGamerTag`", delete_after=10)
        return

    normalized = normalize_tag(tag)
    if not normalized:
        await ctx.send("El tag no puede estar vacío.", delete_after=8)
        return

    removed = remove_tag_by_normalized(CHANNEL_ID, normalized)
    if removed:
        await ctx.send(f"Gamer tag **{discord.utils.escape_markdown(normalized)}** eliminado de la base de datos.")
    else:
        await ctx.send(f"El gamer tag **{discord.utils.escape_markdown(normalized)}** no estaba registrado.")


@bot.command(name="rebuildtags")
@commands.guild_only()
async def cmd_rebuildtags(ctx: commands.Context):
    """
    Borra los gamer tags del canal en la base de datos y vuelve a construirlos
    leyendo todo el historial. También borra del canal los mensajes duplicados.
    Solo administradores o gestión del servidor.
    """
    if not is_admin_or_manage_guild(ctx):
        await ctx.send("No tienes permiso para usar este comando.", delete_after=8)
        return
    if ctx.channel.id != CHANNEL_ID:
        await ctx.send("Este comando solo puede usarse en el canal de gamer tags.", delete_after=8)
        return

    clear_channel_tags(CHANNEL_ID)
    with get_db() as conn:
        conn.execute("DELETE FROM meta WHERE key = ?", (f"scanned_{CHANNEL_ID}",))

    msg = await ctx.send("Reconstruyendo gamer tags desde el historial (se borrarán duplicados)...")
    try:
        channel = bot.get_channel(CHANNEL_ID) or await bot.fetch_channel(CHANNEL_ID)
        n = await scan_channel_history(channel, delete_duplicates=True)
        set_channel_scanned(CHANNEL_ID)
        await msg.edit(content=f"Reconstrucción completada. {n} gamer tags registrados. Duplicados borrados del canal.")
    except discord.Forbidden:
        await msg.edit(content="No tengo permiso para leer el historial del canal.")
    except Exception as e:
        await msg.edit(content=f"Error: {e}")


@bot.command(name="cleanduplicates")
@commands.guild_only()
async def cmd_cleanduplicates(ctx: commands.Context):
    """
    Borra del canal los mensajes que son duplicados (mismo gamer tag ya registrado),
    dejando solo la copia más antigua de cada uno.
    Solo administradores o gestión del servidor.
    """
    if not is_admin_or_manage_guild(ctx):
        await ctx.send("No tienes permiso para usar este comando.", delete_after=8)
        return
    if ctx.channel.id != CHANNEL_ID:
        await ctx.send("Este comando solo puede usarse en el canal de gamer tags.", delete_after=8)
        return

    msg = await ctx.send("Limpiando mensajes duplicados...")
    try:
        channel = bot.get_channel(CHANNEL_ID) or await bot.fetch_channel(CHANNEL_ID)
        deleted = await clean_duplicate_messages(channel)
        await msg.edit(content=f"Listo. Se borraron {deleted} mensajes duplicados (se mantuvo la copia más antigua de cada tag).")
    except discord.Forbidden:
        await msg.edit(content="No tengo permiso para leer o borrar mensajes en el canal.")
    except Exception as e:
        await msg.edit(content=f"Error: {e}")


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
