"""Utility functions for HTML to Markdown converter."""

import os
import re
from pathlib import Path
from urllib.parse import urlparse


def is_external_url(url):
    """Check if a URL is external (http/https/mailto/etc)."""
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https', 'mailto', 'ftp', 'tel')


def is_special_link(url):
    """Check if a link is special (javascript, anchor only, etc)."""
    if not url:
        return False
    return url.startswith(('#', 'javascript:', 'data:'))


def normalize_path(path):
    """Normalize a path: lowercase and replace spaces with underscores."""
    # Convert to Path object for easier manipulation
    path_obj = Path(path)
    
    # Process each part of the path
    parts = []
    for part in path_obj.parts:
        if part == '/' or part == '\\':
            parts.append(part)
        else:
            # Split filename and extension
            if '.' in part and not part.startswith('.'):
                name, ext = part.rsplit('.', 1)
                normalized = name.lower().replace(' ', '_') + '.' + ext.lower()
            else:
                normalized = part.lower().replace(' ', '_')
            parts.append(normalized)
    
    # Reconstruct the path
    if path_obj.is_absolute():
        return Path(*parts)
    else:
        return Path(*parts[1:]) if parts and parts[0] == '/' else Path(*parts)


def ensure_directory_exists(path):
    """Ensure a directory exists, creating it if necessary."""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_relative_path(from_path, to_path):
    """Get relative path from one file to another."""
    from_path = Path(from_path).resolve()
    to_path = Path(to_path).resolve()
    
    # If from_path is a file, use its parent directory
    if from_path.is_file():
        from_path = from_path.parent
    
    try:
        return to_path.relative_to(from_path)
    except ValueError:
        # If paths don't share a common base, return absolute path
        return to_path


def extract_anchor(path):
    """Extract anchor from path if present."""
    if '#' in str(path):
        path_part, anchor = str(path).split('#', 1)
        return path_part, '#' + anchor
    return str(path), ''


def clean_filename(filename):
    """Clean a filename to be filesystem-safe."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    return filename