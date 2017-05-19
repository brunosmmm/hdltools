from hdltools.verilog_gen import dumps_vector, dumps_define
from hdltools.template import HDLTemplateParser
import os

def test_vec():

    print(dumps_vector(1, 32, 'h'))
    print(dumps_vector(1, 32, 'd'))
    print(dumps_vector(1, 32, 'b'))

    try:
        vec = dumps_vector(256, 8, 'b')
        raise
    except ValueError:
        pass

    try:
        vec = dumps_vector(256, 8, 'x')
        raise
    except ValueError:
        pass

def test_define():

    print(dumps_define('NAME', 'VALUE'))

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
