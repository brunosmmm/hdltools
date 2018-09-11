"""Build structural modules manually."""

from hdltools.abshdl.module import HDLModule, HDLModuleTypedPort
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.expr import HDLExpression
from hdltools.specc.codegen import SpecCCodeGenerator


if __name__ == "__main__":

    # create ports
    mod_ports = [HDLModuleTypedPort('in', 'operandA', 'int'),
                 HDLModuleTypedPort('in', 'operandB', 'int'),
                 HDLModuleTypedPort('out', 'result', 'int')]
    test_mod = HDLModule('test', mod_ports)
    test_mod.add(HDLSignal('var', 'test'))
    # test_mod.add(HDLAssignment(-mod_ports[2],
    #                           HDLExpression('operandA')*HDLExpression('operandB')))

    gen = SpecCCodeGenerator(indent=True)
    print(gen.dump_element(test_mod))
