import os
import aiosqlite

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"

async def _execute_db_query(query: str, values: tuple = (), fetch: bool = False) -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(query, values) as cursor:
            await db.commit()
            return await cursor.fetchall() if fetch and cursor else []

async def _execute_and_get_first(query: str, values: tuple = ()) -> any:
    results = await _execute_db_query(query, values, fetch=True)
    return results[0][0] if results else None

async def _change_blacklist(user_id: int, action: str) -> int:
    await _execute_db_query(f"{action} FROM blacklist WHERE user_id=?", (user_id,))
    return await _execute_and_get_first("SELECT COUNT(*) FROM blacklist")

async def _update_guilds(guild_id: int, column: str, value: any) -> None:
    await _execute_db_query(f"INSERT OR IGNORE INTO guilds(guild_id, {column}) VALUES (?, ?)", (guild_id, value))
    await _execute_db_query(f"UPDATE guilds SET {column}=? WHERE guild_id=?", (value, guild_id))

async def _get_guild_column(guild_id: int, column: str) -> any:
    return await _execute_and_get_first(f"SELECT {column} FROM guilds WHERE guild_id=?", (guild_id,))

async def get_blacklisted_users() -> list:
    return await _execute_db_query("SELECT user_id, strftime('%s', created_at) FROM blacklist", fetch=True)

async def is_blacklisted(user_id: int) -> bool:
    return await _execute_and_get_first("SELECT * FROM blacklist WHERE user_id=?", (user_id,)) is not None

async def add_user_to_blacklist(user_id: int) -> int:
    return await _change_blacklist(user_id, "INSERT")

async def remove_user_from_blacklist(user_id: int) -> int:
    return await _change_blacklist(user_id, "DELETE")

async def add_channel(guild_id: int, channel_id: int) -> None:
    result = await _get_guild_column(guild_id, 'channels')
    channels = str(channel_id) if result is None else f"{result},{channel_id}" if result else str(channel_id)
    await _update_guilds(guild_id, 'channels', channels)

async def remove_channel(guild_id: int, channel_id: int) -> None:
    result = await _get_guild_column(guild_id, 'channels')
    if result:
        channels = ','.join(result.split(',').remove(str(channel_id)))
        await _execute_db_query("UPDATE guilds SET channels=? WHERE guild_id=?", (channels, str(guild_id)))

async def set_model(guild_id: int, model: str) -> None:
    await _update_guilds(guild_id, 'model', model)

async def get_model(guild_id: int) -> str:
    return await _get_guild_column(guild_id, 'model')

async def set_temperature(guild_id: int, temperature: float) -> None:
    await _update_guilds(guild_id, 'temperature', temperature)

async def get_temperature(guild_id: int) -> float:
    return await _get_guild_column(guild_id, 'temperature')

async def set_instructions(guild_id: int, instructions: str) -> None:
    await _update_guilds(guild_id, 'instructions', instructions)

async def get_instructions(guild_id: int) -> str:
    return await _get_guild_column(guild_id, 'instructions')

async def opt_in(guild_id: int) -> None:
    await _update_guilds(guild_id, 'opt', 1)

async def opt_out(guild_id: int) -> None:
    await _update_guilds(guild_id, 'opt', 0)
    await _execute_db_query("DELETE FROM messages WHERE guild_id=?", (guild_id,))

async def get_opt(guild_id: int) -> int:
    return await _get_guild_column(guild_id, 'opt')

async def add_message(guild_id: int, author_id: int, channel_id: int, content: str) -> None:
    await _execute_db_query("INSERT INTO messages(guild_id, author_id, channel_id, content) VALUES (?, ?, ?, ?)", (guild_id, author_id, channel_id, content))

async def get_messages(guild_id: int) -> list:
    result = await _execute_db_query("SELECT author_id, content FROM messages WHERE guild_id=?", (guild_id,), fetch=True)
    return [dict(row) for row in result]