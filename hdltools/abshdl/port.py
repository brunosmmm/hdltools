"""HDL Ports."""

from hdltools.abshdl import HDLObject
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.vector import HDLVectorDescriptor


class HDLAbsModulePort(HDLObject):
    """Abstract class from which different port types derive."""

    _port_directions = ["in", "out", "inout"]

    def __init__(self, direction, name):
        """Initialize."""
        if direction not in self._port_directions:
            raise ValueError('invalid port direction: "{}"'.format(direction))

        self._direction = direction
        self._name = name

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        raise NotImplementedError()

    def dumps(self, eval_scope=None):
        """Alias for __repr__."""
        return self.__repr__(eval_scope)

    def __pos__(self):
        """Access internal signal as an expression."""
        return HDLExpression(self.signal)

    def __neg__(self):
        """Access internal signal."""
        return self.signal

    @property
    def direction(self):
        """Get direction."""
        return self._direction

    @property
    def name(self):
        """Get name."""
        return self._name

    def rename(self, new_name):
        """Rename port."""
        self._name = new_name


class HDLModuleTypedPort(HDLAbsModulePort):
    """Typed ports."""

    def __init__(self, direction, name, ptype):
        """Initialize."""
        super().__init__(direction, name)

        # create internal signal
        self.signal = HDLSignal(
            sig_type="var", sig_name=name, var_type=ptype, size=None
        )

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        return "{} {} {}".format(
            self.direction.upper(), self.signal.var_type, self.name
        )


class HDLModulePort(HDLAbsModulePort):
    """HDL Module port."""

    def __init__(self, direction, name, size=1):
        """Initialize.

        Args
        ----
        direction: str
           Port direction
        size: int, tuple or vector.HDLVectorDescriptor
           Port description
        name: str
           Port name
        """
        super().__init__(direction, name)
        if isinstance(size, int):
            # default is [size-1:0] / (size-1 downto 0)
            if size < 0:
                raise ValueError("only positive size allowed")
            self.vector = HDLVectorDescriptor(size - 1, 0)
        elif isinstance(size, (tuple, list)):
            if len(size) != 2:
                raise ValueError(
                    "invalid vector " 'dimensions: "{}"'.format(size)
                )
            self.vector = HDLVectorDescriptor(*size)
        elif isinstance(size, HDLVectorDescriptor):
            self.vector = size
        elif isinstance(size, HDLExpression):
            self.vector = HDLVectorDescriptor(left_size=size - 1)
        else:
            raise TypeError(
                "size can only be of types: int, list or"
                " vector.HDLVectorDescriptor"
            )

        # create internal signal
        self.signal = HDLSignal(sig_type="comb", sig_name=name, size=size)

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        return "{} {}{}".format(
            self.direction.upper(), self.name, self.vector.dumps(eval_scope)
        )

    def __getitem__(self, index):
        """Emulate subscript."""
        return HDLSignalSlice(self.signal, index)
