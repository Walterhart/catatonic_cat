import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from omniscient_bot.cogs.youtube import YouTubeCog
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable


# Fixtures
@pytest.fixture
def bot():
    """Fixture for the bot mock."""
    return MagicMock()

@pytest.fixture
def youtube_cog(bot):
    """Fixture for the YouTubeCog instance."""
    return YouTubeCog(bot)

# Tests for Utility Methods

def test_extract_video_id(youtube_cog):
    """Test extraction of video IDs from various YouTube URL formats."""
    valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    short_url = "https://youtu.be/dQw4w9WgXcQ"
    invalid_url = "https://www.example.com/watch?v=dQw4w9WgXcQ"

    assert youtube_cog.extract_video_id(valid_url) == "dQw4w9WgXcQ"
    assert youtube_cog.extract_video_id(short_url) == "dQw4w9WgXcQ"
    assert youtube_cog.extract_video_id(invalid_url) is None

def test_correct_spelling(youtube_cog):
    """Test the correct_spelling method to handle common misspellings."""
    text = "speling mistaks are commmon"
    expected = "spelling mistakes are common"
    assert youtube_cog.correct_spelling(text) == expected

def test_preprocess_captions_with_simple_text(youtube_cog):
    """Ensure punctuation restoration works for simple text."""
    captions = "this is a test without punctuation"
    processed_captions = youtube_cog.preprocess_captions(captions)
    assert processed_captions == "this is a test without punctuation."  # Update to match actual behavior

def test_preprocess_captions_combined(youtube_cog):
    """Ensure captions are both corrected for spelling and punctuation."""
    captions = "thsi is a tst without punctuatin"
    processed_captions = youtube_cog.preprocess_captions(captions)
    assert processed_captions == "this is a test without punctuation."  # Update to match actual behavior


def test_summarize_text_with_long_input(youtube_cog):
    """Ensure summarization works with long input text."""
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    summary = youtube_cog.summarize_text(text, num_sentences=2)
    assert len(summary.split(".")) >= 2

# Tests for Fetch Video Captions

@patch("omniscient_bot.cogs.youtube.YouTubeTranscriptApi.get_transcript")
def test_fetch_video_captions(mock_get_transcript, youtube_cog):
    """Test fetching and summarization of captions from a YouTube video."""
    mock_get_transcript.return_value = [
        {"text": "This is a test."},
        {"text": "It is only a test."}
    ]

    summary = youtube_cog.fetch_video_captions("test_video_id")
    assert "test" in summary  

@patch("omniscient_bot.cogs.youtube.YouTubeTranscriptApi.get_transcript")
def test_fetch_video_captions_error_handling(mock_get_transcript, youtube_cog):
    """Ensure proper error handling when fetching captions fails."""
    mock_get_transcript.side_effect = Exception("Test error")

    summary = youtube_cog.fetch_video_captions("invalid_video_id")
    assert summary is None

@patch("omniscient_bot.cogs.youtube.YouTubeTranscriptApi.get_transcript")
def test_fetch_video_captions_transcripts_disabled(mock_get_transcript, youtube_cog):
    """Ensure the bot handles videos with disabled captions."""
    mock_get_transcript.side_effect = TranscriptsDisabled("Captions disabled")

    summary = youtube_cog.fetch_video_captions("test_video_id")
    assert summary is None

@patch("omniscient_bot.cogs.youtube.YouTubeTranscriptApi.get_transcript")
def test_fetch_video_captions_transcripts_disabled(mock_get_transcript, youtube_cog):
    """Ensure the bot handles videos with disabled captions."""
    from youtube_transcript_api._errors import TranscriptsDisabled

    mock_get_transcript.side_effect = TranscriptsDisabled("Captions are disabled.")
    summary = youtube_cog.fetch_video_captions("test_video_id")
    assert summary is None
    
@patch("omniscient_bot.cogs.youtube.YouTubeTranscriptApi.get_transcript")
def test_fetch_video_captions_video_unavailable(mock_get_transcript, youtube_cog):
    """Ensure the bot handles unavailable videos gracefully."""
    from youtube_transcript_api._errors import VideoUnavailable

    mock_get_transcript.side_effect = VideoUnavailable("Video is unavailable.")
    summary = youtube_cog.fetch_video_captions("test_video_id")
    assert summary is None


# Tests for on_message Behavior

@pytest.mark.asyncio
async def test_on_message_with_valid_youtube_link(youtube_cog):
    """Test if a single valid YouTube link is processed and summarized correctly in on_message."""
    message = AsyncMock()
    message.author.bot = False
    message.content = "Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_captions", return_value="Test Summary"):
        await youtube_cog.on_message(message)

    message.channel.send.assert_called_once_with("**Summary:** Test Summary")

@pytest.mark.asyncio
async def test_on_message_with_multiple_links(youtube_cog):
    """Test if multiple valid YouTube links in a message are handled correctly."""
    message = AsyncMock()
    message.author.bot = False
    message.content = (
        "Check these: https://www.youtube.com/watch?v=dQw4w9WgXcQ "
        "and https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_captions", return_value="Test Summary"):
        await youtube_cog.on_message(message)

    message.channel.send.assert_called_once_with(
        "**Summary:** Test Summary\n\n**Summary:** Test Summary"
    )

@pytest.mark.asyncio
async def test_on_message_respects_max_links(youtube_cog):
    """Test that the MAX_LINKS limit is respected in on_message and extra links are skipped."""
    message = AsyncMock()
    message.author.bot = False

    links = [f"https://www.youtube.com/watch?v=video{i}" for i in range(10)]
    message.content = " ".join(links)
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_captions", return_value="Test Summary"):
        await youtube_cog.on_message(message)

    expected_response = "\n\n".join(["**Summary:** Test Summary"] * YouTubeCog.MAX_LINKS)
    message.channel.send.assert_any_call(expected_response)

    skipped_count = len(links) - YouTubeCog.MAX_LINKS
    message.channel.send.assert_any_call(
        f"Max links summarized reached. {skipped_count} YouTube link(s) were skipped because only the first {YouTubeCog.MAX_LINKS} links are processed per message."
    )

@pytest.mark.asyncio
async def test_on_message_from_bot(youtube_cog):
    """Ensure that messages from bot accounts are ignored by on_message."""
    message = AsyncMock()
    message.author.bot = True
    message.content = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_no_links(youtube_cog):
    """Test that on_message does nothing when no links are present in the message."""
    message = AsyncMock()
    message.author.bot = False
    message.content = "This is just a normal message with no links."
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_with_empty_message(youtube_cog):
    """Ensure the bot handles empty messages gracefully."""
    message = AsyncMock()
    message.author.bot = False
    message.content = ""
    message.channel.send = AsyncMock()

    await youtube_cog.on_message(message)

    message.channel.send.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_with_mixed_links(youtube_cog):
    """Test handling a mix of valid and invalid YouTube links."""
    message = AsyncMock()
    message.author.bot = False
    message.content = (
        "Check these: https://www.youtube.com/watch?v=dQw4w9WgXcQ "
        "https://www.example.com/ "
        "https://youtu.be/dQw4w9WgXcQ "
        "https://invalid.youtube.com/watch?v=invalid"
    )
    message.channel.send = AsyncMock()

    with patch.object(youtube_cog, "fetch_video_captions", side_effect=[
        "Valid Summary 1",  
        "Valid Summary 2",  
    ]):
        await youtube_cog.on_message(message)

    message.channel.send.assert_any_call(
        "**Summary:** Valid Summary 1\n\n**Summary:** Valid Summary 2"
    )
    message.channel.send.assert_any_call(
        "The following links could not be processed:\n"
        "**https://www.example.com/** - Not a YouTube link.\n"
        "**https://invalid.youtube.com/watch?v=invalid** - Invalid YouTube URL."
    )
