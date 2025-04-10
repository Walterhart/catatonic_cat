import discord
from discord.ext import commands

class GeneralCog(commands.Cog):
    """A cog for general bot commands."""

    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="meow", description="Get a friendly response from the bot.")
    async def meow(self, interaction: discord.Interaction):
        """Responds to the /meow slash command."""
        await interaction.response.send_message("🐱 Yes yes, how may I help you?")

# Required setup function to add the cog
async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
