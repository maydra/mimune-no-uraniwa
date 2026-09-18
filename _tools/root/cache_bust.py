import os
import re
from datetime import datetime

# Configuration
TARGET_EXTENSIONS = ('.html', '.htm')
VERSION_PARAM = 'v'
TIMESTAMP_FORMAT = '%Y%m%d%H%M'

# Regex patterns to target <link href="..."> and <script src="...">
LINK_RE = re.compile(r'(<link[^>]+href=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE)
SCRIPT_RE = re.compile(r'(<script[^>]+src=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE)

def is_external(url):
    """Checks if the URL is external (starts with http, https, or //)."""
    return url.startswith(('http://', 'https://', '//'))

def update_url(url, timestamp):
    """Appends or updates the version query parameter in the URL."""
    if is_external(url):
        return url
    
    # Handle existing query parameters
    if '?' in url:
        path, query = url.split('?', 1)
        # If the version parameter already exists, replace its value
        if f'{VERSION_PARAM}=' in query:
            new_query = re.sub(rf'{VERSION_PARAM}=[^&]*', f'{VERSION_PARAM}={timestamp}', query)
            return f"{path}?{new_query}"
        else:
            # Append the version parameter to other existing parameters
            return f"{url}&{VERSION_PARAM}={timestamp}"
    else:
        # No query parameters, add the version parameter
        return f"{url}?{VERSION_PARAM}={timestamp}"

def process_file(filepath, timestamp):
    """Reads, processes, and writes back the HTML file if changes were made."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding if utf-8 fails
        try:
            with open(filepath, 'r', encoding='shift-jis') as f:
                content = f.read()
        except:
            print(f"Skipping {filepath}: Unable to decode file.")
            return

    modified = False

    def replacer(match):
        prefix, url, suffix = match.groups()
        # Only target certain assets if you want to be more specific, 
        # but the request was for "assets such as CSS and JavaScript".
        # We process all local links found in these tags.
        new_url = update_url(url, timestamp)
        if new_url != url:
            nonlocal modified
            modified = True
            return f"{prefix}{new_url}{suffix}"
        return match.group(0)

    # Process both link and script tags
    content = LINK_RE.sub(replacer, content)
    content = SCRIPT_RE.sub(replacer, content)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

def main():
    # Use the current time for the version string
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    print(f"Starting cache busting with version: {timestamp}")
    
    count = 0
    # Walk through the directory and its subdirectories
    for root, _, files in os.walk('.'):
        for file in files:
            if file.lower().endswith(TARGET_EXTENSIONS):
                filepath = os.path.join(root, file)
                # Avoid processing the script itself if it's named something targeting HTML extensions (unlikely here)
                process_file(filepath, timestamp)
                count += 1

    print(f"Finished processing {count} HTML files.")

if __name__ == "__main__":
    main()
