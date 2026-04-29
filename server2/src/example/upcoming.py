import yt_dlp
from datetime import datetime

def get_upcoming_livestreams(channel_url):
    """
    Fetches all scheduled, upcoming live streams for a given YouTube channel.
    """
    # Target the livestreams tab specifically
    if not channel_url.endswith('/streams'):
        channel_url = channel_url.rstrip('/') + '/streams'

    # Configure yt-dlp options
    ydl_opts = {
        'extract_flat': True,  
        'quiet': True,         
        'no_warnings': True    
    }

    upcoming_streams = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    # Filter specifically for scheduled upcoming streams
                    if entry.get('live_status') == 'is_upcoming':
                        
                        # Grab the timestamp if it exists and convert it to a readable format
                        timestamp = entry.get('release_timestamp')
                        scheduled_time = "Unknown"
                        if timestamp:
                            scheduled_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                        upcoming_streams.append({
                            'title': entry.get('title'),
                            'url': entry.get('url'),
                            'scheduled_time': scheduled_time
                        })
        except Exception as e:
            print(f"An error occurred while fetching the channel: {e}")

    return upcoming_streams

# --- Example Usage ---
if __name__ == "__main__":
    # Example: SpaceX usually has upcoming streams scheduled
    target_channel = "https://www.youtube.com/channel/UC-hM6YJuNYVAmUWxeIr9FeA" 
    
    print(f"Checking {target_channel} for scheduled upcoming streams...\n")
    
    upcoming = get_upcoming_livestreams(target_channel)

    if upcoming:
        print(f"✅ Found {len(upcoming)} upcoming live stream(s):\n")
        for idx, stream in enumerate(upcoming, start=1):
            print(f"{idx}. {stream['title']}")
            print(f"   Link:      {stream['url']}")
            print(f"   Scheduled: {stream['scheduled_time']}")
            print("-" * 40)
    else:
        print("❌ No upcoming streams found for this channel.")