import asyncio, aiohttp, json, logging, os
from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks, db_manager
from io import BytesIO
from discord import channel, TextChannel, File, Embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chat(commands.Cog, name="chat"):
    def __init__(self, bot):
        self.bot = bot
        self.waiting_messages = {}
        self.waiting_task = {}
        self.session = None
        self.is_processing = {}

    async def create_session(self):
        """Create an aiohttp session if it doesn't exist."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info("aiohttp session created")

    async def close_session(self):
        """Close the aiohttp session if it exists."""
        if self.session is not None:
            await self.session.close()
            self.session = None
            logger.info("aiohttp session closed")

    @commands.Cog.listener()
    async def on_ready(self):
        """Create an aiohttp session when the bot is ready."""
        await self.create_session()

    @commands.Cog.listener()
    async def on_disconnect(self):
        """Close the aiohttp session when the bot disconnects."""
        await self.close_session()

    @commands.Cog.listener()
    async def on_connect(self):
        """Create an aiohttp session when the bot connects."""
        await self.create_session()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages."""
        if self.session is None:
            await self.create_session()

        if isinstance(message.channel, channel.DMChannel):
            for owner_id in self.bot.config["owners"]:
                owner = self.bot.get_user(owner_id)
                await owner.send(f"Message from {message.author.display_name} ({message.author.id}): {message.content}")
            return

        selected_channel_id = await db_manager.get_channel(message.guild.id) if message.guild is not None else None
        if selected_channel_id is None:
            return
        
        model = await db_manager.get_model(message.guild.id)
        if model is None:
            await db_manager.set_model(message.guild.id, "gpt-3.5-turbo-16k")
            model = "gpt-3.5-turbo-16k"

        opt_status = await db_manager.get_opt(message.guild.id)
        if opt_status is None:
            await db_manager.opt_in(message.guild.id)
            opt_status = True

        if opt_status:
            await db_manager.add_message(message.guild.id, message.author.id, message.channel.id, message.content)

        if message.author == self.bot.user:
            return

        if await db_manager.is_blacklisted(message.author.id):
            await message.channel.send("You dun goofed, you're on the no-fly list with Osiris Airlines.")

        if message.content.startswith(self.bot.config["prefix"]):
            return

        selected_channel_id = await db_manager.get_channel(message.guild.id)
        if int(message.channel.id) != int(selected_channel_id):
            return

        if message.guild.id not in self.waiting_messages:
            self.waiting_messages[message.guild.id] = []

        self.waiting_messages[message.guild.id].insert(0, message)

        if message.guild.id in self.waiting_task and not self.waiting_task[message.guild.id].done():
            return

        self.waiting_task[message.guild.id] = asyncio.create_task(self.wait_and_respond(message))

    async def wait_and_respond(self, message):
        """Wait for a few seconds and then respond to the message."""
        await asyncio.sleep(7)
        messages = self.waiting_messages[message.guild.id]
        self.waiting_messages[message.guild.id] = []
        history = []
        async for msg in message.channel.history(limit=20):
            if msg.author == self.bot.user and msg.content == "New conversation started!":
                break
            history.append(msg)
        messages = history + [msg for msg in messages if msg not in history]
        async with message.channel.typing():
            instructions = await db_manager.get_instructions(message.guild.id)
            messages_for_openai = [{"role": "system", "content": instructions}]
            for msg in reversed(messages):
                role = "user" if msg.author != self.bot.user else "assistant"
                if role == "user":
                    messages_for_openai.append({"role": role, "content": msg.author.display_name + ": " + msg.content})
                else:
                    messages_for_openai.append({"role": role, "content": msg.content})
            model = await db_manager.get_model(message.guild.id)
            logger.info(f"Model: {model}")

            # Make a moderation request to OpenAI API
            moderation_url = os.getenv("MODERATION_URL", "https://api.openai.com/v1/moderations")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot.config['openai_api_key']}"
            }
            message_stew = "\n".join([msg['content'] for msg in messages_for_openai])
            data = {
                "input": message_stew
            }
            try:
                logger.info(f"Making moderation request to {moderation_url}")
                async with self.session.post(moderation_url, headers=headers, data=json.dumps(data)) as resp:
                    if resp.status == 200:
                        logger.info(f"API request made to {moderation_url}")
                        logger.info(f"Response status: {resp.status}")
                        logger.info(f"Response headers: {resp.headers}")
                        response = await resp.json()
                        logger.info(f"Response: {response}")
                        if response['results'][0]['flagged']:
                            message_embed = Embed(
                                title="Your messages were flagged by Osiris.",
                                description="Please refrain from using offensive language in the future.",
                                color=0xff0000
                            )
                            await message.channel.send(embed=message_embed)
                            return
                    else:
                        logger.error(f"Error occurred while making API request: {resp.status}")
                        await message.channel.send("Error occurred while making moderation request.")
                        return
            except Exception as e:
                logger.error(f"Error occurred while making API request: {e}")
                await message.channel.send("Error occurred while making moderation request.")
                return

            # Make a ChatCompletion request to OpenAI API
            chatcompletion_url = os.getenv("CHATCOMPLETION_URL", "https://api.openai.com/v1/chat/completions")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot.config['openai_api_key']}"
            }
            data = {
                "messages": messages_for_openai,
                "max_tokens": 512,
                "model": model,
            }
            for i in range(3):  # Retry up to 3 times
                try:
                    logger.info(f"Making ChatCompletion request to {chatcompletion_url}")
                    async with self.session.post(chatcompletion_url, headers=headers, data=json.dumps(data), timeout=20) as resp:  # Timeout after 20 seconds
                        logger.info(f"API request made to {chatcompletion_url}")
                        logger.info(f"Response status: {resp.status}")
                        logger.info(f"Response headers: {resp.headers}")
                        response = await resp.json()
                        logger.info(f"Response: {response}")
                        break
                except Exception as e:
                    if i < 2:  # If not the last retry
                        logger.warning(f"Error occurred while making API request, retrying: {e}")
                        continue
                    else:  # If last retry
                        logger.error(f"Error occurred while making API request: {e}")
                        return

            # Send the response to the channel
            if len(response['choices'][0]['message']['content']) < 2000:
                await message.channel.send(response['choices'][0]['message']['content'])
            else:
                content = response['choices'][0]['message']['content']
                if content:
                    file_content = BytesIO(content.encode('utf-8'))
                    await message.channel.send("Message too long, sending as attachment", file=File(file_content, filename="message.txt"))
            bot_username = self.bot.user.name
            tokens_used = response['usage']['total_tokens']
            logger.info(f"Tokens used: {tokens_used} of 8192")
            await message.guild.me.edit(nick=bot_username + " (" + str(round(round(float(tokens_used/8192), 3)*100, 1)) + "% used)")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Send a welcome message when the bot joins a guild."""
        message_embed = Embed(
            title="Welcome to Osiris!",
            description="To get started, use the `/channel` command in the channel you want Osiris to speak in.",
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