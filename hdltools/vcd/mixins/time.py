"""Simulation time mixins."""

from hdltools.vcd.mixins import VCDParserMixin


class VCDTimeRestrictionMixin(VCDParserMixin):
    """Time restriction mixin."""

    def __init__(self, **kwargs):
        """Initialize."""
        time_range = kwargs.pop("time_range")
        super().__init__(**kwargs)
        self.add_state_hook("dump", self._time_dump_hook)
        if time_range is not None:
            if not isinstance(time_range, (tuple, list)):
                raise TypeError("time_range must be a list")
            if len(time_range) != 2:
                raise ValueError("time_range must have 2 elements exactly")
            start, end = time_range
            if not isinstance(start, int) or not isinstance(end, int):
                raise TypeError("start and end in time_range must be integers")
            self._hist_start = start
            self._hist_end = end
        else:
            self._hist_start = None
            self._hist_end = None

    @property
    def start_time(self):
        """Get start time."""
        return self._hist_start

    @property
    def end_time(self):
        """Get end time."""
        return self._hist_end

    @property
    def time_valid(self):
        """Get if we are in valid time constraints."""
        if self.start_time is not None and self.current_time < self.start_time:
            return False
        if self.end_time is not None and self.current_time > self.end_time:
            return False

        return True

    def _time_dump_hook(self, state, stmt, fields):
        """Value change hook."""
        if self.end_time is not None and self.current_time > self.end_time:
            # terminate simulation
            self._abort_parser()
