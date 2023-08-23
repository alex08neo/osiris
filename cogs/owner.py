import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks, db_manager


class OzAdmin(commands.Cog, name="ozadmin"):
    def __init__(self, bot):
        self.bot = bot

    # Some sync magic for you and your bot. Now serving with a smile!
    @commands.command(description="Sync or unsync the slash commands.")
    @app_commands.describe(scope="The scope of the sync. Can be `global` or `guild`.")
    @checks.is_owner()
    async def sync(self, context: Context, action: str, scope: str) -> None:
        """
        Sync or unsync the slash commands.

        :param context: The command context.
        :param action: 'sync' or 'unsync' the commands.
        :param scope: The scope of the sync. Can be 'global' or 'guild'.
        """
        if action not in ['sync', 'unsync']:
            embed = discord.Embed(description="Action must be 'sync' or 'unsync'.", color=0xE02B2B)
            await context.send(embed=embed)
            return

        if scope not in ['global', 'guild']:
            embed = discord.Embed(description="Scope must be 'global' or 'guild'.", color=0xE02B2B)
            await context.send(embed=embed)
            return

        if action == 'sync':
            target_func = context.bot.tree.sync
        else:
            target_func = context.bot.tree.clear_commands

        if scope == 'global':
            await target_func(guild=None)
        else:
            await target_func(guild=context.guild)

        description = f"Slash commands have been {action}ed globally." if scope == 'global' else f"Slash commands have been {action}ed in this guild."
        embed = discord.Embed(description=description, color=0x9C84EF)
        await context.send(embed=embed)

    # The cog love, load, unload, and reload. Feels like a laundry day, doesn't it?
    @commands.hybrid_group(
        name="cog",
        description="Cog management commands.",
    )
    @checks.is_owner()
    async def cog(self, context: Context, action: str, cog_name: str) -> None:
        """
        Manage cogs: load, unload, reload.

        :param context: The hybrid command context.
        :param action: The action to perform (load, unload, reload).
        :param cog_name: The name of the cog.
        """
        action_map = {"load": "loaded", "unload": "unloaded", "reload": "reloaded"}
        try:
            method = getattr(self.bot, f"{action}_extension")
            method(f"cogs.{cog_name}")
            embed = discord.Embed(description=f"Successfully {action_map[action]} the `{cog_name}` cog.", color=0x9C84EF)
        except Exception:
            embed = discord.Embed(description=f"Could not {action} the `{cog_name}` cog.", color=0xE02B2B)
        await context.send(embed=embed)

    # Bot wants to talk? Let's make it talk! Or shout within an embed, just for fun!
    @commands.hybrid_group(
        name="say",
        description="The bot will say anything you want, plain or in an embed!",
    )
    @app_commands.describe(message="The message that should be repeated by the bot.")
    @checks.is_owner()
    async def say(self, context: Context, *, message: str, in_embed: bool = False) -> None:
        """
        The bot will say anything you want.

        :param context: The hybrid command context.
        :param message: The message that should be repeated by the bot.
        :param in_embed: Whether to send the message within an embed.
        """
        if in_embed:
            embed = discord.Embed(description=message, color=0x9C84EF)
            await context.send(embed=embed)
        else:
            await context.send(message)

    # The dreaded shutdown command. Farewell, dear bot. Until next time!
    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @checks.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(description="Shutting down. Bye! :wave:", color=0x9C84EF)
        await context.send(embed=embed)
        await self.bot.close()

    # All the blacklist magic in one place. Add, remove, show - your bot, your rules!
    @commands.hybrid_group(
        name="blacklist",
        description="Get the list of all blacklisted users.",
    )
    @checks.is_owner()
    async def blacklist(self, context: Context, action: str, user: discord.User = None) -> None:
        """
        Lets you add, remove, or show blacklisted users.

        :param context: The hybrid command context.
        :param action: 'add', 'remove', or 'show' blacklisted users.
        :param user: The user to be added or removed from the blacklist.
        """
        if action not in ['add', 'remove', 'show']:
            embed = discord.Embed(description="Action must be 'add', 'remove', or 'show'.", color=0xE02B2B)
            await context.send(embed=embed)
            return

        if action == 'show':
            blacklisted_users = await db_manager.get_blacklist()
            description = '\n'.join([f"{usr.id} - {usr.name}#{usr.discriminator}" for usr in blacklisted_users])
            embed = discord.Embed(title="Blacklisted Users", description=description, color=0x9C84EF)
            await context.send(embed=embed)
        elif action == 'add' and user:
            await db_manager.add_to_blacklist(user)
            embed = discord.Embed(description=f"{user.mention} has been added to the blacklist.", color=0x9C84EF)
            await context.send(embed=embed)
        elif action == 'remove' and user:
            await db_manager.remove_from_blacklist(user)
            embed = discord.Embed(description=f"{user.mention} has been removed from the blacklist.", color=0x9C84EF)
            await context.send(embed=embed)


def setup(bot):
    bot.add_cog(OzAdmin(bot))
