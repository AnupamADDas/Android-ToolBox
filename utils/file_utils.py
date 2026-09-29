import os
import sys

def format_size(bytes_size: int) -> str:
    """Format bytes into human readable format (KB, MB, GB)."""
    if bytes_size is None or bytes_size < 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{int(bytes_size)} B"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def sanitize_remote_path(path: str) -> str:
    """Ensure path uses POSIX slashes for Android."""
    if not path:
        return "/"
    p = path.replace("\\", "/").strip()
    if not p.startswith("/"):
        p = "/" + p
    return p

def get_file_name_from_path(path: str) -> str:
    """Extract base filename from either POSIX or Windows path."""
    return os.path.basename(path.replace("\\", "/"))
