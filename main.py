import discord
from discord.ext import commands
import os
from cogs.shared import log
from ConfigLoader import load_config
from cogs.tickets import TicketPanelView
from cogs.tickets import TicketCloseView

print(discord.__version__)
print(hasattr(discord.ui, "channel_select"))
print([x for x in dir(discord.ui) if "select" in x.lower()])

# Load optional .env (still works for local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MOD_API_TOKEN = os.getenv("MOD_API_TOKEN")

DB_PATH = os.getenv("DB_PATH", "bot.db")
LOG_PATH = os.getenv("LOG_PATH", "./logs")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set in environment variables")
if not MOD_API_TOKEN:
    print("WARNING: MOD_API_TOKEN is not set in environment variables, mod api may be unusable")

CONFIG = load_config()

DEV_GUILD_ID = 1254318703554723901

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

        # attach shared runtime config
        self.config = CONFIG
        self.db_path = DB_PATH
        self.log_path = LOG_PATH
        self.mod_api_token = MOD_API_TOKEN 

    async def setup_hook(self):

        # Load cogs
        await self.load_extension("cogs.logs")
        await self.load_extension("cogs.utility")
        await self.load_extension("cogs.config")
        await self.load_extension("cogs.database")
        await self.load_extension("cogs.FlagManager")
        await self.load_extension("cogs.SuspiciousKeywords")
        await self.load_extension("cogs.moderation")
        await self.load_extension("cogs.image_filter")
        await self.load_extension("cogs.LinkSpam")
        await self.load_extension("cogs.MassMentionPrevention")
        await self.load_extension("cogs.DoubleExtensionPrevention")
        await self.load_extension("cogs.Setup")
        await self.load_extension("cogs.links_filter")
        await self.load_extension("cogs.words_filter")
        await self.load_extension("cogs.giveaway")
        await self.load_extension("cogs.tickets")
        await self.load_extension("cogs.events")
        await self.load_extension("cogs.announcements")
        await self.load_extension("cogs.LeaveJoin")
        await self.load_extension("cogs.tiktaktoe")

        self.add_view(TicketPanelView())
        self.add_view(TicketPanelView())

        dev_guild = discord.Object(id=DEV_GUILD_ID)

        try:
            # Sync / commands to dev guild
            await self.tree.sync(guild=dev_guild)

            # Sync / commands globally
            await self.tree.sync()

        except Exception as e:
            print(f"Sync failed: {e}")

bot = MyBot()

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
