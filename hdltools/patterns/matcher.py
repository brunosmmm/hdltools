"""Pattern matcher."""

from hdltools.patterns import Pattern


class PatternMatcherError(Exception):
    """Pattern matcher error."""


class PatternMatcher:
    """Sequential pattern matcher."""

    def __init__(self, *expected_sequence: Pattern):
        """Initialize."""
        for pattern in expected_sequence:
            if not isinstance(pattern, Pattern):
                raise TypeError(
                    "elements from expected sequence must be Pattern objects"
                )

        # expected sequence
        self._sequence = expected_sequence

        # progress tracking
        self._progress = 0

    def matched(self):
        """Sequential pattern match complete."""

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

        return False
