import random, time, openai, asyncio

from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks, db_manager
from discord import TextChannel, File

class Chat(commands.Cog, name="chat"):
    def __init__(self, bot):
        self.bot = bot
        self.waiting_messages = {}
        self.is_waiting = {}

    @checks.is_server_admin()
    @commands.hybrid_command(
        name="channel",
        description="Set the channel where the bot speaks.",
    )

    @checks.not_blacklisted()
    async def channel(self, context: Context, channel: TextChannel):
        """
        Set the channel where the bot speaks.

        :param context: The application command context.
        :param channel: The channel to set.
        """
        # Save the channel id to the database
        await db_manager.set_channel(context.guild.id, channel.id)
        await context.send(f"Channel set to {channel.mention}")

    @commands.hybrid_command(
        name="purge",
        description="Purge all messages from the channel.",
    )
    @checks.is_server_admin()
    @checks.not_blacklisted()
    async def purge(self, context: Context):
        # send initial response so it does not time out. save message id to edit later
        pending_message = await context.send("Purging channel...")
        # purge all messages from the channel
        await context.channel.purge()
        # send message to confirm
        await pending_message.edit(content="Channel purged by " + context.author.mention + ".")
        # if channel is also the bot channel, set usage to 0 in nickname
        if context.channel.id == await db_manager.get_channel(context.guild.id):
            await context.guild.me.edit(nick=self.bot.user.name + " (0% used)")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen to messages and respond using OpenAI.

        :param message: The message context.
        """
        # Ignore messages sent by the bot
        if message.author == self.bot.user:
            return
        
        # check if user is blacklisted
        if await db_manager.is_blacklisted(message.author.id):
            # tell user they are blacklisted in signature Osiris style
            await message.channel.send("You dun goofed, you're on the no-fly list with Osiris Airlines.")

        # check if message starts with the prefix, if so, ignore
        if message.content.startswith(self.bot.config["prefix"]):
            return
        
        # Check if the message is in the selected channel
        selected_channel_id = await db_manager.get_channel(message.guild.id)
        if int(message.channel.id) != int(selected_channel_id):
            return

        # Add the message to the waiting messages
        if message.guild.id not in self.waiting_messages:
            self.waiting_messages[message.guild.id] = []
        self.waiting_messages[message.guild.id].append(message)

        # If the bot is already waiting, don't start another wait period
        if self.is_waiting.get(message.guild.id, False):
            return

        # Set the waiting flag
        self.is_waiting[message.guild.id] = True

        # Wait for 3-5 seconds
        await asyncio.sleep(random.randint(3, 5))

        # Get the waiting messages and clear them
        messages = self.waiting_messages[message.guild.id]
        self.waiting_messages[message.guild.id] = []

        # Clear the waiting flag
        self.is_waiting[message.guild.id] = False

        # Get the last 20 messages in the channel
        history = []
        async for msg in message.channel.history(limit=50):
            history.append(msg)

        # Merge the history and the new messages, removing duplicates
        messages = history + [msg for msg in messages if msg not in history]

        async with message.channel.typing():
            # Prepare the messages for the OpenAI API
            messages_for_openai = [{"role": "system", "content": "You are now Osiris, the spirit of wisdom and learning, guide us in our digital journey on this server. With attributes bestowed from your namesake - the Egyptian god of resurrection and regeneration, facilitate meaningful and respectful conversations. Encourage exploration of ideas fearlessly, prompt the cycle of learning and growth. Be the benevolent guide in our collective pursuit of knowledge. Inspire positivity, enrich discussions, and maintain the harmony in our digital dynasty. Let's keep the spirit of Osiris alive through the enduring quest for wisdom."}]
            for msg in reversed(messages):
                role = "user" if msg.author == message.author else "assistant"
                messages_for_openai.append({"role": role, "content": msg.content})

            # Call OpenAI and send the response
            response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages_for_openai,
            max_tokens=2048
            )
            # if message is under 2000 characters, send it
            if len(response['choices'][0]['message']['content']) < 2000:
                await message.channel.send(response['choices'][0]['message']['content'])
            else:
                await message.channel.send("Message too long, sending as attachment")
                await message.channel.send(file=File(fp=response['choices'][0]['message']['content'], filename="message.txt"))
            # change nickname to include tokens used in parentheses
            # first get bot username
            bot_username = self.bot.user.name
            # then get the number of tokens used
            tokens_used = response['usage']['total_tokens']
            # then change nickname, displaying usage in percent used
            print("Tokens used: " + str(tokens_used) + " of 16384")
            await message.guild.me.edit(nick=bot_username + " (" + str(round(round(float(tokens_used/16384), 3)*100, 1)) + "% used)")

async def setup(bot):
    openai.api_key = bot.config["openai_api_key"]
    await bot.add_cog(Chat(bot))