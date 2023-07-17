import os
import openai
from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks, db_manager
from discord import TextChannel, File

load_dotenv()

class Chat(commands.Cog, name="chat"):
    def __init__(self, bot):
        self.bot = bot
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

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen to messages and respond using OpenAI.

        :param message: The message context.
        """
        # Ignore messages sent by the bot
        if message.author == self.bot.user:
            return

        # Check if the message is in the selected channel
        selected_channel_id = await db_manager.get_channel(message.guild.id)
        if int(message.channel.id) != int(selected_channel_id):
            print("Message received but not in selected channel " + str(message.channel.id) + " != " + str(selected_channel_id))
            return

        print("Message received in selected channel" + str(message.channel.id) + " == " + str(selected_channel_id))
        # Get the last 20 messages in the channel
        messages = []
        async for msg in message.channel.history(limit=20):
            messages.append(msg)

        # Prepare the messages for the OpenAI API
        messages_for_openai = [{"role": "system", "content": "You are chatting with an AI assistant."}]
        for msg in reversed(messages):
            role = "user" if msg.author == message.author else "assistant"
            messages_for_openai.append({"role": role, "content": msg.content})
        print(str(messages_for_openai))
        # Call OpenAI and send the response
        response = openai.ChatCompletion.create(
          model="gpt-4-0613",
          messages=messages_for_openai
        )
        # if message is under 2000 characters, send it
        if len(response['choices'][0]['message']['content']) < 2000:
            await message.channel.send(response['choices'][0]['message']['content'])
        else:
            await message.channel.send("Message too long, sending as attachment")
            await message.channel.send(file=File(response['choices'][0]['message']['content'], filename="message.txt"))
async def setup(bot):
    openai.api_key = bot.config["OPENAI_API_KEY"]
    await bot.add_cog(Chat(bot))