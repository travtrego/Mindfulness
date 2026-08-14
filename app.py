"""Production entrypoint for Vercel's Python runtime."""

from scripts.serve import Handler


class handler(Handler):
    """Expose the local server handler in Vercel's default format."""

