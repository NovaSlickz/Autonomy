from discord.ext import commands
import discord
import datetime
import json

from .shared import db, command_enabled


class ModerationCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.log_manager = self.bot.get_cog("LogsManager")

    @commands.hybrid_command(name="quarantine", description="Quarantine a member.")
    @command_enabled(default=True)
    async def quarantine(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided."):
        try:

            if member == ctx.author:
                return await ctx.reply("You cannot quarantine yourself.")

            if member == ctx.guild.owner:
                return await ctx.reply("You cannot quarantine the server owner.")

            if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
                return await ctx.reply("You cannot quarantine someone with equal or higher permissions.")

            quarantine_role = discord.utils.get(ctx.guild.roles, name="QUARANTINED")

            if quarantine_role is None:
                return await ctx.reply("The QUARANTINED role does not exist.")

            if quarantine_role >= ctx.guild.me.top_role:
                return await ctx.reply("My role must be above the QUARANTINED role.")

            if quarantine_role in member.roles:
                return await ctx.reply("That member is already quarantined.")

            saved_roles = []

            for role in member.roles:
                if role != ctx.guild.default_role and role != quarantine_role:
                    saved_roles.append(role.id)

            db.delete(
                "quarantined_users",
                {
                    "guild_id": ctx.guild.id,
                    "user_id": member.id
                }
            )

            db.add("quarantined_users", ctx.guild.id, member.id, json.dumps(saved_roles))

            await member.edit(
                roles=[quarantine_role],
                reason=f"{ctx.author} | {reason}"
            )

            description = (
                f"Quarantined user: {member.mention}\n"
                f"Reason: {reason}\n\n"
                f"Quarantinued by: {ctx.author.mention}\n"
            )

            await self.log_manager.add_log(guild_id=ctx.guild.id, event_name="User quarantined", event_description=description, event_colour=0xff0000)
            await ctx.reply(f"{member.mention} has been quarantined.\nReason: {reason}")

        except Exception as error:
            print(error)

    @commands.hybrid_command(name="dequarantine", description="Remove quarantine from a member.")
    @command_enabled(default=True)
    async def dequarantine(self, ctx: commands.Context, member: discord.Member):
        try:
            if ctx.author != ctx.guild.owner:
                return await ctx.reply("Only the server owner can dequarantine users.")

            quarantine_role = discord.utils.get(ctx.guild.roles, name="QUARANTINED")

            if quarantine_role is None:
                return await ctx.reply("The QUARANTINED role does not exist.")

            data = db.get(
                "quarantined_users",
                {
                    "guild_id": ctx.guild.id,
                    "user_id": member.id
                }
            )

            if not data:
                return await ctx.reply("No quarantine data found for that user.")

            saved_role_ids = json.loads(data[0][2])

            roles_to_restore = []

            for role_id in saved_role_ids:

                role = ctx.guild.get_role(role_id)

                if role is not None:
                    roles_to_restore.append(role)

            roles_to_restore.append(ctx.guild.default_role)

            await member.edit(
                roles=roles_to_restore,
                reason=f"Dequarantined by {ctx.author}"
            )

            db.delete(
                "quarantined_users",
                {
                    "guild_id": ctx.guild.id,
                    "user_id": member.id
                }
            )
        except Exception as e:
            print(e)

        await ctx.reply(f"{member.mention} has been dequarantined.")

    @commands.hybrid_command(name="removenick", description="Removes a member's server nickname.")
    @command_enabled(default=True)
    @commands.has_permissions(manage_nicknames=True)
    async def removenick(self, ctx: commands.Context, member: discord.Member):
        try:
            await member.edit(nick=None)
            await ctx.send(f"Successfully removed the nickname for {member.mention}!")
            
        except discord.Forbidden:
            await ctx.send("I lack the permissions to change this users nickname make sure \n im added with all requested permissions \n my role is higher than theirs")
            
        except Exception:
            await ctx.send("An error occurred")

    @commands.hybrid_command(name="ban", description="ban a user from the server")
    @command_enabled(default=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):

        if member.guild_permissions.manage_messages or member.guild_permissions.administrator:
            await ctx.send("That user has administrator permissions, an emergency quarantine command is coming soon")
            return

        try:
            await member.ban(reason=reason)
            await ctx.send(f"Banned **{member.mention}**")

        except Exception:
            await ctx.send("Failed to ban")

    async def banned_users_autocomplete(self, interaction: discord.Interaction, current: str):

        choices = []

        async for entry in interaction.guild.bans(limit=None):

            user = entry.user

            if current.lower() in user.name.lower() or current in str(user.id):

                choices.append(
                    discord.app_commands.Choice(
                        name=f"{user} ({user.id})",
                        value=str(user.id)
                    )
                )

            if len(choices) >= 25:
                break

        return choices

    @commands.hybrid_command(name="unban", description="Unban a user by ID or autocomplete.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @discord.app_commands.autocomplete(user_id=banned_users_autocomplete)
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "No reason provided"):

        try:

            user = await self.bot.fetch_user(int(user_id))

            await ctx.guild.unban(user, reason=reason)

            await ctx.send(f"Successfully unbanned **{user}**\nReason: {reason}")

        except ValueError:
            await ctx.send("Invalid user ID.")

        except discord.NotFound:
            await ctx.send("That user is not banned.")

        except discord.Forbidden:
            await ctx.send("I do not have permission to unban members.")

    @commands.hybrid_command(name="mute")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):

        try:

            duration = datetime.timedelta(minutes=minutes)

            await member.timeout(duration, reason=reason)

            await ctx.send(f"{member.mention} has been muted/timed out for {minutes} minutes. reason: {reason}")

        except Exception:
            await ctx.send("Failed to mute, do I have the correct permissons?")

    @commands.hybrid_command(name="unmute")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):

        try:

            await member.timeout(None, reason=reason)

            await ctx.send(f"Unmuted {member.mention}, Reason: {reason}")

        except Exception:
            await ctx.send("Failed to unmute, do I have the correct permissions?")

    @commands.hybrid_command(name="lock", description="Lock a channel")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):

        channel = channel or ctx.channel

        await channel.set_permissions(ctx.guild.default_role, send_messages=False)

        await ctx.send(f"{channel.mention} has been locked.")

    @commands.hybrid_command(name="unlock", description="Unlocks a channel")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):

        channel = channel or ctx.channel

        await channel.set_permissions(ctx.guild.default_role, send_messages=True)

        await ctx.send(f"{channel.mention} has been unlocked.")

    @commands.hybrid_group(name="warn")
    @command_enabled(default=True)
    async def warn(self, ctx):

        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid use")

    @warn.command(name="add")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def warn_add(self, ctx, user: discord.Member, *, reason: str):

        db.add("warnings", ctx.guild.id, user.id, reason)

        await ctx.send(f"{user.mention} warned")

    @warn.command(name="remove")
    @command_enabled(default=True)
    @commands.has_permissions(moderate_members=True)
    async def warn_remove(self, ctx, user: discord.Member):

        db.delete(
            "warnings",
            {
                "guild_id": ctx.guild.id,
                "user": user.id
            }
        )

        await ctx.send(f"Warnings removed for {user.mention}")


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))