"""Interfaces."""

from hdltools.abshdl import HDLObject
from hdltools.abshdl.port import HDLModulePort
from typing import Dict, Union
import re


EXPRESSION_REGEX = re.compile(r"[\+\-\*\/\(\)]+")


class HDLModuleInterfaceError(Exception):
    """Interface description error."""


class HDLModuleInterface(HDLObject):
    """Module interface."""

    _PORTS: Dict[str, Dict[str, Union[str, int]]] = {}

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__()

        # create ports
        if self._PORTS is None or not self._PORTS:
            raise HDLModuleInterfaceError(
                "interface must have at least 1 port"
            )

        self._ports = []
        for port_name, port_desc in self._PORTS.items():
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
                    names = re.findall(r"[_a-zA-Z]\w+", size)
                    for name in names:
                        if name not in kwargs:
                            raise HDLModuleInterfaceError(
                                f"in expression '{size}': unknown name '{name}'"
                            )
                        size = size.replace(name, str(kwargs[name]))
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
                        raise HDLModuleInterfaceError(f"unknown name: {size}")
                    if not isinstance(kwargs[size], int):
                        raise HDLModuleInterfaceError(
                            "port sizes must be integer values"
                        )
                    else:
                        size = kwargs[size]
            if size == 0:
                # ignore port
                continue
            elif size < 0:
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
            self._ports.append(HDLModulePort(direction, port_name, size))

    @property
    def ports(self):
        """Get ports."""
        return self._ports
