# cogs/double_extension_detector.py

import re
import discord
from discord.ext import commands

# Extensions commonly used to disguise executables
DANGEROUS_EXTENSIONS = {
    "exe",
    "scr",
    "bat",
    "cmd",
    "com",
    "pif",
    "js",
    "vbs",
    "msi",
    "jar",
    "ps1",
}

# Extensions attackers commonly pretend to be
FAKE_VISIBLE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "mp4",
    "mov",
    "avi",
    "mp3",
    "wav",
    "pdf",
    "doc",
    "docx",
    "txt",
    "zip",
    "rar",
}


class DoubleExtensionDetector(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_double_extension(self, filename: str) -> bool:
        filename = filename.lower().strip()

        match = re.match(r"^.+\.([a-z0-9]+)\.([a-z0-9]+)$", filename)

        if not match:
            return False

        fake_ext, real_ext = match.groups()

        return (
            fake_ext in FAKE_VISIBLE_EXTENSIONS
            and real_ext in DANGEROUS_EXTENSIONS
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        for attachment in message.attachments:
            if self.is_double_extension(attachment.filename):

                try:
                    await message.delete()
                except discord.Forbidden:
                    pass

                await message.channel.send(
                    f"{message.author.mention} "
                    f"your file `{attachment.filename}` was blocked "
                    f"because it contains a suspicious double extension."
                )

                print(
                    f"[DOUBLE EXT BLOCKED] "
                    f"{message.author} uploaded {attachment.filename}"
                )

                return


async def setup(bot: commands.Bot):
    await bot.add_cog(DoubleExtensionDetector(bot))