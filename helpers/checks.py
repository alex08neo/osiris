from typing import Callable, TypeVar
from discord.ext import commands
from exceptions import UserNotOwner, UserNotServerAdmin, UserBlacklisted
from helpers import db_manager
import json
import os

T = TypeVar("T")

def is_owner() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        with open(f"{os.path.dirname(__file__)}/../config.json") as file:
            if context.author.id not in json.load(file)["owners"]:
                raise UserNotOwner
        return True
    return commands.check(predicate)

def is_server_admin() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if context.author.guild_permissions.administrator or context.author.id in context.bot.config["owners"]:
            return True
        raise UserNotServerAdmin
    return commands.check(predicate)

def not_blacklisted() -> Callable[[T], T]:
    async def predicate(context: commands.Context) -> bool:
        if await db_manager.is_blacklisted(context.author.id):
            raise UserBlacklisted
        return True
    return commands.check(predicate)
