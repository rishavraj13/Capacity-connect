"""Development settings module with debug defaults enabled."""

from config.settings.base import *  # noqa: F403

DEBUG: bool = env.bool("DEBUG", default=True)  # noqa: F405
ALLOWED_HOSTS: list[str] = env.list(  # noqa: F405
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"],
)
