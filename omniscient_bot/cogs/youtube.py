from discord.ext import commands
import re

class YouTubeCog(commands.Cog):
    """A cog for detecting YouTube links."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:  # Ignore bot messages
            return
        try:
            urls = re.findall(r'(https?://[^\s]+)', message.content)
            if urls:
                for url in urls:
                    if 'youtube.com' in url or 'youtu.be' in url:
                        await message.channel.send(f"Detected a YouTube link! Processing the link now: {url}")
        except Exception as e:
            print(f"Error processing message: {e}")

# Required setup function to add the cog
async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
