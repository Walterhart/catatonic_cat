import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import discord
from omniscient_bot.cogs.general import GeneralCog

@pytest.mark.asyncio
async def test_meow_command():
    """Test the test_meow_command"""
    # Mock the bot and interaction
    bot = MagicMock()
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()

    cog = GeneralCog(bot)

    # Call the slash command (use `callback` to simulate)
    await cog.meow.callback(cog, interaction)

    # Assert the response was sent correctly
    interaction.response.send_message.assert_called_once_with("🐱 Yes yes, how may I help you?")
