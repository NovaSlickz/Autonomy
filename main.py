import discord
from discord.ext import commands
import os

from dotenv import load_dotenv

from logs import logs
from ConfigLoader import load_config
from bot_filter import ImageFilter

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

CONFIG = load_config()

DEV_GUILD_ID = 1254318703554723901

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
intents.messages = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=CONFIG["general"]["prefix"],
            intents=intents
        )

    async def setup_hook(self):

        # Load cogs
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.config")
        await self.load_extension("cogs.database")
        await self.load_extension("cogs.FlagManager")
        await self.load_extension("cogs.SuspiciousKeywords")

        # Sync slash commands
        guild = discord.Object(id=DEV_GUILD_ID)

        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = MyBot()

image_filter = ImageFilter(
    "./threat_database/scam_hashes.txt",
    threshold=5
)

logs(
    bot,
    CONFIG=CONFIG,
    image_filter=image_filter
)


@bot.event
async def on_ready():

    status_type = CONFIG["general"]["status_type"].lower()
    status_text = CONFIG["general"]["status_text"]

    if status_type == "playing":
        activity = discord.Game(name=status_text)

    elif status_type == "watching":
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=status_text
        )

    elif status_type == "listening":
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=status_text
        )

    else:
        raise ValueError(
            f"Invalid status_type in config.yml: {status_type}"
        )

    await bot.change_presence(
        activity=activity,
        status=discord.Status.online
    )

    print(f"Logged in as {bot.user}")


bot.run(DISCORD_TOKEN)