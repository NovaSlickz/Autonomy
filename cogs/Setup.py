import discord
from discord.ext import commands

from .shared import db


class LoggingChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Select a logging channel...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]

        existing = db.get(
            "logging_channel",
            {
                "guild_id": interaction.guild.id
            }
        )

        if existing:
            db.delete(
                "logging_channel",
                {
                    "guild_id": interaction.guild.id
                }
            )

        db.add(
            "logging_channel",
            interaction.guild.id,
            str(channel.id)
        )

        embed = discord.Embed(
            title="✅ Logging Configured",
            description=f"Logging channel set to {channel.mention}",
            colour=discord.Colour.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )


class LoggingSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.add_item(
            LoggingChannelSelect()
        )


class SetupDialogView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Configure Logging",
        style=discord.ButtonStyle.primary,
        custom_id="configure_logging"
    )
    async def configure_logging(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Logging Setup",
            description=(
                "Select the channel you want me to use "
                "for logging events."
            ),
            colour=discord.Colour.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=LoggingSetupView(),
            ephemeral=True
        )


class SetupDialog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        print(
            f"Added to {guild.name} "
            f"({guild.id})"
        )

        embed = discord.Embed(
            title="Setup",
            description=(
                "Hi! Thanks for adding me.\n\n"
                "Click the button below to configure the bot."
            ),
            colour=discord.Colour.green()
        )

        system_channel = guild.system_channel

        if (
            system_channel
            and system_channel.permissions_for(guild.me).send_messages
        ):
            await system_channel.send(
                embed=embed,
                view=SetupDialogView()
            )
            return

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(
                    embed=embed,
                    view=SetupDialogView()
                )
                break


async def setup(bot):
    await bot.add_cog(
        SetupDialog(bot)
    )