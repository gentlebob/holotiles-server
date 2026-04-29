import yt_dlp

def get_active_livestreams(channel_url):
    """
    Fetches all currently live streams for a given YouTube channel.
    """
    # Append '/streams' to the channel URL to specifically target the livestreams tab
    # This prevents extracting regular VODs and speeds up the process.
    if not channel_url.endswith('/streams'):
        channel_url = channel_url.rstrip('/') + '/streams'

    # Configure yt-dlp options
    ydl_opts = {
        'extract_flat': True,  # Extract metadata only (don't download the video)
        'quiet': True,         # Suppress standard console output
        'no_warnings': True    # Suppress warnings
    }

    live_streams = []

    # Initialize yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Fetch the playlist data
            info = ydl.extract_info(channel_url, download=False)
            
            # Loop through the entries in the playlist
            if 'entries' in info:
                for entry in info['entries']:
                    # Check if the entry is currently live. 
                    # yt-dlp exposes this via the 'live_status' key or 'is_live' boolean.
                    if entry.get('live_status') == 'is_live' or entry.get('is_live') is True:
                        live_streams.append({
                            'title': entry.get('title'),
                            'url': entry.get('url'),
                            'view_count': entry.get('view_count', 'Unknown')
                        })
        except Exception as e:
            print(f"An error occurred while fetching the channel: {e}")

    return live_streams

# --- Example Usage ---
if __name__ == "__main__":
    # Example: Lofi Girl's channel, which almost always has an active live stream
    target_channel = "https://www.youtube.com/channel/UC-hM6YJuNYVAmUWxeIr9FeA" 
    
    print(f"Checking {target_channel} for active live streams...\n")
    
    active_streams = get_active_livestreams(target_channel)

    if active_streams:
        print(f"✅ Found {len(active_streams)} active live stream(s):\n")
        for idx, stream in enumerate(active_streams, start=1):
            print(f"{idx}. {stream['title']}")
            print(f"   Link:    {stream['url']}")
            print(f"   Viewers: {stream['view_count']}")
            print("-" * 40)
    else:
        print("❌ No currently live streams found for this channel.")
