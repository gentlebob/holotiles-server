import yt_dlp

def get_active_livestreams(channel_url):
    """
    Fetches all currently live streams for a given YouTube channel.
    """
    # Append '/streams' to the channel URL to specifically target the livestreams tab
    # This prevents extracting regular VODs and speeds up the process.
    if not channel_url.endswith('/streams'):
        channel_url = channel_url.rstrip('/') + '/streams'

    # Configure yt-dlp options.
    # NOTE: 'extract_flat' is intentionally NOT set. Flat extraction of a YouTube
    # channel /streams tab no longer populates 'live_status' / 'is_live' on entries
    # (yt-dlp / YouTube response change), so we'd never match anything. Full extraction
    # is slower but is the only way to reliably tell live from past streams here.
    ydl_opts = {
        'quiet': True,         # Suppress standard console output
        'no_warnings': True,   # Suppress warnings
        'skip_download': True, # Metadata only
        'ignoreerrors': True,  # Don't abort the whole batch if one entry fails
                               # (some past streams return "We're processing this video")
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
    target_channel = "https://www.youtube.com/@LofiGirl" 
    
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
