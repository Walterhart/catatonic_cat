from discord.ext import commands
import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
from deepmultilingualpunctuation import PunctuationModel
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from spellchecker import SpellChecker

class YouTubeCog(commands.Cog):
    """A cog for detecting YouTube links and processing captions."""

    MAX_LINKS = 5  # Limit the number of links processed per message

    def __init__(self, bot):
        self.bot = bot
        self.punct_model = PunctuationModel()
        self.spell = SpellChecker()

    def extract_video_id(self, url):
        """Extract video ID from YouTube URL."""
        # Match only valid YouTube URLs
        match = re.search(r'(?:https?://(?:www\.)?(youtube\.com/watch\?v=|youtu\.be/))([^&?/\s]+)', url)
        return match.group(2) if match else None

    def correct_spelling(self, text):
        """Correct spelling errors in text."""
        corrected_text = []
        words = text.split()
        for word in words:
            corrected_word = self.spell.correction(word)
            if corrected_word and corrected_word.endswith('e') and word.endswith('es'):
                corrected_word += 's'  # Retain plural form if nedded
            elif corrected_word and word.endswith('s') and not corrected_word.endswith('s'):
                corrected_word += 's'
            corrected_text.append(corrected_word or word)  
        return ' '.join(corrected_text)


    def summarize_text(self, text, num_sentences=5):
        """Summarize text using LSA Summarizer."""
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, num_sentences)
        return " ".join(str(sentence) for sentence in summary)

    def preprocess_captions(self, captions):
        """C orrect spelling and restore punctuation."""
        corrected_text = self.correct_spelling(captions)
        punctuated_text = self.punct_model.restore_punctuation(corrected_text)
        return punctuated_text

    def fetch_video_captions(self, video_id):
        """Fetch and preprocess captions from a YouTube video."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            captions = " ".join([item['text'] for item in transcript])
            processed_captions = self.preprocess_captions(captions)
            summary = self.summarize_text(processed_captions)
            return summary
        except TranscriptsDisabled:
            print(f"Captions are disabled for video {video_id}.")
            return None
        except VideoUnavailable:
            print(f"Video {video_id} is unavailable.")
            return None
        except Exception as e:
            print(f"An error occurred while fetching captions: {e}")
            return None

    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect YouTube links and fetch video captions."""
        if message.author.bot:
            return

        valid_responses = []
        invalid_responses = []

        # Find URLs in the message
        urls = re.findall(r'(https?://[^\s]+)', message.content)
        urls_to_process = urls[:self.MAX_LINKS]
        skipped_count = len(urls) - self.MAX_LINKS

        for url in urls_to_process:
            try:
                if 'youtube.com' in url or 'youtu.be' in url:
                    video_id = self.extract_video_id(url)  
                    if video_id:
                        summary = self.fetch_video_captions(video_id)
                        if summary:
                            valid_responses.append(f"**Summary:** {summary}")
                        else:
                            invalid_responses.append(f"**{url}** - Captions are unavailable.")
                    else:
                        invalid_responses.append(f"**{url}** - Invalid YouTube URL.")
                else:
                    invalid_responses.append(f"**{url}** - Not a YouTube link.")
            except Exception as e:
                print(f"Unexpected error processing URL {url}: {e}")
                invalid_responses.append(f"**{url}** - An unexpected error occurred while processing this link.")

        # Notify if some links were skipped
        if skipped_count > 0:
            await message.channel.send(
                f"Max links summarized reached. {skipped_count} YouTube link(s) were skipped because only the first {self.MAX_LINKS} links are processed per message."
            )

        # Send responses
        if valid_responses:
            await message.channel.send("\n\n".join(valid_responses))
        if invalid_responses:
            await message.channel.send(f"The following links could not be processed:\n" + "\n".join(invalid_responses))

# Required setup function to add the cog
async def setup(bot):
    await bot.add_cog(YouTubeCog(bot))
