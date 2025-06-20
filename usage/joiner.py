"""Generate sequential joiner."""

from hdltools.abshdl.module import HDLModule, input_port, output_port
from hdltools.hdllib.patterns import (
    ParallelBlock,
    ClockedBlock,
    get_multiplexer,
)
from hdltools.abshdl.highlvl import HDLBlock
from hdltools.abshdl.signal import HDLSignal
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator
from hdltools.abshdl.generator import HDLEntityGenerator
from hdltools.util import clog2

DEFAULT_PORT_SIZE = 32


class JoinerGenerator(HDLEntityGenerator):
    """Joiner generator."""

    REQUIRED_PARAMETERS = {"inputNum": ("number of inputs", int, 8)}
    OPTIONAL_PARAMETERS = {"mangled_name": ("mangled name", str)}

    @classmethod
    def _generate_entity(cls, mod_params, backend_name=None):
        """Generate entity."""
        input_count = mod_params["inputNum"]
        mangled_name = mod_params.get("mangled_name", f"joiner__{input_count}")
        input_ports = [input_port("clk"), input_port("rst")]
        data_input_ports = [
            input_port(f"jinput{x}", size=DEFAULT_PORT_SIZE)
            for x in range(0, input_count)
        ]
        data_output_port = output_port("joutput", size=DEFAULT_PORT_SIZE)
        output_ports = [data_output_port]

        selector_signal = HDLSignal("reg", "selector", size=clog2(input_count))

        @HDLModule(
            mangled_name, ports=input_ports + data_input_ports + output_ports
        )
        def gen_module(mod):
            """Generate the module."""
            # add selector signal
            mod.add(selector_signal)

            # clocked block for counter
            @HDLBlock(mod)
            @ParallelBlock()
            def module_body(input_count):
                """Generate the actual implementation."""

                @ClockedBlock(clk)
                def join_seq():
                    if rst == 1:
                        selector = 0
                    else:
                        # FIXME(hdltools): selector += 1 does not produce code
                        if selector < input_count - 1:
                            selector = selector + 1
                        else:
                            selector = 0

            # input multiplexer
            mod.add(
                get_multiplexer(
                    data_output_port, selector_signal, *data_input_ports
                )
            )
            mod.extend(*module_body(input_count=input_count))

        return gen_module()


if __name__ == "__main__":
    # test
    joiner = JoinerGenerator.parse_and_generate()
    verilog_gen = VerilogCodeGenerator(indent=True)
    vhdl_gen = VHDLCodeGenerator()
    
    print("=" * 60)
    print("*Joiner Verilog Code*")
    print("=" * 60)
    print(verilog_gen.dump_element(joiner))
    print()
    print("=" * 60)
    print("*Joiner VHDL Code*")
    print("=" * 60)
    print(vhdl_gen.dump_element(joiner))
