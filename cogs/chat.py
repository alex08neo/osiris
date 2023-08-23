from discord.ext import commands
from helpers import db_manager, oai_helper
from discord import channel, Embed
import re

class Chat(commands.Cog, name="chat"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Respond to messages."""

        if message.author == self.bot.user or message.guild is None or isinstance(message.channel, channel.DMChannel):
            return

        selected_channel_ids = await db_manager.get_channels(str(message.guild.id))
        if str(message.channel.id) not in selected_channel_ids:
            return

        model = await db_manager.get_model(message.guild.id) or "gpt-3.5-turbo-16k"
        temp = await db_manager.get_temperature(message.guild.id) or 0.5
        opt_status = await db_manager.get_opt(message.guild.id) or True

        if opt_status:
            await db_manager.add_message(message.guild.id, message.author.id, message.channel.id, message.content)

        if await db_manager.is_blacklisted(message.author.id):
            await message.delete()
            return

        if message.content.startswith(self.bot.config["prefix"]):
            return

        history = []
        async for msg in message.channel.history(limit=10):
            if msg.author == self.bot.user and msg.content == "New conversation started!":
                break
            history.append(msg)

        oai_msgs = [{"role": "system", "content": await db_manager.get_instructions(message.guild.id)}]
        supported_filetypes = ["txt", "log", "py", "js", "json", "html", "css", "md", "csv", "tsv", "xml", "yaml", "yml", "ini", "cfg", "toml", "sh", "bat", "ps1", "psm1", "psd1", "ps1xml", "psc1", "pssc", "reg", "inf", "sql"]

        for msg in reversed(history):
            role = "user" if msg.author != self.bot.user else "assistant"
            name = re.sub(r"[^a-zA-Z0-9]", "", msg.author.display_name)
            user_content = msg.content
            if msg.attachments:
                for attachment in msg.attachments:
                    if attachment.filename.split(".")[-1] in supported_filetypes:
                        attachment_content = await attachment.read()
                        attachment_content = attachment_content.decode("utf-8")
                        if len(attachment_content) > 10000:
                            attachment_content = attachment_content[:10000]
                        user_content += "\n\n" + attachment.filename + ":\n```\n" + attachment_content + "\n```"
            oai_msgs.append({"role": role, "content": user_content, "name": name})

        async with message.channel.typing():
            assistant_message = await oai_helper.infer(oai_msgs, model, temp)
            if isinstance(assistant_message, int):
                error_embed = Embed(
                    title="Error!",
                    description=f"An error occurred while trying to generate a response. Please try again later. Error code {str(assistant_message)}",
                    color=0xff0000
                )
                await message.channel.send(embed=error_embed)
                return

            if len(assistant_message) > 2000:
                parts = [assistant_message[i:i+2000] for i in range(0, len(assistant_message), 2000)]
                for part in parts:
                    await message.channel.send(part)
            else:
                await message.channel.send(assistant_message)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Welcome message when bot joins a guild."""
        message_embed = Embed(
            title="Welcome to Osiris!",
            description="To get started, use the `/osiris channel add` command in the channel you want Osiris to speak in.",
            color=0x00ff00
        )

        if guild.system_channel is not None:
            await guild.system_channel.send(embed=message_embed)
        else:  
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(embed=message_embed)
                    break

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Delete the guild from the database when the bot leaves a guild."""
        await db_manager.delete_guild(guild.id)

async def setup(bot):
    chat_cog = Chat(bot)
    await bot.add_cog(chat_cog)