# Standard library imports
import feedparser # For parsing RSS feeds to extract podcast episode information
import urllib.request # For making HTTP requests, primarily to download audio files

class RSSFetcher:
    """
    A class to parse podcast RSS feeds and extract episode audio URLs.
    """

    def parse_feed(self, rss_url, max_episodes=5):
        """
        Parses the RSS feed URL to extract podcast episode details.
        It looks for audio enclosures or links.

        Args:
            rss_url (str): The URL of the podcast's RSS feed.
            max_episodes (int): The maximum number of episodes to parse from the feed.

        Returns:
            list: A list of dictionaries, each containing 'title' and 'audio_url' for an episode.
        """
        print(f"Parsing RSS feed: {rss_url}")
        
        req = urllib.request.Request(
            rss_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        )
        with urllib.request.urlopen(req) as response:
            feed = feedparser.parse(response.read())
    
        print(f"Found {len(feed.entries)} entries in feed.")

        episodes = []
        for entry in feed.entries[:max_episodes]:
            audio_url = None

            # Prioritize 'enclosures' as they typically contain the direct audio file link
            for enclosure in entry.get("enclosures", []):
                if enclosure.get("type", "").startswith("audio/"):
                    audio_url = enclosure.get("href")
                    break

            # If no audio found in enclosures, check 'links' for audio types
            if not audio_url:
                for link in entry.get("links", []):
                    if link.get("type", "").startswith("audio"):
                        audio_url = link.get("href")
                        break

            if audio_url:
                # Basic validation for audio_url to ensure it's a non-empty string
                if isinstance(audio_url, str) and audio_url.strip():
                    episodes.append({
                        "title": entry.get("title", "Untitled Episode"),
                        "audio_url": audio_url.strip()
                    })
                    print(f"  ✅ Added episode: '{entry.get('title', 'Untitled Episode')}'")
                else:
                    print(f"  Skipping entry '{entry.get('title', 'Untitled')}' due to invalid audio URL.")
            else:
                print(f"  No audio found for entry: '{entry.get('title', 'Untitled')}'")

        print(f"Returning {len(episodes)} episodes with valid audio URLs.")
        return episodes

