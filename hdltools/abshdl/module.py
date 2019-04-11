"""HDL Module."""

from . import HDLObject
from .builtin import HDLBuiltins
from .scope import HDLScope
from .signal import HDLSignal
from .macro import HDLMacro
from .seq import HDLSequentialBlock
from .port import HDLModulePort, HDLModuleTypedPort


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
            ret_str = "#{} {}".format(self.ptype.upper(), self.name.upper())
        else:
            ret_str = "#{}".format(self.name.upper())
        if self.value is not None:
            ret_str += " ({})".format(self.value)

        return ret_str

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()


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
        self.constants = []
        if params is not None:
            self.add_parameters(params)
        if ports is not None:
            self.add_ports(ports)
        self.scope = HDLScope(scope_type="par", parent=self)

    def __call__(self, fn):
        """Use as decorator."""

        def wrapper_HDLModule(*args):
            mod = self
            fn(mod, *args)
            return mod

        return wrapper_HDLModule

    def add(self, items):
        """Add to scope."""
        self.scope.add(items)

    def extend(self, scope, const=None):
        """Extend scope."""
        self.scope.extend(scope)
        if const is not None:
            self.add_constants(const)

    def insert_before(self, tag, items):
        """Insert element before tag."""
        self.scope.insert_before(tag, *items)

    def insert_after(self, tag, items):
        """Insert element after tag."""
        self.scope.insert_after(tag, *items)

    def find_by_tag(self, tag):
        """Find element by tag."""
        return self.scope.find_by_tag(tag)

    def add_ports(self, ports):
        """Add ports to module.

        Args
        ----
        ports: list or HDLModulePort
            List of ports to be added
        """
        # TODO: duplicate port verification
        typed_ports_added = False
        untyped_ports_added = False
        if not isinstance(ports, (tuple, list)):
            ports = [ports]
        for port in ports:
            if isinstance(port, HDLModuleTypedPort):
                if untyped_ports_added:
                    raise TypeError("cannot mix typed and untyped ports")
                self.ports.append(port)
                typed_ports_added = True
            elif isinstance(port, HDLModulePort):
                if typed_ports_added:
                    raise TypeError("cannot mix typed and untyped ports")
                self.ports.append(port)
                untyped_ports_added = True
            else:
                raise TypeError(
                    "list may only contain HDLModulePort" " instances"
                )

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
                    raise TypeError(
                        "list may only contain HDLModuleParameter" " instances"
                    )
            self.params.extend(params)
        else:
            raise TypeError("params must be a list or HDLModuleParameter")

    def add_constants(self, constants):
        """Add constant declarations (macros)."""
        if isinstance(constants, HDLMacro):
            self.constants.append(constants)
        elif isinstance(constants, (list, tuple)):
            for constant in constants:
                if not isinstance(constant, HDLMacro):
                    raise TypeError("list may only contain HDLMacro instances")

                self.constants.append(constant)
        else:
            raise TypeError("constants must be a list or HDLMacro")

    def get_parameter_scope(self):
        """Get parameters as dictionary."""
        scope = {}
        for param in self.params:
            scope[param.name] = param.value

        return scope

    def get_port_scope(self):
        """Get ports as dict."""
        scope = {}
        for port in self.ports:
            scope[port.name] = port

        return scope

    def get_signal_scope(self):
        """Get signals as dict (includes ports)."""
        scope = {}
        port_scope = self.get_port_scope()
        # access port signals and add to scope
        for name, port in port_scope.items():
            scope[name] = -port

        for item in self.scope:
            if isinstance(item, HDLSignal):
                scope[item.name] = item

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
        ret_str = "{} {{\n".format(self.name.upper())

        for constant in self.constants:
            ret_str += "{}\n".format(constant.dumps())

        for param in self.params:
            ret_str += "{}\n".format(param.dumps())

        for port in self.ports:
            ret_str += "    {}\n".format(port.dumps(eval_scope=eval_scope))

        ret_str += "}"

        # TODO dump scope

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

    def get_port(self, name):
        """Get port object."""
        for port in self.ports:
            if port.name == name:
                return port

        return None

    def get_signal(self, name):
        """Get signal."""
        for element in self.scope:
            if isinstance(element, HDLSignal):
                if element.name == name:
                    return element

        return None


def input_port(name, size=1):
    """Make an input port."""
    return HDLModulePort("in", name, size)


def output_port(name, size=1):
    """Make an output port."""
    return HDLModulePort("out", name, size)


def inout_port(name, size=1):
    """Make an input port."""
    return HDLModulePort("inout", name, size)
