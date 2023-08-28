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

async def add_channel(guild_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT channels FROM guilds WHERE guild_id=?", (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            if result is None:
                channels = str(channel_id)
                await db.execute(
                    "INSERT INTO guilds(guild_id, channels) VALUES (?, ?)",
                    (str(guild_id), channels),
                )
            else:
                channels = result[0] + ',' + str(channel_id) if result[0] else str(channel_id)
                await db.execute(
                    "UPDATE guilds SET channels=? WHERE guild_id=?",
                    (channels, str(guild_id)),
                )
        await db.commit()

async def remove_channel(guild_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT channels FROM guilds WHERE guild_id=?", (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            if result is None:
                return
            channels = result[0].split(',')
            channels.remove(str(channel_id))
            channels_str = ','.join(channels)
            await db.execute(
                "UPDATE guilds SET channels=? WHERE guild_id=?",
                (channels_str, str(guild_id)),
            )
        await db.commit()

async def get_channels(guild_id: int) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT channels FROM guilds WHERE guild_id=?", (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result[0].split(',') if result and result[0] else None

async def is_guild_in_db(guild_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM guilds WHERE guild_id=?", (str(guild_id),)) as cursor:
            result = await cursor.fetchone()
            return result is not None
        
async def add_guild(guild_id: int) -> None:
    """
    Adds a guild to the database.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO guilds(guild_id) VALUES (?)",
            (guild_id,),
        )
        await db.commit()

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
        
async def set_temperature(guild_id: int, temperature: float) -> None:
    """
    Sets the temperature for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, temperature) VALUES (?, ?)",
            (guild_id, temperature),
        )
        await db.execute(
            "UPDATE guilds SET temperature=? WHERE guild_id=?",
            (temperature, guild_id),
        )
        await db.commit()

async def get_temperature(guild_id: int) -> float:
    """
    Returns the temperature for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT temperature FROM guilds WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None
        
async def get_instructions(guild_id: int) -> str:
    """
    Returns the system message for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT instructions FROM guilds WHERE guild_id=?", (guild_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None
        
async def set_instructions(guild_id: int, instructions: str) -> None:
    """
    Sets the system message for the guild.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO guilds(guild_id, instructions) VALUES (?, ?)",
            (guild_id, instructions),
        )
        await db.execute(
            "UPDATE guilds SET instructions=? WHERE guild_id=?",
            (instructions, guild_id),
        )
        await db.commit()

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

async def get_messages(guild_id: int) -> list:
    """
    Returns all messages for the guild.

    CREATE TABLE IF NOT EXISTS `messages` (
        `guild_id` varchar(20) NOT NULL,
        `channel_id` varchar(20) NOT NULL,
        `author_id` varchar(20) NOT NULL,
        `content` text NOT NULL,
        `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`guild_id`) REFERENCES `guilds` (`guild_id`)
    );
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT author_id, content FROM messages WHERE guild_id=?",
            (guild_id,),
        ) as cursor:
            result = [dict(row) for row in await cursor.fetchall()]
            return result