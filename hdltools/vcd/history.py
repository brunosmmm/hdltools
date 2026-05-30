"""VCD value history."""

from typing import Set
from hdltools.vcd import VCDObject, VCDScope


class VCDValueHistoryEntry(VCDObject):
    """Value history entry."""

    def __init__(self, scope: VCDScope, signal: str, time: int):
        """Initialize.

        :param scope: The current VCD scope
        :param signal: Signal name
        :param time: Change time
        """
        super().__init__()
        self._scope = scope
        self._signal = signal
        # FIXME: convert value to integer in VCD parser, not here
        self._time = int(time)

    @property
    def scope(self) -> VCDScope:
        """Get scope."""
        return self._scope

    @property
    def signal(self) -> str:
        """Get signal name."""
        return self._signal

    @property
    def time(self) -> int:
        """Get time."""
        return self._time

    def __repr__(self):
        """Get representation."""
        return "{{{}::{} @{}}}".format(str(self.scope), self.signal, self.time)

    def __eq__(self, other):
        """Test equality."""
        if not isinstance(other, VCDValueHistoryEntry):
            return NotImplemented
        if other.scope != self.scope:
            return False

        if other.signal != self.signal:
            return False

        if other.time != self.time:
            return False

        return True

    def __hash__(self):
        """Get hash."""
        return hash(tuple([self.scope, self.signal, self.time]))


class VCDValueHistory(VCDObject):
    """VCD Value history."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._history = []

    def __getitem__(self, idx):
        """Get item."""
        return self._history[idx]

    def __iter__(self):
        """Iterate over history entries."""
        return iter(self._history)

    def get_by_time(self, time: int) -> VCDValueHistoryEntry:
        """Get history entry by simulation time.

        :param time: Time slot in VCD
        :return: A value history entry
        """
        for item in self._history:
            if item.time == time:
                return item

        raise IndexError("invalid item index")

    def add_entry(self, entry: VCDValueHistoryEntry):
        """Add history entry.

        :param: History entry to add
        """
        if not isinstance(entry, VCDValueHistoryEntry):
            raise TypeError("entry must be a VCDValueHistoryEntry object")
        self._history.append(entry)

    def __len__(self):
        """Get length."""
        return len(self._history)

    @property
    def visited_scopes(self) -> Set[VCDScope]:
        """Determine all visited scopes."""
        return {entry.scope for entry in self._history}
