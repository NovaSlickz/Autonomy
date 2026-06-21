from discord.ext import commands
import random

from .shared import command_enabled


class UtilityCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @command_enabled(default=True)
    async def ping(self, ctx):
        await ctx.send("Pong!")

    @commands.hybrid_command(name="botinvite")
    @command_enabled(default=True)
    async def invite(self, ctx):
        await ctx.send("https://discord.com/oauth2/authorize?client_id=1481512387419836416")

    @commands.hybrid_command(name="documentation")
    @command_enabled(default=True)
    async def documentation(self, ctx):
        await ctx.send("https://boneheadbreaker.github.io/Autonomy/")

    @commands.hybrid_command(name="support")
    @command_enabled(default=True)
    async def support(self, ctx):
        await ctx.send("https://discord.gg/YMn5hfefbU")

    @commands.hybrid_command(name="discord")
    @command_enabled(default=True)
    async def discord(self, ctx):
        await ctx.send("https://discord.gg/YMn5hfefbU")

    @commands.hybrid_command()
    @command_enabled(default=True)
    async def coinflip(self, ctx):

        result = (
            "Heads!"
            if random.randint(0, 1)
            else "Tails!"
        )

        await ctx.send(result)

    @commands.hybrid_command()
    @command_enabled(default=True)
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, text: str):

        if ctx.interaction:

            await ctx.interaction.response.send_message(
                "Sending..",
                ephemeral=True
            )

            await ctx.channel.send(text)

        else:

            await ctx.send(text)
            await ctx.message.delete()

    @commands.hybrid_command()
    @command_enabled(default=True)
    async def info(self, ctx):
        await ctx.send("Use /documentation to get the documentation \n use /config to configure things about the bot (example if logs are enabled)")

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))