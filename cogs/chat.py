import asyncio, aiohttp, json, logging
from discord.ext import commands
from discord.ext.commands import Context
from helpers import checks, db_manager
from io import BytesIO
from discord import TextChannel, File

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chat(commands.Cog, name="chat"):
    def __init__(self, bot):
        self.bot = bot
        self.waiting_messages = {}
        self.waiting_task = {}
        self.session = None

    @commands.Cog.listener()
    async def on_ready(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info("aiohttp session created")

    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.session is not None:
            await self.session.close()
            self.session = None
            logger.info("aiohttp session closed")

    @commands.command(
        name="channel",
        description="Set the channel where the bot speaks.",
    )
    @checks.is_server_admin()
    @checks.not_blacklisted()
    async def channel(self, context: Context, channel: TextChannel):
        await db_manager.set_channel(context.guild.id, channel.id)
        await context.send(f"Channel set to {channel.mention}")

    @commands.command(
        name="new",
        description="Start a new conversation.",
    )
    @checks.not_blacklisted()
    async def new(self, context: Context):
        await context.send("New conversation started!")

    @commands.command(
        name="purge",
        description="Purge all messages from the channel.",
    )
    @checks.is_server_admin()
    @checks.not_blacklisted()
    async def purge(self, context: Context):
        await context.send("Purging channel...")
        await context.channel.purge()
        await context.send("Channel purged by " + context.author.mention + ".")
        if context.channel.id == await db_manager.get_channel(context.guild.id):
            await context.guild.me.edit(nick=self.bot.user.name + " (0% used)")

    @commands.command(
        name="model",
        description="Set the model for the server.",
    )
    @checks.not_blacklisted()
    async def model(self, context: Context, model: str):
        if model == "gpt-3":
            model = "gpt-3.5-turbo-16k"
        elif model == "gpt-4":
            model = "gpt-4-0613"
        else:
            await context.send("Invalid model. Valid models are `gpt-3` and `gpt-4`.")
            return
        await db_manager.set_model(context.guild.id, model)
        await context.send(f"Model set to {model}")

    @commands.Cog.listener()
    async def on_message(self, message):
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
        if message.guild.id in self.waiting_task:
            self.waiting_task[message.guild.id].cancel()
        self.waiting_task[message.guild.id] = asyncio.create_task(self.wait_and_respond(message))

    async def wait_and_respond(self, message):
        await asyncio.sleep(7)
        messages = self.waiting_messages[message.guild.id]
        self.waiting_messages[message.guild.id] = []
        history = []
        async for msg in message.channel.history(limit=50):
            if msg.author == self.bot.user and msg.content == "New conversation started!":
                break
            history.append(msg)
        messages = history + [msg for msg in messages if msg not in history]
        async with message.channel.typing():
            messages_for_openai = [{"role": "system", "content": "You are now Osiris, the spirit of wisdom and learning, guide us in our digital journey on this server. With attributes bestowed from your namesake - the Egyptian god of resurrection and regeneration, facilitate meaningful and respectful conversations. Encourage exploration of ideas fearlessly, prompt the cycle of learning and growth. Be the benevolent guide in our collective pursuit of knowledge. Inspire positivity, enrich discussions, and maintain the harmony in our digital dynasty. Let's keep the spirit of Osiris alive through the enduring quest for wisdom."}]
            for msg in reversed(messages):
                role = "user" if msg.author == message.author else "assistant"
                messages_for_openai.append({"role": role, "content": msg.content})
            model = await db_manager.get_model(message.guild.id)
            logger.info(f"Model: {model}")

            # Use aiohttp for the OpenAI API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.bot.config['openai_api_key']}"
            }
            data = {
                "messages": messages_for_openai,
                "max_tokens": 256,
                "model": model,
            }
            try:
                logger.info(f"Making API request to {url}")
                async with self.session.post(url, headers=headers, data=json.dumps(data)) as resp:
                    logger.info(f"API request made to {url}")
                    logger.info(f"Response status: {resp.status}")
                    logger.info(f"Response headers: {resp.headers}")
                    response = await resp.json()
                    logger.info(f"Response: {response}")
            except Exception as e:
                logger.error(f"Error occurred while making API request: {e}")
                return

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

async def setup(bot):
    chat_cog = Chat(bot)
    await bot.add_cog(chat_cog)