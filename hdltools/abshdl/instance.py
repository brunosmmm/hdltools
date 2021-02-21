"""Instances of other modules."""

from hdltools.abshdl import HDLObject
import hdltools.abshdl.module
from hdltools.abshdl.stmt import HDLStatement
from hdltools.abshdl.interface import HDLModuleInterface, HDLInterfaceDeferred


class HDLInstance(HDLObject):
    """Instances."""

    def __init__(self, instance_name, instance_type):
        """Initialize."""
        if not isinstance(instance_type, hdltools.abshdl.module.HDLModule):
            raise TypeError(
                "argument instanc_type must be HDLModule or subclass type"
            )

        self._name = instance_name
        self._type = instance_type
        self._params = {}
        self._ports = {}

    @property
    def name(self):
        """Get name."""
        return self._name

    @property
    def itype(self):
        """Get type."""
        return self._type

    def attach_parameter_value(self, param_name, param_value):
        """Attach a value to a parameter."""
        inst_params = self._type.get_parameter_scope()
        if param_name not in inst_params:
            raise KeyError(
                "parameter '{}' not found in module '{}'".format(
                    param_name, self._type.name
                )
            )

        self._params[param_name] = param_value

    def connect_port(self, port_name, signal_name):
        """Connect instance port."""
        inst_ports = self._type.get_port_scope()
        if port_name not in inst_ports:
            raise KeyError(
                "port '{}' not found in module '{}'".format(
                    port_name, self._type.name
                )
            )
        inst_port = inst_ports[port_name]
        if isinstance(inst_port, HDLModuleInterface):
            raise NotImplementedError
        elif isinstance(inst_port, HDLInterfaceDeferred):
            # in this case, port_name is the interface signal prefix name
            interface = inst_port.instantiate(**self._params)
            for port in interface:
                if port.name.startswith(port_name):
                    if_signal_name = port.name[len(port_name) :]
                else:
                    raise RuntimeError("cannot connect interface")
                self._ports[port.name] = signal_name + if_signal_name
        else:
            self._ports[port_name] = signal_name

    @property
    def params(self):
        """Get params."""
        return self._params

    @property
    def ports(self):
        """Get ports."""
        return self._ports


class HDLInstanceStatement(HDLStatement):
    """Instance statement."""

    def __init__(self, inst, **kwargs):
        """Initialize."""
        super().__init__("par", **kwargs)
        if not isinstance(inst, HDLInstance):
            raise TypeError("inst must be HDLInstance")

        self._inst = inst

    def is_legal(self):
        """Determine legality."""
        return True

    @property
    def instance(self):
        """Get instance."""
        return self._inst
