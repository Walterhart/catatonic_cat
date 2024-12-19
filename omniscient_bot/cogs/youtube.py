from discord.ext import commands
import re
import os
import requests

TOKEN = os.getenv("YOUTUBE_TOKEN")

class YouTubeCog(commands.Cog):
    """A cog for detecting YouTube links."""

    MAX_LINKS = 5  # Limit the number of links processed per message

    def __init__(self, bot):
        self.bot = bot

    def extract_video_id(self, url):
        """Extract video ID from YouTube URL."""
        # Match only valid YouTube URLs
        match = re.search(r'(?:https?://(?:www\.)?(youtube\.com/watch\?v=|youtu\.be/))([^&?/\s]+)', url)
        return match.group(2) if match else None

    def fetch_video_details(self, video_id):
        """Fetch video details from YouTube API."""
        try:
            url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={TOKEN}"
            response = requests.get(url)
            response.raise_for_status()  
            
            data = response.json()
            if data.get("items"):
                return data["items"][0]["snippet"]  # Returns snippet with title, description, etc.
            else:
                return {"error": "Video not found. It may have been removed or set to private."}
        
        except requests.exceptions.RequestException as e:
            # Handle request errors 
            print(f"Error fetching video details: {e}")
            return {"error": "An error occurred while contacting the YouTube API."}
        except KeyError:
            # Handle unexpected JSON structure
            print("Error parsing video details: Missing expected fields in the response.")
            return {"error": "Unexpected error occurred while fetching video details."}


    @commands.Cog.listener()
    async def on_message(self, message):
        """Detect YouTube links and fetch video details."""
        if message.author.bot:  # Ignore bot messages
            return

        valid_responses = []
        invalid_responses = []

        # Find URLs in the message
        urls = re.findall(r'(https?://[^\s]+)', message.content)
        urls_to_process = urls[:self.MAX_LINKS]  # Limit the number of links processed
        skipped_count = len(urls) - self.MAX_LINKS  

        for url in urls_to_process:
            try:
                if 'youtube.com' in url or 'youtu.be' in url:
                    video_id = self.extract_video_id(url)
                    if video_id:
                        video_details = self.fetch_video_details(video_id)
                        if "error" in video_details:
                            invalid_responses.append(f"**{url}** - {video_details['error']}")
                        else:
                            title = video_details['title']
                            description = video_details['description']
                            shorten_description = (description[:300] + '...') if len(description) > 300 else description
                            valid_responses.append(f"**Video Title:** {title}\n**Description:** {shorten_description}")
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
