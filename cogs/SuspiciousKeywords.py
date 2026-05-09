import discord
from fnmatch import fnmatch
from discord.ext import commands

class SuspiciousKeywords(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flag_manager = self.bot.get_cog("FlagManager")
        self.keywords_file = "./threat_database/suspicious_keywords.txt"
        self.known_keywords = self.load_keywords()

    def load_keywords(self):
        keywords = []
        with open(self.keywords_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        keywords.append(line)
                    except Exception as e:
                        print(f"[Suspicious Keywords] Invalid keyword skipped: {line} ({e})")
        print(f"[Suspicious Keywords] Loaded {len(keywords)} keywords")
        return keywords

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        content = message.content.lower()

        if any(fnmatch(content, pattern.lower()) for pattern in self.known_keywords):
            if self.flag_manager:
                self.flag_manager.add_score(message.author.id, 5)

                score = self.flag_manager.get_score(message.author.id)
                print(score)
            else:
                print("ERROR: FLAG MANAGER NOT FOUND")
            
async def setup(bot):
    await bot.add_cog(SuspiciousKeywords(bot))