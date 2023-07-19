import os
import aiosqlite

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

async def get_blacklisted_users() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, strftime('%s', created_at) FROM blacklist"
        ) as cursor:
            result = await cursor.fetchall()
            return result

async def is_blacklisted(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM blacklist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None

async def add_user_to_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO blacklist(user_id) VALUES (?)", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

async def remove_user_from_blacklist(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM blacklist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

async def set_channel(guild_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, channel_id) VALUES (?, ?)",
            (guild_id, channel_id),
        )
        await db.execute(
            "UPDATE guilds SET channel_id=? WHERE guild_id=?",
            (channel_id, guild_id),
        )
        await db.commit()

async def get_channel(guild_id: int) -> int:
    """
    Returns the channel ID where the bot will send the messages.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT channel_id FROM guilds WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None

async def set_model(guild_id: int, model: str) -> None:
    """
    Sets the model for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, model) VALUES (?, ?)",
            (guild_id, model),
        )
        await db.execute(
            "UPDATE guilds SET model=? WHERE guild_id=?",
            (model, guild_id),
        )
        await db.commit()

async def get_model(guild_id: int) -> str:
    """
    Returns the model for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT model FROM guilds WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None

async def opt_in(guild_id: int) -> None:
    """
    Opts the selected guild into conversation logging.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, opt) VALUES (?, ?)",
            (guild_id, 1),
        )
        await db.execute(
            "UPDATE guilds SET opt=? WHERE guild_id=?",
            (1, guild_id),
        )
        await db.commit()

async def opt_out(guild_id: int) -> None:
    """
    Opts the selected guild out of conversation logging. Deletes all messages from the database as a part of this.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, opt) VALUES (?, ?)",
            (guild_id, 0),
        )
        await db.execute(
            "UPDATE guilds SET opt=? WHERE guild_id=?",
            (0, guild_id),
        )
        await db.execute(
            "DELETE FROM messages WHERE guild_id=?",
            (guild_id,),
        )
        await db.commit()

async def get_opt(guild_id: int) -> int:
    """
    Returns the opt-out status for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT opt FROM guilds WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None

async def add_message(guild_id: int, author_id: int, channel_id: int, content: str) -> None:
    """
    Adds a message to the database.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages(guild_id, author_id, channel_id, content) VALUES (?, ?, ?, ?)",
            (guild_id, author_id, channel_id, content),
        )
        await db.commit()