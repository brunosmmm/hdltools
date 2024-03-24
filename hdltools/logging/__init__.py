"""Logs and messages."""

import os
import sys
import inspect
from rich.console import Console
from rich.style import Style


class DefaultLogger:
    """Sedona Logger."""

    LOG_LEVELS = {"debug": 0, "info": 1, "warning": 2, "error": 3, "none": 99}

    def __init__(self, level="info", prefix="", dest=sys.stdout):
        """Initialize."""
        self._level = level
        self._prefix = prefix
        self._dest = dest
        self._console = Console(file=self._dest)

    def _will_show_msg(self, level):
        if self.LOG_LEVELS[level] < self.LOG_LEVELS[self._level]:
            return False

        return True

    def rich_print(self, *args, **kwargs):
        """Print directly using rich."""
        self._console.print(*args, **kwargs)

    def message(self, level, message, ignore_level=False, **kwargs):
        """Log a message."""
        if not self._will_show_msg(level) and not ignore_level:
            return

        if "style" in kwargs and kwargs["style"] is not None:
            style = kwargs["style"]
        else:
            style = ""

        self._console.print(self._prefix + message, style=style)

    def warning(self, message):
        """Show warning."""
        self.message(
            level="warning",
            message=f"WARNING: {message}",
            style="bold yellow",
        )

    def error(self, message):
        """Show error."""
        self.message(
            level="error",
            message=f"ERROR: {message}",
            style="bold red",
        )

    def info(self, message):
        """Show informative message."""
        self.message(
            level="info",
            message=f"INFO: {message}",
            style="bold white",
        )

    def debug(self, message):
        """Show debug message."""
        self.message(
            level="debug",
            message=f"DEBUG: {message}",
            style="cyan",
        )

    def dev_debug(self, message):
        """Show development debug message."""
        if os.environ.get("DEBUG", False):
            frame = inspect.stack()[1]
            mod = inspect.getmodule(frame[0])
            if hasattr(mod, "__name__"):
                modname = mod.__name__
            else:
                modname = "unknown"
            style = Style(bgcolor="red", color="white", bold=True)
            self.message(
                level="debug",
                message=f"DEBUG: {modname}: {message}",
                style=style,
            )

    def set_level(self, level):
        """Set logging level."""
        self._level = level


DEFAULT_LOGGER = DefaultLogger(dest=sys.stderr)
