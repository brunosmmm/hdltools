"""AXI interface patterns."""

from hdltools.abshdl.interface import HDLModuleInterface


class AXI4LiteSlaveIf(HDLModuleInterface):
    """AXI4 Lite slave interface."""

    _PORTS = {
        "_aclk": {"dir": "input", "size": 1, "flips": False},
        "_aresetn": {"dir": "input", "size": 1, "flips": False},
        "_awvalid": {"dir": "input", "size": 1},
        "_awaddr": {"dir": "input", "size": "addr_width"},
        "_awready": {"dir": "output", "size": 1},
        "_wvalid": {"dir": "input", "size": 1},
        "_wdata": {"dir": "input", "size": "data_width"},
        "_wstrb": {"dir": "input", "size": "data_width / 8"},
        "_wready": {"dir": "output", "size": 1},
        "_bvalid": {"dir": "output", "size": 1},
        "_bresp": {"dir": "output", "size": 2},
        "_bready": {"dir": "input", "size": 1},
        "_arvalid": {"dir": "input", "size": 1},
        "_araddr": {"dir": "input", "size": "addr_width"},
        "_arready": {"dir": "output", "size": 1},
        "_rvalid": {"dir": "output", "size": 1},
        "_rdata": {"dir": "output", "size": "data_width"},
        "_rresp": {"dir": "output", "size": 2},
        "_rready": {"dir": "input", "size": 1},
        "_awprot": {"dir": "input", "size": 3},
        "_arprot": {"dir": "input", "size": 3},
    }


class AXI4LiteMasterIf(HDLModuleInterface):
    """AXI4 Lite master interface."""

    _PORTS = AXI4LiteSlaveIf.get_flipped()
