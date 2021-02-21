"""Logs and messages."""

import sys
import colorama


class DefaultLogger:
    """Default Logger."""

    LOG_LEVELS = {"debug": 0, "info": 1, "warning": 2, "error": 3, "none": 99}

    def __init__(self, level="info", prefix="", dest=sys.stdout):
        """Initialize."""
        self._level = level
        self._prefix = prefix
        self._dest = dest

    def _will_show_msg(self, level):
        if self.LOG_LEVELS[level] < self.LOG_LEVELS[self._level]:
            return False

        return True

    def message(self, level, message, **kwargs):
        """Log a message."""
        if not self._will_show_msg(level):
            return

        # print stuff
        if "style" in kwargs and kwargs["style"] is not None:
            style = kwargs["style"]
        else:
            style = ""

        print(
            style + self._prefix + message + colorama.Style.RESET_ALL,
            file=self._dest,
        )

    def warning(self, message):
        """Show warning."""
        self.message(
            level="warning",
            message="WARNING: {}".format(message),
            style=colorama.Fore.YELLOW + colorama.Style.BRIGHT,
        )

    def error(self, message):
        """Show error."""
        self.message(
            level="error",
            message="ERROR: {}".format(message),
            style=colorama.Fore.RED + colorama.Style.BRIGHT,
        )

    def info(self, message):
        """Show informative message."""
        self.message(
            level="info",
            message="INFO: {}".format(message),
            style=colorama.Fore.WHITE + colorama.Style.BRIGHT,
        )

    def debug(self, message):
        """Show debug message."""
        self.message(
            level="debug",
            message="DEBUG: {}".format(message),
            style=colorama.Fore.CYAN,
        )

    def dev_debug(self, message):
        """Show development debug message."""
        self.message(
            level="debug",
            message="DEBUG: {}".format(message),
            style=colorama.Fore.WHITE
            + colorama.Back.RED
            + colorama.Style.BRIGHT,
        )

    def set_level(self, level):
        """Set logging level."""
        self._level = level


DEFAULT_LOGGER = DefaultLogger()
