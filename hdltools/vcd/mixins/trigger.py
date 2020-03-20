"""Trigger mixin."""

from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin
from hdltools.vcd.trigger.fsm import SimpleTrigger


class VCDTriggerMixin(VCDHierarchyAnalysisMixin, SimpleTrigger):
    """Trigger mixin."""

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self.add_state_hook("dump", self._dump_hook)

    def _mixin_init(self):
        """Mixin initialization."""

    def _dump_hook(self, state, stmt, fields):
        """Value change hook."""
        # match
        # FIXME: match against proper statement
        if "var" not in fields:
            return
        self.match_and_advance(state, fields["var"], fields["value"])
