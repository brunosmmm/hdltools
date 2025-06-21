"""Build structural modules manually."""

from hdltools.abshdl.module import HDLModule, HDLModuleTypedPort
from hdltools.abshdl.signal import HDLSignal
from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.vhdl.codegen import VHDLCodeGenerator


if __name__ == "__main__":

    # create ports
    mod_ports = [HDLModuleTypedPort('in', 'operandA', 'int'),
                 HDLModuleTypedPort('in', 'operandB', 'int'),
                 HDLModuleTypedPort('out', 'result', 'int')]
    test_mod = HDLModule('test', mod_ports)
    test_mod.add(HDLSignal('var', 'test'))
    # test_mod.add(HDLAssignment(-mod_ports[2],
    #                           HDLExpression('operandA')*HDLExpression('operandB')))

    verilog_gen = VerilogCodeGenerator(indent=True)
    vhdl_gen = VHDLCodeGenerator()
    
    print("Verilog Code:")
    print(verilog_gen.dump_element(test_mod))
    print()
    print("VHDL Code:")
    print(vhdl_gen.dump_element(test_mod))
