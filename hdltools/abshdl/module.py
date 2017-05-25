"""HDL Module."""

from . import HDLObject
from .vector import HDLVectorDescriptor
from .builtin import HDLBuiltins


class HDLModuleParameter(HDLObject):
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
        if self.ptype is not None:
            ret_str = '#{} {}'.format(self.ptype.upper(),
                                      self.name.upper())
        else:
            ret_str = '#{}'.format(self.name.upper())
        if self.value is not None:
            ret_str += ' ({})'.format(self.value)

        return ret_str

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()


class HDLModulePort(HDLObject):
    """HDL Module port."""

    _port_directions = ['in', 'out', 'inout']

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
                            ' vector.HDLVectorDescriptor')

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        return '{} {}{}'.format(self.direction.upper(),
                                self.name,
                                self.vector.dumps(eval_scope))

    def dumps(self, eval_scope=None):
        """Alias for __repr__."""
        return self.__repr__(eval_scope)


class HDLModule(HDLObject):
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

    def get_parameter_scope(self):
        """Get parameters as dictionary."""
        scope = {}
        for param in self.params:
            scope[param.name] = param.value

        return scope

    def get_full_scope(self):
        """Get scope, including builtins."""
        scope = {}
        scope.update(self.get_parameter_scope())
        scope.update(HDLBuiltins.get_builtin_scope())
        return scope

    def __repr__(self, evaluate=False):
        """Get readable representation."""
        if evaluate is True:
            eval_scope = self.get_full_scope()
        else:
            eval_scope = None
        ret_str = '{} {{\n'.format(self.name.upper())

        for param in self.params:
            ret_str += '{}\n'.format(param.dumps())

        for port in self.ports:
            ret_str += '    {}\n'.format(port.dumps(eval_scope=eval_scope))

        ret_str += '}'
        return ret_str

    def dumps(self, evaluate=False):
        """Alias for __repr__."""
        return self.__repr__(evaluate)

    def get_param_names(self):
        """Return list of all parameters available."""
        return [x.name for x in self.params]

    def get_port_names(self):
        """Return list of all ports available."""
        return [x.name for x in self.ports]
