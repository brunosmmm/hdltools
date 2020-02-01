"""Pattern matcher."""

from typing import Callable, Optional
from hdltools.patterns import Pattern


class PatternMatcherError(Exception):
    """Pattern matcher error."""


class PatternMatcher:
    """Sequential pattern matcher.

    Arguments
    ---------
    expected_sequence
      List of expected patterns in order
    restart_on_unmatched
      Restart matching sequence on new state that does not match expected
    match_cb
      Optional callback to be called on match
    initial
      Optional initial value
    """

    def __init__(
        self,
        *expected_sequence: Pattern,
        restart_on_unmatched: bool = True
        match_cb: Optional[Callable] = None,
        initial: Optional[str] = None
    ):
        """Initialize."""
        for pattern in expected_sequence:
            if not isinstance(pattern, Pattern):
                raise TypeError(
                    "elements from expected sequence must be Pattern objects"
                )

        # optional callback
        if match_cb is not None and not callable(match_cb):
            raise TypeError("match_cb must be a callable")
        self._match_cb = match_cb

        # initial value
        if initial is not None and not isinstance(initial, str):
            raise TypeError("initial value must be string")
        self._initial = initial

        # expected sequence
        self._sequence = expected_sequence

        # progress tracking
        self._progress = 0
        self._restart_unmatch = restart_on_unmatched

    @property
    def initial(self):
        """Get initial value."""
        return self._initial

    @initial.setter
    def initial(self, value: str):
        """Set initial value."""
        if not isinstance(value, str):
            raise TypeError("value must be string")
        if self._progress > 0:
            raise PatternMatcherError(
                "matching in progress, cannot set initial value"
            )
        self._initial = value

    def matched(self):
        """Sequential pattern match complete."""
        if self._match_cb is not None:
            self._match_cb(self)

    def restart(self):
        """Restart matching sequence."""
        self._progress = 0

    @property
    def progress(self):
        """Get progress."""
        return self._progress

    def __len__(self):
        """Get sequence length."""
        return len(self._sequence)

    def __getitem__(self, index: int) -> Pattern:
        """Get a pattern from the sequence."""
        return self._sequence[index]

    def new_state(self, value: str) -> bool:
        """Act on new state."""
        if self._progress == len(self._sequence):
            # finished already
            raise PatternMatcherError("sequential matching already complete")

        # try to match
        if self._sequence[self._progress].match(value):
            if self._progress == len(self._sequence) - 1:
                # finished
                self.matched()
            self._progress += 1
            return True

        # restart sequence
        if self._restart_unmatch:
            self._progress = 0

        return False
