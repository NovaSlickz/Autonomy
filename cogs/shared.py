from discord.ext import commands

from db import Database

db = Database("bot.db")

db.create_table("test", "guild_id INTEGER", "text TEXT")
db.create_table("warnings", "guild_id INTEGER", "user INTEGER", "reason TEXT")
db.create_table("DB_ACCESS_TOKENS", "TOKENS TEXT")
db.create_table("logging_channel", "guild_id INTEGER", "channel TEXT")
db.create_table("commands_is_enabled", "guild_id INTEGER", "command TEXT", "is_enabled BOOLEAN")
db.create_table("quarantined_users", "guild_id INTEGER", "user_id INTEGER", "roles TEXT")

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
                    {
                        "guild_id": guild_id,
                        "command": name
                    }
                )

                if result:
                    return bool(result[0][2])

            return getattr(
                ctx.command.callback,
                "__command_default__",
                True
            )

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