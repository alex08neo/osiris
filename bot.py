import asyncio
import json
import logging
import os
import platform
import random
import sys

import aiosqlite
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

import exceptions

if not os.path.isfile(f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
        config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix=commands.when_mentioned_or(config["prefix"]), intents=intents, help_command=None,)


class LoggingFormatter(logging.Formatter):
    black, red, green, yellow, blue, gray = "\x1b[30m", "\x1b[31m", "\x1b[32m", "\x1b[33m", "\x1b[34m", "\x1b[38m"
    reset, bold = "\x1b[0m", "\x1b[1m"
    COLORS = {logging.DEBUG: gray + bold, logging.INFO: blue + bold, logging.WARNING: yellow + bold, logging.ERROR: red, logging.CRITICAL: red + bold,}

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(black){asctime}(reset) (levelcolor){levelname:<8}(reset) (green){name}(reset) {message}"
        format = format.replace("(black)", self.black + self.bold).replace("(reset)", self.reset).replace("(levelcolor)", log_color).replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)


logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(LoggingFormatter())
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{")
file_handler.setFormatter(file_handler_formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
bot.logger = logger


async def init_db():
    async with aiosqlite.connect(f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db") as db:
        with open(f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql") as file:
            await db.executescript(file.read())
        await db.commit()

bot.config = config


@bot.event
async def on_ready():
    bot.logger.info(f"Logged in as {bot.user.name}")
    bot.logger.info(f"discord.py API version: {discord.__version__}")
    bot.logger.info(f"Python version: {platform.python_version()}")
    bot.logger.info(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    bot.logger.info("-------------------")
    status_task.start()
    if config["sync_commands_globally"]:
        bot.logger.info("Syncing commands globally...")
        await bot.tree.sync()


@tasks.loop(minutes=1.0)
async def status_task():
    statuses = ["with your mind", "games with you", "with your heart", "with your soul"]
    await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)


@bot.event
async def on_command_completion(context: Context):
    full_command_name = context.command.qualified_name
    executed_command = str(full_command_name.split(" ")[0])
    if context.guild is not None:
        bot.logger.info(f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})")
    else:
        bot.logger.info(f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs")


@bot.event
async def on_command_error(context: Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        embed = discord.Embed(description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.", color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, exceptions.UserBlacklisted):
        embed = discord.Embed(description="You are blacklisted from using the bot!", color=0xE02B2B)
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(f"{context.author} (ID: {context.author.id}) tried to execute a command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is blacklisted from using the bot.")
        else:
            bot.logger.warning(f"{context.author} (ID: {context.author.id}) tried to execute a command in the bot's DMs, but the user is blacklisted from using the bot.")
    elif isinstance(error, exceptions.UserNotOwner):
        embed = discord.Embed(description="You are not the owner of the bot!", color=0xE02B2B)
        await context.send(embed=embed)
        if context.guild:
            bot.logger.warning(f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot.")
        else:
            bot.logger.warning(f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot.")
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="You are missing the permission(s) `" + ", ".join(error.missing_permissions) + "` to execute this command!", color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        embed = discord.Embed(description="I am missing the permission(s) `" + ", ".join(error.missing_permissions) + "` to fully perform this command!", color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="Error!", description=str(error).capitalize(), color=0xE02B2B,)
        await context.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if config["debug"]:
            raise error
        else:
            bot.logger.error(f"An error has occurred: {type(error).__name__}: {str(error)}")


async def run():
    await init_db()
    await bot.start(config["token"])


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
