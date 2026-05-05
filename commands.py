from discord.ext import commands
import discord
from db import Database
import random

db = Database('bot.db')

db.create_table("test", "guild_id INTEGER", "text TEXT")
db.create_table("warnings", "guild_id INTEGER", "user INTEGER", "reason TEXT")
db.create_table("DB_ACCESS_TOKENS", "TOKENS TEXT")
db.create_table("logging_channel", "guild_id INTEGER", "channel TEXT")
db.create_table("commands_is_enabled", "guild_id INTEGER", "command TEXT", "is_enabled BOOLEAN")

def command_enabled(default=True):
    def decorator(func):
        func.__command_enabled__ = True
        func.__command_default__ = default

        async def predicate(ctx: commands.Context):
            if ctx.guild is None:
                return True

            command = ctx.command
            guild_id = ctx.guild.id

            names_to_check = []

            while command:
                names_to_check.append(command.qualified_name)
                command = command.parent

            for name in names_to_check:
                result = db.get(
                    "commands_is_enabled",
                    {"guild_id": guild_id, "command": name}
                )

                if result:
                    return bool(result[0][2])

            return getattr(ctx.command.callback, "__command_default__", True)

        return commands.check(predicate)(func)
    return decorator

def get_toggleable_commands(bot):
    cmds = set()

    for cmd in bot.walk_commands():
        if hasattr(cmd.callback, "__command_enabled__"):
            cmds.add(cmd.qualified_name)

            parent = cmd.parent
            while parent:
                cmds.add(parent.qualified_name)
                parent = parent.parent

    return sorted(cmds)

def handle_commands(bot):

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            if ctx.guild:
                await ctx.send("This command is disabled in this server. Moderators can use /config to enable it.")

    @bot.hybrid_command()
    @command_enabled(default=True)
    async def ping(ctx):
        await ctx.send("Pong!")

    @bot.hybrid_command(name="documentation")
    @command_enabled(default=True)
    async def get_documentation(ctx):
        await ctx.send("https://boneheadbreaker.github.io/Autonomy/")

    @bot.hybrid_command(name="say")
    @command_enabled(default=True)
    @commands.has_permissions(manage_messages=True)
    async def say(ctx, *, text: str):
        if ctx.interaction:
            await ctx.interaction.response.send_message("Sending..", ephemeral=True)
            await ctx.channel.send(text)
        else:
            await ctx.send(text)
            await ctx.message.delete()

    # Database commands
    @bot.hybrid_group(name="database")
    @command_enabled(default=True)
    async def database_command(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid use")

    @database_command.command(name="add")
    @command_enabled(default=True)
    async def database_add(ctx, token, table, data):
        if not db.exists("DB_ACCESS_TOKENS", "TOKENS", token):
            await ctx.send("Invalid token")
            return

        if data.startswith('"') and data.endswith('"'):
            data = data[1:-1]

        values = [v.strip() for v in data.split(",")]

        if table in ["test", "warnings"]:
            db.add(table, ctx.guild.id, *values)
        else:
            db.add(table, *values)

        await ctx.send(f"Added {data}")

    @database_command.command(name="create")
    @command_enabled(default=True)
    async def database_create(ctx, token, table, columns):
        if not db.exists("DB_ACCESS_TOKENS", "TOKENS", token):
            await ctx.send("Invalid token")
            return

        db.create_table(table, columns)
        await ctx.send(f"Created `{table}`")

    # Warn commands
    @bot.hybrid_group(name="warn")
    @command_enabled(default=True)
    async def warn_command(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid use")

    @warn_command.command(name="add")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def warn_add(ctx, user: discord.Member, *, reason: str):
        db.add("warnings", ctx.guild.id, user.id, reason)
        await ctx.send(f"{user.mention} warned")

    @warn_command.command(name="remove")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def warn_remove(ctx, user: discord.Member):
        db.delete("warnings", {
            "guild_id": ctx.guild.id,
            "user": user.id
        })
        await ctx.send(f"Warnings removed for {user.mention}")

    # Config commands
    @bot.hybrid_group(name="config")
    @command_enabled(default=True)
    async def config_command(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid use")

    @config_command.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def config_enable(ctx, command_name: str):
        valid = get_toggleable_commands(ctx.bot)

        if command_name not in valid:
            await ctx.send(f"Invalid command.\nAvailable: {', '.join(valid)}")
            return

        command_obj = ctx.bot.get_command(command_name)
        default = True
        if command_obj and hasattr(command_obj.callback, "__command_default__"):
            default = command_obj.callback.__command_default__

        db.delete("commands_is_enabled", {
            "guild_id": ctx.guild.id,
            "command": command_name
        })

        if not default:
            db.add("commands_is_enabled", ctx.guild.id, command_name, True)

        await ctx.send(f"Enabled `{command_name}`")

    @config_command.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def config_disable(ctx, command_name: str):
        valid = get_toggleable_commands(ctx.bot)

        if command_name not in valid:
            await ctx.send(f"Invalid command.\nAvailable: {', '.join(valid)}")
            return

        command_obj = ctx.bot.get_command(command_name)
        default = True
        if command_obj and hasattr(command_obj.callback, "__command_default__"):
            default = command_obj.callback.__command_default__

        db.delete("commands_is_enabled", {
            "guild_id": ctx.guild.id,
            "command": command_name
        })

        if default:
            db.add("commands_is_enabled", ctx.guild.id, command_name, False)

        await ctx.send(f"Disabled `{command_name}`")

    @config_command.command(name="list")
    @commands.has_permissions(administrator=True)
    async def config_list(ctx):
        cmds = get_toggleable_commands(ctx.bot)
        rows = db.get("commands_is_enabled", {"guild_id": ctx.guild.id}) or []
        overrides = {row[1]: bool(row[2]) for row in rows}

        lines = []
        for cmd in cmds:
            command_obj = ctx.bot.get_command(cmd)
            default = True
            if command_obj and hasattr(command_obj.callback, "__command_default__"):
                default = command_obj.callback.__command_default__

            if cmd in overrides:
                state = "Enabled" if overrides[cmd] else "Disabled"
            else:
                state = "Enabled (default)" if default else "Disabled (default)"

            lines.append(f"{cmd}: {state}")

        message = "\n".join(lines) if lines else "No commands found"
        await ctx.send(f"```\n{message}\n```")

    @config_command.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def config_reset(ctx):
        db.delete("commands_is_enabled", {"guild_id": ctx.guild.id})
        await ctx.send("All command overrides have been reset to default.")

    @config_enable.autocomplete("command_name")
    @config_disable.autocomplete("command_name")
    async def command_autocomplete(interaction: discord.Interaction, current: str):
        cmds = get_toggleable_commands(interaction.client)

        return [
            discord.app_commands.Choice(name=cmd, value=cmd)
            for cmd in cmds if current.lower() in cmd.lower()
        ][:25]

    @bot.hybrid_command(name="ban")
    @command_enabled(default=True)
    @commands.has_permissions(ban_members=True)
    async def ban(ctx, member: discord.Member, *, reason="No reason"):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"Banned {member.mention}")
        except:
            await ctx.send("Failed to ban")

    @bot.hybrid_command(name="coinflip")
    @command_enabled(default=True)
    async def coinflip(ctx):
        await ctx.send("Heads!" if random.randint(0, 1) else "Tails!")