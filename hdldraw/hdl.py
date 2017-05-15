"""Common HDL declaration elements."""


class HDLVectorDescriptor(object):
    """Describe a vector signal."""

    def __init__(self, right_size, left_size):
        """Initialize.

        Args
        ----
        left_size: int
           Size on the left of vector declaration
        right_size: int
           Size on the right of vector declaration
        """
        if not isinstance(right_size, int) or not isinstance(left_size, int):
            raise TypeError('only int allowed as vector size')

        if (right_size < 0) or (left_size < 0):
            raise ValueError('only positive values allowed for sizes')

        self.right_size = right_size
        self.left_size = left_size

    def __len__(self):
        """Get vector length."""
        return abs(self.left_size - self.right_size) + 1


class HDLModulePort(object):
    """HDL Module port."""

    _port_directions = ['in', 'out', 'inout']

    def __init__(self, direction, name, size=1):
        """Initialize.

        Args
        ----
        direction: str
           Port direction
        size: int, tuple or HDLVectorDescriptor
           Port description
        name: str
           Port name
        """
        if direction not in self._port_directions:
            raise ValueError('invalid port direction: "{}"'.format(direction))

        self.direction = direction
        self.name = name

        if isinstance(size, int):
            # default is [size-1:0] / (size-1 downto 0)
            if (size < 0):
                raise ValueError('only positive size allowed')
            self.vector = HDLVectorDescriptor(size-1, 0)
        elif isinstance(size, (tuple, list)):
            if len(size) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(size))
            self.vector = HDLVectorDescriptor(*size)
        elif isinstance(size, HDLVectorDescriptor):
            self.vector = size
        else:
            raise TypeError('size can only be of types: int, list or'
                            ' HDLVectorDescriptor')
