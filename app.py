"""Production entrypoint for Vercel's Python runtime."""

from scripts.serve import Handler
from generator import api as _api
from generator import critic as _critic

# Keep the HTTP surface unchanged while layering a second-model editorial pass over the
# existing generator. critic.generate_session captures the original api.generate_session at
# import time, so this assignment cannot recurse.
_api.generate_session = _critic.generate_session


class handler(Handler):
    """Expose the local server handler in Vercel's default format."""

