"""AXI skeleton modules."""

from hdltools.abshdl.module import HDLModule, HDLModuleParameter
from hdltools.abshdl.instance import HDLInstance
from hdltools.abshdl.interface import HDLInterfaceDeferred
from hdltools.hdllib.axi.interfaces import AXI4LiteSlaveIf


class AXI4LiteSlaveMod(HDLModule):
    """AXI4 Lite slave module skeleton."""

    def __init__(self, extra_ports=None):
        """Initialize."""
        module_params = [
            HDLModuleParameter("C_S_AXI_DATA_WIDTH", "integer", 32),
            HDLModuleParameter("C_S_AXI_ADDR_WIDTH", "integer", 16),
        ]
        module_ports = [HDLInterfaceDeferred("s_axi", AXI4LiteSlaveIf)]
        if extra_ports is not None:
            if not isinstance(extra_ports, (tuple, list)):
                raise TypeError("extra_ports must be a tuple-like object")
            module_ports.extend(extra_ports)
        super().__init__("axi4liteslave", module_ports, module_params)


class AXI4LiteSlave(HDLInstance):
    """AXI4 Lite slave instance."""

    def __init__(self, inst_name, extra_ports=None):
        """Initialize."""
        super().__init__(inst_name, AXI4LiteSlaveMod(extra_ports))
