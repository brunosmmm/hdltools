"""Sequential block."""

from .stmt import HDLStatement
from .scope import HDLScope
from .sens import HDLSensitivityList


class HDLSequentialBlock(HDLStatement):
    """Sequential block."""

    def __init__(self, sensitivity_list=None, **kwargs):
        """Initialize."""
        super().__init__(stmt_type="par", has_scope=True, **kwargs)
        self.scope = HDLScope(scope_type="seq", parent=self)

        # parse sensitivity list?
        if not isinstance(sensitivity_list, (HDLSensitivityList, type(None))):
            raise TypeError("only HDLSensitivityList allowed")

        self.sens_list = sensitivity_list

    def add(self, *items):
        """Add to scope."""
        self.scope.add(items)

    def dumps(self):
        """Get representation."""
        ret_str = "SEQ({}) BEGIN\n".format(self.sens_list.dumps())
        ret_str += self.scope.dumps()
        ret_str += "\nEND\n"

        return ret_str

    def is_legal(self):
        """Check legality."""
        if len(self.scope) == 0:
            return False

        return True

    def get_scope(self):
        """Get scope."""
        return self.scope
