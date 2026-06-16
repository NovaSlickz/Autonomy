from discord.ext import commands
import discord
from datetime import datetime, UTC, timedelta
import re

DURATION_RE = re.compile(r"(\d+)([wdhm])")

def parse_duration(text: str) -> timedelta:
    total = timedelta()

    for amount, unit in DURATION_RE.findall(text.lower()):
        amount = int(amount)

        if unit == "w":
            total += timedelta(weeks=amount)
        elif unit == "d":
            total += timedelta(days=amount)
        elif unit == "h":
            total += timedelta(hours=amount)
        elif unit == "m":
            total += timedelta(minutes=amount)

    if total.total_seconds() == 0:
        raise ValueError("Invalid duration")

    return total

class EventCreateModal(discord.ui.Modal, title="Schedule event"):
    title_input = discord.ui.TextInput(
        label="Title",
        placeholder="Enter a title...",
        required=True,
        max_length=100,
    )

    description_input = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Describe it...",
        required=True,
        max_length=1000,
    )

    timeframe_input = discord.ui.TextInput(
        label="Time Frame",
        placeholder="e.g. 24h, 7d or 1m",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        title = self.title_input.value
        description = self.description_input.value
        timeframe = self.timeframe_input.value

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Time Frame", value=timeframe)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        duration = parse_duration(timeframe)

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_manager = self.bot.get_cog("LogsManager")

    @commands.hybrid_group(name="event")
    @command_enabled(default=True)
    async def event(self, ctx):

        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid use, you must use a subcommand example: /event create")

    @event.command(name="create")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def create_event(self, ctx, channel: discord.TextChannel):
        if ctx.interaction is None:
            await ctx.send("Currently the text version of this command is unavaliable, please use the / version\nthis is because of a discord limitation, we are currently working on a work around")
        await ctx.interaction.response.send_modal()

        log_description = (
            f"Event scheduled\n"
            f"Scheduled by {ctx.author.mention}\n"
            f"title: {title}\n"
            f"Sent in: {channel}"
        )
        await self.log_manager.add_log(guild_id=ctx.guild.id, event_name="Event scheduled", event_description=log_description, event_colour=0x008000)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))