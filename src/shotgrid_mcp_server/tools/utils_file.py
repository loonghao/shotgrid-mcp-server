"""
File name utilities for ShotGrid MCP server.
Provides safe file name conversion helpers.
"""

from slugify import slugify


def safe_slug_filename(name: str, ext: str = "") -> str:
    """
    Convert a string to a safe and beautiful file name using slugify.
    Optionally add extension (without dot).
    """
    slug = slugify(name, lowercase=True, separator="_")
    if ext:
        return f"{slug}.{ext}"
    return slug
