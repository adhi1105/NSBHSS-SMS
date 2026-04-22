from django import template
from urllib.parse import urlparse, parse_qs

register = template.Library()

@register.filter(name='youtube_embed')
def youtube_embed(url):
    """
    Robustly extracts the YouTube ID from various URL formats:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://www.youtube.com/embed/dQw4w9WgXcQ
    """
    if not url:
        return ""
    
    # Clean the URL (remove surrounding spaces)
    url = url.strip()
    
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Case 1: Standard URL (youtube.com/watch?v=ID)
    if 'youtube.com' in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get('v', [None])[0]
        
        # Handle case where it's already an embed link (youtube.com/embed/ID)
        if not video_id and 'embed' in parsed_url.path:
            video_id = parsed_url.path.split('/')[-1]

    # Case 2: Short URL (youtu.be/ID)
    elif 'youtu.be' in parsed_url.netloc:
        video_id = parsed_url.path.lstrip('/')
    
    else:
        video_id = None

    # Return the clean Embed URL if ID found, else return original (or empty)
    if video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    
    return ""