"""Pre and post-condition mixins."""

from hdltools.vcd.mixins.trigger import VCDTriggerMixin
from hdltools.vcd.trigger import VCDTriggerDescriptor


class VCDConditionMixin(VCDTriggerMixin):
    """Condition mixin."""

    def __init__(self, **kwargs):
        """Initialize."""
        postconditions = kwargs.pop("postconditions")
        preconditions = kwargs.pop("preconditions")
        super().__init__(**kwargs)
        self._postconditions = []
        self._preconditions = []

        self._wait_precondition = False
        self._wait_postcondition = False
        if postconditions is not None:
            if isinstance(postconditions, VCDTriggerDescriptor):
                self._postconditions.append(postconditions)
            else:
                for postcondition in postconditions:
                    if not isinstance(postcondition, VCDTriggerDescriptor):
                        raise TypeError(
                            "precondition must be a VCDTriggerDescriptor object"
                        )
                    self._postconditions.append(postcondition)
        if preconditions is not None:
            self._wait_precondition = True
            if isinstance(preconditions, VCDTriggerDescriptor):
                self.add_trigger_level(preconditions)
            else:
                for precondition in preconditions:
                    if not isinstance(precondition, VCDTriggerDescriptor):
                        raise TypeError(
                            "precondition must be a VCDTriggerDescriptor object"
                        )
                    self.add_trigger_level(precondition)

            # arm trigger
            self.trigger_callback = self._precondition_callback
            self.arm_trigger()

    def _precondition_callback(self, *args):
        """Precondition callback."""
        if self._debug:
            print(
                "DEBUG: {} trigger reached_preconditions".format(
                    self.current_time
                )
            )
        self._wait_precondition = False
        # setup postconditions
        if self._postconditions:
            self._wait_postcondition = True
            self.trigger_reset()
            for postcondition in self._postconditions:
                self.add_trigger_level(postcondition)

            self.trigger_callback = self._postcondition_callback
            self.arm_trigger()

    def _postcondition_callback(self, *args):
        """Postcondition callback."""
        if self._debug:
            print(
                "DEBUG: {} trigger reached_postconditions".format(
                    self.current_time
                )
            )
        self._wait_postcondition = False
        self._abort_parser()

    @property
    def waiting_precondition(self):
        """Get wheter waiting precondition."""
        return self._wait_precondition is True and self.triggered is False
