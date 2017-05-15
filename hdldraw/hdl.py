"""Common HDL declaration elements."""


class HDLExpression(object):
    """An expression involving parameters."""

    pass


class HDLVectorDescriptor(object):
    """Describe a vector signal."""

    def __init__(self, left_size, right_size=None, stored_value=None):
        """Initialize.

        Args
        ----
        left_size: int
           Size on the left of vector declaration
        right_size: int, NoneType
           Size on the right of vector declaration
        stored_value: int, NoneType
           A stored value
        """
        if not isinstance(left_size, int):
            raise TypeError('only int allowed as vector size')

        if not isinstance(right_size, int):
            if right_size is None:
                # take this as zero
                right_size = 0

        if not isinstance(stored_value, (int, (type(None)))):
            raise TypeError('stored_value can only be int or None')

        if (right_size < 0) or (left_size < 0):
            raise ValueError('only positive values allowed for sizes')

        self.right_size = right_size
        self.left_size = left_size
        self.stored_value = stored_value

    def __len__(self):
        """Get vector length."""
        return abs(self.left_size - self.right_size) + 1

    def __repr__(self):
        """Represent."""
        return '[{}:{}]'.format(self.left_size, self.right_size)

    def dumps(self):
        """Dump description to string."""
        return self.__repr__()


class HDLModuleParameter(object):
    """Module parameter / generic values."""

    def __init__(self, param_name, param_type, param_default=None):
        """Initialize.

        Args
        ----
        param_name: str
           Parameter name
        param_type: str
           Parameter type
        param_default: object
           Parameter value
        """
        self.name = param_name
        self.ptype = param_type
        self.value = param_default

    def __repr__(self):
        """Get readable representation."""
        ret_str = '#{} {}'.format(self.ptype.upper(),
                                  self.name.upper())
        if self.value is not None:
            ret_str += ' ({})'.format(self.value)

        return ret_str

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()


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

    def __repr__(self):
        """Get readable representation."""
        return '{} {}{}'.format(self.direction.upper(),
                                self.name,
                                self.vector.dumps())

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()


class HDLModule(object):
    """HDL Module."""

    def __init__(self, module_name, ports=None, params=None):
        """Initialize.

        Args
        ----
        module_name: str
            Module or entity name
        ports: list
            List of ports in module declaration
        """
        self.name = module_name
        self.ports = []
        self.params = []
        if params is not None:
            self.add_parameters(params)
        if ports is not None:
            self.add_ports(ports)

    def add_ports(self, ports):
        """Add ports to module.

        Args
        ----
        ports: list or HDLModulePort
            List of ports to be added
        """
        # TODO: duplicate port verification
        if isinstance(ports, HDLModulePort):
            self.ports.append(ports)
        elif isinstance(ports, (tuple, list)):
            for port in ports:
                if not isinstance(port, HDLModulePort):
                    raise TypeError('list may only contain HDLModulePort'
                                    ' instances')
                self.ports.extend(ports)
        else:
            raise TypeError('ports must be a list or HDLModulePort')

    def add_parameters(self, params):
        """Add parameters to module.

        Args
        ----
        params: list or HDLModuleParameter
            List of parameters to be added.
        """
        # TODO: duplicate parameter verification
        if isinstance(params, HDLModuleParameter):
            self.params.append(params)
        elif isinstance(params, (tuple, list)):
            for param in params:
                if not isinstance(param, HDLModuleParameter):
                    raise TypeError('list may only contain HDLModuleParameter'
                                    ' instances')
                self.params.extend(params)
        else:
            raise TypeError('params must be a list or HDLModuleParameter')

    def __repr__(self):
        """Get readable representation."""
        ret_str = '{} {{\n'.format(self.name.upper())

        for param in self.params:
            ret_str += '{}\n'.format(param.dumps())

        for port in self.ports:
            ret_str += '    {}\n'.format(port.dumps())

        ret_str += '}'
        return ret_str

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()
