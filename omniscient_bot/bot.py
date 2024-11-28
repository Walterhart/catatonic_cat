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

# Initialize the bot
bot = commands.Bot(command_prefix='/Cast', intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Napping in the void"))
    print(f'{bot.user} has connected to Discord and is monitoring server activity.')

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Yea Yea I am awake')

@bot.event
async def on_message(message):
    print(f"Received message: {message.content}")
    await bot.process_commands(message)

bot.run(TOKEN)
