"""Interfaces."""

from hdltools.abshdl import HDLObject
from hdltools.abshdl.port import HDLModulePort
from typing import Dict, Union, Tuple
import re
import copy


EXPRESSION_REGEX = re.compile(r"[\+\-\*\/\(\)]+")


class HDLModuleInterfaceError(Exception):
    """Interface description error."""


class HDLModuleInterface(HDLObject):
    """Module interface."""

    _PORTS: Dict[str, Dict[str, Union[str, int]]] = {}
    _ALIASES: Dict[str, Tuple[str]] = {}

    def __init__(self):
        """Initialize."""
        super().__init__()

        # create ports
        if self._PORTS is None or not self._PORTS:
            raise HDLModuleInterfaceError(
                "interface must have at least 1 port"
            )

    @classmethod
    def find_alias(cls, name):
        """Find alias."""
        for used_name, aliases in cls._ALIASES.items():
            for alias_name in aliases:
                if alias_name == name:
                    return used_name
        return None

    @classmethod
    def parameterize(cls, **kwargs):
        """Parameterize interface ports."""
        ports = []
        for port_name, port_desc in cls._PORTS.items():
            port_optional = port_desc.get("optional", False)
            if "dir" not in port_desc or "size" not in port_desc:
                raise HDLModuleInterfaceError("malformed port description")
            size = port_desc["size"]
            if not isinstance(size, (int, str)):
                raise HDLModuleInterfaceError(
                    "port size must be integer or expression"
                )

            if isinstance(size, str):
                # determine if is simple name or expression
                m = EXPRESSION_REGEX.findall(size)
                if m:
                    # is expression
                    names = re.findall(r"[_a-zA-Z]\w*", size)
                    for name in names:
                        original_name = name
                        if name not in kwargs:
                            name = cls.find_alias(name)
                        if name not in kwargs and port_optional is False:
                            raise HDLModuleInterfaceError(
                                f"in expression '{size}': unknown name '{name}'"
                            )
                        if port_optional:
                            # ignore port
                            continue
                        size = size.replace(original_name, str(kwargs[name]))
                    # force integer division
                    size = size.replace("/", "//")
                    try:
                        size = eval(size)
                    except SyntaxError:
                        raise HDLModuleInterfaceError(
                            f"invalid expression: '{size}'"
                        )
                else:
                    # is name
                    if size not in kwargs:
                        _size = cls.find_alias(size)
                        if _size is not None:
                            size = _size
                    if size not in kwargs and port_optional is False:
                        raise HDLModuleInterfaceError(f"unknown name: {size}")
                    if port_optional:
                        # not specified, so ignore
                        continue
                    if not isinstance(kwargs[size], int):
                        raise HDLModuleInterfaceError(
                            "port sizes must be integer values"
                        )
                    size = kwargs[size]
            else:
                enable_port = kwargs.get(f"enable{port_name}", False)
                if port_optional and bool(enable_port) is False:
                    # ignore optional port
                    continue
            if size == 0:
                # ignore port
                continue
            if size < 0:
                raise HDLModuleInterfaceError(f"invalid port size: {size}")
            if port_desc["dir"] == "input":
                direction = "in"
            elif port_desc["dir"] == "output":
                direction = "out"
            elif port_desc["dir"] == "inout":
                direction = "inout"
            else:
                raise HDLModuleInterfaceError(
                    "port direction must be input, output or inout"
                )
            ports.append(HDLModulePort(direction, port_name, size))
        return HDLParameterizedInterface(*ports)

    @classmethod
    def instantiate(cls, name, decorate=None, **kwargs):
        """Instantiate."""
        if decorate is not None:

            @decorate
            def decorated_parameterize(**kwargs):
                return cls.parameterize(**kwargs)

            return decorated_parameterize.instantiate(name)

        interface = cls.parameterize(**kwargs)
        return interface.instantiate(name)

    @classmethod
    def get_flipped(cls):
        """Get interface with flipped port directions."""
        flipped_ports = {}
        for name, config in cls._PORTS.items():
            port_flips = config.get("flips", True)
            if port_flips is True:
                if config["dir"] == "output":
                    flipped_dir = "input"
                elif config["dir"] == "input":
                    flipped_dir = "output"
                else:
                    flipped_dir = config["dir"]
            else:
                flipped_dir = config["dir"]
            _config = config.copy()
            _config["dir"] = flipped_dir
            flipped_ports[name] = _config

        return flipped_ports


class HDLParameterizedInterface(HDLObject):
    """Parameterized interface."""

    def __init__(self, *ports):
        """Initialize."""
        super().__init__()
        for port in ports:
            if not isinstance(port, HDLModulePort):
                raise HDLModuleInterfaceError(
                    "ports must be of HDLModulePort type"
                )

        self._ports = ports

    @property
    def ports(self):
        """Get ports."""
        return self._ports

    def instantiate(self, name):
        """Instantiate."""
        inst_ports = copy.copy(self._ports)
        for port in inst_ports:
            port.rename(name + port.name)

        return inst_ports


class HDLInterfaceDeferred(HDLObject):
    """Deferred instantiation of an interface."""

    def __init__(self, inst_name, if_type):
        """Initialize."""
        super().__init__()
        if not issubclass(if_type, HDLModuleInterface):
            raise TypeError("must be a subclass of HDLModuleInterface")
        self._name = inst_name
        self._iftype = if_type

    @property
    def name(self):
        """Get name."""
        return self._name

    def instantiate(self, **kwargs):
        """Instantiate."""
        return self._iftype.instantiate(self.name, **kwargs)
