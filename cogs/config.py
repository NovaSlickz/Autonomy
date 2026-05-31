from discord.ext import commands
import discord

from .shared import (
    db,
    get_toggleable_commands
)


class ConfigCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(
                f"You need the following permissions to use this command: `{perms}`"
            )

        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                "This command is disabled in this server."
            )

    async def is_enabled(
        self,
        guild_id: int,
        module_name: str,
        default: bool = True
    ):

        rows = db.get(
            "modules_is_enabled",
            {
                "guild_id": guild_id,
                "module": module_name
            }
        )

        if not rows:
            return default

        return bool(rows[0][2])

    async def _config_enable(
        self,
        ctx,
        module_name: str
    ):

        valid = get_toggleable_commands(
            ctx.bot
        )

        if module_name not in valid:
            return "invalid_module_name"

        db.delete(
            "modules_is_enabled",
            {
                "guild_id": ctx.guild.id,
                "module": module_name
            }
        )

        db.add(
            "modules_is_enabled",
            ctx.guild.id,
            module_name,
            True
        )

    async def _config_disable(
        self,
        ctx,
        module_name: str
    ):

        valid = get_toggleable_commands(
            ctx.bot
        )

        if module_name not in valid:
            return "invalid_module_name"

        db.delete(
            "modules_is_enabled",
            {
                "guild_id": ctx.guild.id,
                "module": module_name
            }
        )

        db.add("modules_is_enabled", ctx.guild.id, module_name, False)

    @commands.hybrid_group(name="config")
    async def config(self, ctx):

        if ctx.invoked_subcommand is None:

            await ctx.send(
                "You must use a subcommand"
            )

    @config.command(name="enable")
    @commands.has_permissions(
        administrator=True
    )
    async def config_enable(
        self,
        ctx,
        module_name: str
    ):

        error = await self._config_enable(
            ctx,
            module_name
        )

        if error == "invalid_module_name":

            valid_commands = (
                get_toggleable_commands(
                    ctx.bot
                )
            )

            return await ctx.send(
                f"Invalid module.\n"
                f"Available modules: "
                f"{', '.join(valid_commands)}"
            )

        await ctx.send(
            f"Enabled `{module_name}`"
        )

    @config.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def config_disable(self, ctx, module_name: str):

        error = await self._config_disable(
            ctx,
            module_name
        )

        if error == "invalid_module_name":

            valid_commands = (
                get_toggleable_commands(
                    ctx.bot
                )
            )

            return await ctx.send(
                f"Invalid module.\n"
                f"Available modules: "
                f"{', '.join(valid_commands)}"
            )

        await ctx.send(
            f"Disabled `{module_name}`"
        )

    @config.command(name="set")
    @commands.has_permissions(administrator=True)
    async def config_set(self, ctx, module_name: str, channel: discord.TextChannel):

        # currently only logs
        # supports extra config

        if module_name != "logs":

            return await ctx.send(
                "Only the `logs` module "
                "currently supports "
                "extra configuration."
            )

        db.delete(
            "logging_channel",
            {
                "guild_id": ctx.guild.id
            }
        )

        db.add(
            "logging_channel",
            ctx.guild.id,
            str(channel.id)
        )

        await ctx.send(
            f"Logging channel set to "
            f"{channel.mention}"
        )

    @config.command(name="list")
    @commands.has_permissions(
        administrator=True
    )
    async def config_list(self, ctx):

        modules = (
            get_toggleable_commands(
                ctx.bot
            )
        )

        rows = db.get(
            "modules_is_enabled",
            {
                "guild_id": ctx.guild.id
            }
        ) or []

        overrides = {
            row[1]: bool(row[2])
            for row in rows
        }

        lines = []

        for module in modules:

            if module in overrides:

                state = (
                    "Enabled"
                    if overrides[module]
                    else "Disabled"
                )

            else:

                state = (
                    "Enabled (default)"
                )

            extra = ""

            # show logging channel
            # only on parent logs module

            if module == "logs":

                channel_rows = db.get(
                    "logging_channel",
                    {
                        "guild_id": ctx.guild.id
                    }
                )

                if channel_rows:

                    channel_id = (
                        channel_rows[0][1]
                    )

                    channel = (
                        ctx.guild.get_channel(
                            int(channel_id)
                        )
                    )

                    if channel:

                        extra = (
                            f" | Channel: "
                            f"{channel.mention}"
                        )

            lines.append(
                f"{module}: "
                f"{state}"
                f"{extra}"
            )

        message = (
            "\n".join(lines)
            if lines
            else "No modules found"
        )

        await ctx.send(
            f"```\n{message}\n```"
        )

    @config.command(name="reset")
    @commands.has_permissions(
        administrator=True
    )
    async def config_reset(self, ctx):

        db.delete(
            "modules_is_enabled",
            {
                "guild_id": ctx.guild.id
            }
        )

        db.delete(
            "logging_channel",
            {
                "guild_id": ctx.guild.id
            }
        )

        await ctx.send(
            "Config reset back to default"
        )

    @config_enable.autocomplete(
        "module_name"
    )
    @config_disable.autocomplete(
        "module_name"
    )
    @config_set.autocomplete(
        "module_name"
    )
    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):

        cmds = (
            get_toggleable_commands(
                interaction.client
            )
        )

        return [
            discord.app_commands.Choice(
                name=cmd,
                value=cmd
            )
            for cmd in cmds
            if current.lower()
            in cmd.lower()
        ][:25]


async def setup(bot):

    await bot.add_cog(
        ConfigCog(bot)
    )