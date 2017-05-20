from hdltools.verilog.codegen import VerilogCodeGenerator
from hdltools.template import HDLTemplateParser
from hdltools.mmap import MemoryMappedInterface
import os

def test_vec():

    print(VerilogCodeGenerator.dumps_vector(1, 32, 'h'))
    print(VerilogCodeGenerator.dumps_vector(1, 32, 'd'))
    print(VerilogCodeGenerator.dumps_vector(1, 32, 'b'))

    try:
        vec = VerilogCodeGenerator.dumps_vector(256, 8, 'b')
        raise
    except ValueError:
        pass

    try:
        vec = VerilogCodeGenerator.dumps_vector(256, 8, 'x')
        raise
    except ValueError:
        pass

def test_define():

    print(VerilogCodeGenerator.dumps_define('NAME', 'VALUE'))

def test_template():

    template_file = os.path.join('assets', 'verilog', 'axi_slave.v')
    parser = HDLTemplateParser()
    parser.parse_file(template_file)
    parser.insert_contents(list(parser.locations.keys())[0],
                           'line1\nline2\nline3')

    try:
        parser.dump_templated('test.v')
        raise
    except ValueError:
        pass

def test_mmap():

    TEST_STR = """
    #register_size 32;
    //registers
    register control;
    register status;

    //register fields
    field control.IRQEN 0 RW description="Enable Interrupts";
    field control.STOP_ON_ERROR 1 RW description="Stop on Error";
    field status.IRQCLR 7 RW description="Interrupt flag; write 1 to clear";
    field position=2..1 source=status.TEST access=R;
    //field unknown.UNKNOWN 0;
    //field position=2 source=status.Conflict access=R;

    //outputs from register bits
    output IRQ_EN source=control.IRQEN;
    output STOP_ON_ERR source=control.STOP_ON_ERROR;
    //output UNKNOWN source=unknown.UNKNOWN;
    """

    mmap = MemoryMappedInterface()
    mmap.parse_str(TEST_STR)
