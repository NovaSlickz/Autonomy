import discord
from discord.ext import commands

import imagehash
from PIL import Image, ImageFile

import requests

from io import BytesIO

ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageFilterCog(commands.Cog):
    def __init__(self, bot, hash_file="./threat_database/scam_hashes.txt", threshold=5):
        self.bot = bot
        self.hash_file = hash_file
        self.threshold = threshold

        self.known_hashes = self.load_hashes()

    def load_hashes(self):
        hashes = []

        try:
            with open(self.hash_file, "r") as f:
                for line in f:
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        hashes.append(
                            imagehash.hex_to_hash(line)
                        )

                    except Exception as e:
                        print(
                            f"[ImageFilter] Invalid hash skipped: "
                            f"{line} ({e})"
                        )

            print(f"[ImageFilter] Loaded {len(hashes)} hashes")

        except FileNotFoundError:
            print(
                f"[ImageFilter] Hash file not found: "
                f"{self.hash_file}"
            )

        return hashes


    def extract_urls(self, message):
        urls = []

        # Attachments
        for attachment in message.attachments:
            if (
                attachment.content_type
                and "image" in attachment.content_type
            ):
                urls.append(attachment.url)

        # Embeds
        for embed in message.embeds:
            if embed.image and embed.image.url:
                urls.append(embed.image.url)

            if embed.thumbnail and embed.thumbnail.url:
                urls.append(embed.thumbnail.url)

        return urls

    def check_url(self, url):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))

            phash = imagehash.phash(img)

            for known in self.known_hashes:
                distance = phash - known

                if distance <= self.threshold:
                    return True, distance

        except Exception as e:
            print(f"[ImageFilter] Error: {e}")

        return False, None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        urls = self.extract_urls(message)

        if not urls:
            return

        for url in urls:
            match, distance = self.check_url(url)

            if match:
                try:
                    await message.delete()

                    print(f"[ImageFilter] Deleted (distance={distance})")

                    logs_cog = self.bot.get_cog("LogsManager")

                    if logs_cog:
                        await logs_cog.add_log(
                            guild_id = message.guild.id,
                            event_name = "Log - Known scam image",
                            event_description=(
                                f"Author: {message.author} ({message.author.id})\n",
                                f"Channel: {message.channel.mention}\n",
                                f"Distance: {distance}\n",
                                f"Message Content: {message.content or 'message contained no text'}"
                            ),
                            event_colour=0xff0000
                        )

                except discord.Forbidden:
                    print("[ImageFilter] Missing permissions to delete message")

                except Exception as e:
                    print(f"[ImageFilter] Delete failed: {e}")

                return

async def setup(bot):
    await bot.add_cog(
        ImageFilterCog(
            bot,
            hash_file="./threat_database/scam_hashes.txt",
            threshold=5
        )
    )