import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
class VoidCat(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/Meow", intents=intents)
    
    async def setup_hook(self):
        # Sync application commands (slash commands)
        await self.tree.sync()

        # Dynamically load cogs
        for cog in ['cogs.youtube', 'cogs.general']:
            await self.load_extension(cog)

# Instantiate the bot
bot = VoidCat()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Napping in the void"))
    print(f'{bot.user} has connected to Discord and is monitoring server activity.')

# Run the bot
bot.run(TOKEN)
