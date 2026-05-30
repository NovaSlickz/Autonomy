import re

import discord
from discord.ext import commands

from .shared import db


class LogsManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.invite_regex = re.compile(
            r"(?:https?://)?(?:www\.)?"
            r"(?:discord\.gg|discord\.com/invite|discordapp\.com/invite|discordapp\.com)/"
            r"[A-Za-z0-9-]+",
            re.IGNORECASE
        )

    async def is_enabled(
        self,
        guild_id,
        module_name
    ):

        config_cog = self.bot.get_cog("ConfigCog")

        if config_cog is None:
            return True

        return await config_cog.is_enabled(
            guild_id,
            module_name
        )

    def get_log_channel(self, guild_id):

        rows = db.get(
            "logging_channel",
            {
                "guild_id": guild_id
            }
        )

        if not rows:
            return None

        try:
            channel_id = int(rows[0][1])
        except (ValueError, TypeError):
            return None

        return self.bot.get_channel(channel_id)

    async def add_log(
        self,
        guild_id,
        event_name,
        event_description,
        event_colour
    ):

        log_channel = self.get_log_channel(guild_id)

        if log_channel is None:
            return

        embed = discord.Embed(
            title=event_name,
            description=event_description,
            colour=event_colour
        )

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if message.guild is None:
            return

        if message.author.bot:
            return

        if not await self.is_enabled(
            message.guild.id,
            "logs.deleted_messages"
        ):
            return

        content = message.content or "No message content"

        attachment_text = "None"

        if message.attachments:
            attachment_text = "\n".join(
                attachment.url
                for attachment in message.attachments
            )

        embed_urls = []

        for embed in message.embeds:

            if embed.image and embed.image.url:
                embed_urls.append(embed.image.url)

            if embed.thumbnail and embed.thumbnail.url:
                embed_urls.append(embed.thumbnail.url)

        embed_text = (
            "\n".join(embed_urls)
            if embed_urls
            else "None"
        )

        description = (
            f"Author: {message.author} ({message.author.id})\n"
            f"Channel: {message.channel.mention}\n\n"
            f"Message Content:\n"
            f"{content}\n\n"
            f"Attachments:\n"
            f"{attachment_text}\n\n"
            f"Embedded Images:\n"
            f"{embed_text}"
        )

        await self.add_log(
            guild_id=message.guild.id,
            event_name="Log - Message Deleted",
            event_description=description,
            event_colour=0xFF0000
        )

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        old_message,
        new_message
    ):

        if old_message.guild is None:
            return

        if old_message.author.bot:
            return

        if old_message.content == new_message.content:
            return

        if not await self.is_enabled(
            old_message.guild.id,
            "logs.edited_messages"
        ):
            return

        log_channel = self.get_log_channel(
            old_message.guild.id
        )

        if log_channel is None:
            return

        old_embed = discord.Embed(
            title="Old Message",
            description=(
                f"{old_message.content or 'No content'}\n\n"
                f"Author: {old_message.author}"
            ),
            colour=0xFFA500
        )

        new_embed = discord.Embed(
            title="New Message",
            description=(
                f"{new_message.content or 'No content'}\n\n"
                f"Author: {new_message.author}"
            ),
            colour=0x00FF00
        )

        await log_channel.send(embed=old_embed)
        await log_channel.send(embed=new_embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if not await self.is_enabled(
            member.guild.id,
            "logs.member_join"
        ):
            return

        joined_text = (
            f"<t:{int(member.joined_at.timestamp())}:R>"
            if member.joined_at
            else "Unknown"
        )

        await self.add_log(
            guild_id=member.guild.id,
            event_name="Log - Member Join",
            event_description=(
                f"Member: {member.mention}\n"
                f"User ID: {member.id}\n"
                f"Joined: {joined_text}"
            ),
            event_colour=0x00FF00
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if not await self.is_enabled(
            member.guild.id,
            "logs.member_remove"
        ):
            return

        await self.add_log(
            guild_id=member.guild.id,
            event_name="Log - Member Leave/Remove",
            event_description=(
                f"Member: {member}\n"
                f"User ID: {member.id}"
            ),
            event_colour=0xFF0000
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.guild is None:
            return

        if message.author.bot:
            return

        if not await self.is_enabled(
            message.guild.id,
            "logs.invites"
        ):
            return

        invite_links = self.invite_regex.findall(
            message.content
        )

        if not invite_links:
            return

        links_found = len(invite_links)

        await self.add_log(
            guild_id=message.guild.id,
            event_name="Log - Invite Posted",
            event_description=(
                f"User: {message.author.mention}\n"
                f"User ID: {message.author.id}\n"
                f"Channel: {message.channel.mention}\n"
                f"Invites Found: {links_found}"
            ),
            event_colour=0xFFA500
        )


async def setup(bot):
    await bot.add_cog(LogsManager(bot))