import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import requests
from omniscient_bot.cogs.youtube import YouTubeCog


@pytest.fixture
def bot():
    """Fixture for the bot mock."""
    return MagicMock()

@pytest.fixture
def youtube_cog(bot):
    """Fixture for the YouTubeCog instance."""
    return YouTubeCog(bot)

def test_extract_video_id(youtube_cog):
    """Test the extract_video_id method."""
    valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    short_url = "https://youtu.be/dQw4w9WgXcQ"
    invalid_url = "https://www.example.com/watch?v=dQw4w9WgXcQ"

    assert youtube_cog.extract_video_id(valid_url) == "dQw4w9WgXcQ"
    assert youtube_cog.extract_video_id(short_url) == "dQw4w9WgXcQ"
    assert youtube_cog.extract_video_id(invalid_url) is None

def test_extract_video_id_edge_cases(youtube_cog):
    """Test edge cases for extract_video_id."""
    url_with_params = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
    embed_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"

    assert youtube_cog.extract_video_id(url_with_params) == "dQw4w9WgXcQ"
    assert youtube_cog.extract_video_id(embed_url) is None

@patch("omniscient_bot.cogs.youtube.requests.get")
def test_fetch_video_details(mock_get, youtube_cog):
    """Test the fetch_video_details method."""
    video_id = "dQw4w9WgXcQ"
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {
                "snippet": {
                    "title": "Test Video",
                    "description": "This is a test video description.",
                }
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    video_details = youtube_cog.fetch_video_details(video_id)
    assert video_details["title"] == "Test Video"
    assert video_details["description"] == "This is a test video description."

@patch("omniscient_bot.cogs.youtube.requests.get")
def test_fetch_video_details_error_handling(mock_get, youtube_cog):
    """Test error handling in fetch_video_details."""
    mock_get.side_effect = requests.exceptions.RequestException("Network error")

    video_details = youtube_cog.fetch_video_details("invalid_id")
    assert video_details["error"] == "An error occurred while contacting the YouTube API."

@pytest.mark.asyncio
async def test_on_message_with_valid_youtube_link(youtube_cog):
    """Test on_message with a valid YouTube link."""
    message = AsyncMock()
    message.author.bot = False
    message.content = "Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_details", return_value={"title": "Test Video", "description": "Description of the test video."}):
        await youtube_cog.on_message(message)

    message.channel.send.assert_called_once_with("**Video Title:** Test Video\n**Description:** Description of the test video.")

@pytest.mark.asyncio
async def test_on_message_with_invalid_youtube_link(youtube_cog):
    """Test on_message with an invalid YouTube link."""
    message = AsyncMock()
    message.author.bot = False
    message.content = "Check this out: https://www.example.com/watch?v=invalid"
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    message.channel.send.assert_called_once_with(
        "The following links could not be processed:\n**https://www.example.com/watch?v=invalid** - Not a YouTube link."
    )

@pytest.mark.asyncio
async def test_on_message_with_multiple_links(youtube_cog):
    """Test on_message with multiple YouTube links."""
    message = AsyncMock()
    message.author.bot = False
    message.content = (
        "Check these: https://www.youtube.com/watch?v=dQw4w9WgXcQ "
        "and https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_details", return_value={"title": "Test Video", "description": "A test video."}):
        await youtube_cog.on_message(message)

    message.channel.send.assert_called_once_with(
        "**Video Title:** Test Video\n**Description:** A test video.\n\n"
        "**Video Title:** Test Video\n**Description:** A test video."
    )

@pytest.mark.asyncio
async def test_on_message_from_bot(youtube_cog):
    """Ensure on_message ignores bot messages."""
    message = AsyncMock()
    message.author.bot = True 
    message.content = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    # Assert that no response was sent
    message.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_respects_max_links(youtube_cog):
    """Test that on_message respects the MAX_LINKS limit and skips extra links."""
    message = AsyncMock()
    message.author.bot = False

    # Generate more than MAX_LINKS links
    links = [f"https://www.youtube.com/watch?v=video{i}" for i in range(10)]
    message.content = " ".join(links)  # All links in the message
    message.channel.send = AsyncMock()

    # Mock fetch_video_details to return the same result for all links
    with patch.object(
        youtube_cog,
        "fetch_video_details",
        return_value={"title": "Test Video", "description": "A test video."}
    ):
        await youtube_cog.on_message(message)

    # Assert that only MAX_LINKS links were processed
    expected_response = "\n\n".join(
        ["**Video Title:** Test Video\n**Description:** A test video."] * YouTubeCog.MAX_LINKS
    )
    message.channel.send.assert_any_call(expected_response)

    # Assert that the skipped link notification was sent
    skipped_count = len(links) - YouTubeCog.MAX_LINKS
    message.channel.send.assert_any_call(
        f"Max links summarized reached. {skipped_count} YouTube link(s) were skipped because only the first {YouTubeCog.MAX_LINKS} links are processed per message."
    )


@pytest.mark.asyncio
async def test_on_message_with_fewer_links_than_max(youtube_cog):
    """Test on_message processes all links when fewer than MAX_LINKS are provided."""
    message = AsyncMock()
    message.author.bot = False

    # Provide fewer links than MAX_LINKS
    message.content = "https://www.youtube.com/watch?v=video1 https://www.youtube.com/watch?v=video2"
    message.channel.send = AsyncMock()

    # Mock fetch_video_details to return the same result for all links
    with patch.object(
        youtube_cog, 
        "fetch_video_details", 
        return_value={"title": "Test Video", "description": "A test video."}
    ):
        await youtube_cog.on_message(message)

    # Assert that all provided links were processed
    expected_response = (
        "**Video Title:** Test Video\n**Description:** A test video.\n\n"
        "**Video Title:** Test Video\n**Description:** A test video."
    )
    message.channel.send.assert_called_once_with(expected_response)

@pytest.mark.asyncio
async def test_on_message_no_links(youtube_cog):
    """Test on_message does nothing when no links are present."""
    message = AsyncMock()
    message.author.bot = False
    message.content = "This is just a normal message with no links."
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    # Assert that no message was sent
    message.channel.send.assert_not_called()

