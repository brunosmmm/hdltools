"""AXI Memory Mapped Slave Model."""

from ..abshdl.module import HDLModule, HDLModuleParameter, HDLModulePort
from ..abshdl.expr import HDLExpression
from ..abshdl.signal import HDLSignal
from ..abshdl.comment import HDLComment, make_comment
from ..abshdl.assign import HDLAssignment
from ..abshdl.ifelse import HDLIfElse
from ..abshdl.switch import HDLSwitch, HDLCase
from ..abshdl.loop import HDLForLoop
from .patterns import (get_clock_rst_block, get_any_sequential_block,
                       get_reset_if_else)
import math


def get_register_write_logic(loop_variable, data_width, axi_wstrb,
                             register, axi_wdata):
    """Get logic for writing with byte strobes."""
    initial = loop_variable.assign(0)
    expr = loop_variable <= int(data_width / 8) - 1
    after = loop_variable.assign(loop_variable + 1)
    loop = HDLForLoop(initial, expr, after)

    data = axi_wdata.part_select(loop_variable*8, 8)
    assign = register.part_select(loop_variable*8, 8).assign(data)
    loop.add_to_scope(HDLIfElse(axi_wstrb[loop_variable] == 1,
                                if_scope=assign))

    return loop


def get_axi_mm_slave(mod_name, data_width, register_count):
    """Get AXI Slave Model."""
    # module object
    mod = HDLModule(module_name=mod_name)

    # addr lsb bits
    lsb_bits = (HDLExpression('AXI_DATA_WIDTH') / 32) + 1

    # caculate minimum address width: resolve immediately, do not depend
    # on parameters (could also evaluate lsb_bits with AXI_DATA_WIDTH=32)
    eval_lsb = lsb_bits.evaluate(AXI_DATA_WIDTH=data_width)
    addr_bits = int(math.ceil(math.log2(register_count)))+int(eval_lsb)

    # create standard parameters
    param_list = [HDLModuleParameter('AXI_DATA_WIDTH', 'integer', data_width),
                  HDLModuleParameter('AXI_ADDR_WIDTH', 'integer', addr_bits)]

    # create standard ports
    port_list = [HDLModulePort('in', 'S_AXI_ACLK'),
                 HDLModulePort('in', 'S_AXI_ARESETN'),
                 HDLModulePort('in', 'S_AXI_AWADDR',
                               size=HDLExpression('AXI_ADDR_WIDTH')),
                 HDLModulePort('in', 'S_AXI_AWPROT', size=3),
                 HDLModulePort('in', 'S_AXI_AWVALID'),
                 HDLModulePort('out', 'S_AXI_AWREADY'),
                 HDLModulePort('in', 'S_AXI_WDATA',
                               size=HDLExpression('AXI_DATA_WIDTH')),
                 HDLModulePort('in', 'S_AXI_WSTRB',
                               size=HDLExpression('AXI_DATA_WIDTH/8')),
                 HDLModulePort('in', 'S_AXI_WVALID'),
                 HDLModulePort('out', 'S_AXI_WREADY'),
                 HDLModulePort('out', 'S_AXI_BRESP', size=2),
                 HDLModulePort('out', 'S_AXI_BVALID'),
                 HDLModulePort('in', 'S_AXI_BREADY'),
                 HDLModulePort('in', 'S_AXI_ARADDR',
                               size=HDLExpression('AXI_ADDR_WIDTH')),
                 HDLModulePort('in', 'S_AXI_ARPROT', size=3),
                 HDLModulePort('in', 'S_AXI_ARVALID'),
                 HDLModulePort('out', 'S_AXI_ARREADY'),
                 HDLModulePort('out', 'S_AXI_RDATA',
                               size=HDLExpression('AXI_DATA_WIDTH')),
                 HDLModulePort('out', 'S_AXI_RRESP', size=2),
                 HDLModulePort('out', 'S_AXI_RVALID'),
                 HDLModulePort('in', 'S_AXI_RREADY')]

    # add stuff to module
    mod.add_parameters(param_list)
    mod.add_ports(port_list)

    # create some signals
    def body_1():
        yield HDLSignal('reg', 'axi_awaddr',
                        size=HDLExpression('AXI_ADDR_WIDTH'))
        yield HDLSignal('reg', 'axi_awready')
        yield HDLSignal('reg', 'axi_wready')
        yield HDLSignal('reg', 'axi_bresp', size=2)
        yield HDLSignal('reg', 'axi_bvalid')
        yield HDLSignal('reg', 'axi_araddr',
                        size=HDLExpression('AXI_ADDR_WIDTH'))
        yield HDLSignal('reg', 'axi_arready')
        yield HDLSignal('reg', 'axi_rdata',
                        size=HDLExpression('AXI_DATA_WIDTH'))
        yield HDLSignal('reg', 'axi_rresp',
                        size=2)
        yield HDLSignal('reg', 'axi_rvalid')
        yield HDLSignal('const', 'ADDR_LSB', size=None,
                        default_val=HDLExpression('AXI_DATA_WIDTH/32+1'))
        yield HDLSignal('const', 'OPT_MEM_ADDR_BITS', size=None,
                        default_val=3)
        yield HDLComment('Register Space', tag='REG_DECL')
        yield HDLSignal('comb', 'slv_reg_rden')
        yield HDLSignal('comb', 'slv_reg_wren')
        yield HDLSignal('reg', 'reg_data_out',
                        size=HDLExpression('AXI_DATA_WIDTH'))
        yield HDLSignal('var', 'byte_index',
                        size=None)
        yield 'I/O Connection assignments'
        yield HDLAssignment(mod.get_port('S_AXI_AWREADY'),
                            mod.get_signal('axi_awready'))
        yield HDLAssignment(mod.get_port('S_AXI_WREADY'),
                            mod.get_signal('axi_wready'))
        yield HDLAssignment(mod.get_port('S_AXI_BRESP'),
                            mod.get_signal('axi_bresp'))
        yield HDLAssignment(mod.get_port('S_AXI_BVALID'),
                            mod.get_signal('axi_bvalid'))
        yield HDLAssignment(mod.get_port('S_AXI_ARREADY'),
                            mod.get_signal('axi_arready'))
        yield HDLAssignment(mod.get_port('S_AXI_RDATA'),
                            mod.get_signal('axi_rdata'))
        yield HDLAssignment(mod.get_port('S_AXI_RRESP'),
                            mod.get_signal('axi_rresp'))
        yield HDLAssignment(mod.get_port('S_AXI_RVALID'),
                            mod.get_signal('axi_rvalid'))
        yield HDLComment('User logic', tag='USER_LOGIC')

    # add declarations
    mod.add(body_1())

    # access signals in python scope
    clk = mod.get_port('S_AXI_ACLK')
    rst = mod.get_port('S_AXI_ARESETN')
    axi_awready = mod.get_signal('axi_awready')
    axi_wready = mod.get_signal('axi_wready')
    axi_awaddr = mod.get_signal('axi_awaddr')
    slv_reg_wren = mod.get_signal('slv_reg_wren')
    axi_bvalid = mod.get_signal('axi_bvalid')
    AWVALID = mod.get_port('S_AXI_AWVALID')
    WVALID = mod.get_port('S_AXI_WVALID')
    AWADDR = mod.get_port('S_AXI_AWADDR')
    ADDR_LSB = mod.get_signal('ADDR_LSB')
    OPT_MEM_ADDR_BITS = mod.get_signal('OPT_MEM_ADDR_BITS')

    sig = mod.get_signal_scope()

    # inner if-else
    innerifelse = HDLIfElse(
        (~axi_awready).bool_and(+AWVALID).bool_and(+WVALID),
        if_scope=axi_awready.assign(1),
        else_scope=axi_awready.assign(0))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=axi_awready.assign(0),
                              stmts=innerifelse,
                              tag='awready_gen')

    mod.add([seq])

    # awaddr latching
    innerifelse = HDLIfElse(
        (~axi_awready).bool_and(+AWVALID).bool_and(+WVALID),
        if_scope=axi_awaddr.assign(-AWADDR))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=axi_awaddr.assign(0),
                              stmts=innerifelse,
                              tag='awadr_latch')

    mod.add([seq])

    # wready generation
    innerifelse = HDLIfElse(
        (~axi_awready).bool_and(+AWVALID).bool_and(+WVALID),
        if_scope=axi_wready.assign(1),
        else_scope=axi_wready.assign(0))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=axi_wready.assign(0),
                              stmts=innerifelse,
                              tag='wready_gen')

    mod.add([seq])

    # slave write enable
    mod.add(['generate slave write enable',
             slv_reg_wren.assign((~axi_wready)
                                 .bool_and(+WVALID)
                                 .bool_and(+axi_awready)
                                 .bool_and(+AWVALID))])

    switch = HDLSwitch(axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB],
                       tag='reg_write_case')
    def_case = HDLCase('default')
    switch.add_case(def_case)
    innerif = HDLIfElse(slv_reg_wren,
                        if_scope=switch)
    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=make_comment('Reset Registers',
                                                     tag='REG_RESET'),
                              stmts=innerif,
                              tag='reg_write')

    mod.add([seq])

    # write response logic
    innerifelse = HDLIfElse((~axi_awready)
                            .bool_and(+AWVALID)
                            .bool_and(~axi_bvalid)
                            .bool_and(axi_wready)
                            .bool_and(+WVALID),
                            if_scope=(axi_bvalid.assign(1),
                                      sig['axi_bresp'].assign(0)),
                            else_scope=HDLIfElse(
                                sig['S_AXI_BREADY']
                                .bool_and(axi_bvalid),
                                if_scope=axi_bvalid.assign(0)))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=(sig['axi_bvalid'].assign(0),
                                         sig['axi_bresp'].assign(0)),
                              stmts=innerifelse,
                              tag='wr_resp_logic')

    mod.add(['Write response logic', seq])

    # arready generation
    innerifelse = HDLIfElse((~sig['axi_arready'])
                            .bool_and(sig['S_AXI_ARVALID']),
                            if_scope=(sig['axi_arready'].assign(1),
                                      sig['axi_araddr']
                                      .assign(sig['S_AXI_ARADDR'])),
                            else_scope=sig['axi_arready'].assign(0))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=(sig['axi_arready'].assign(0),
                                         sig['axi_araddr'].assign(0)),
                              stmts=innerifelse,
                              tag='arready_gen')

    mod.add(['axi_arready generation', seq])

    # arvalid generation
    innerifelse = HDLIfElse(sig['axi_arready']
                            .bool_and(sig['S_AXI_ARVALID'])
                            .bool_and(~sig['axi_rvalid']),
                            if_scope=(sig['axi_rvalid'].assign(1),
                                      sig['axi_rresp'].assign(0)),
                            else_scope=HDLIfElse(
                                sig['axi_rvalid']
                                .bool_and(sig['S_AXI_RREADY']),
                                if_scope=sig['axi_rvalid']
                                .assign(0)))

    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=(sig['axi_rvalid'].assign(0),
                                         sig['axi_rresp'].assign(0)),
                              stmts=innerifelse,
                              tag='arvalid_gen')

    mod.add(['arvalid generation', seq])

    # register selection
    mod.add(['Register select and read logic',
             sig['slv_reg_rden'].assign(sig['axi_arready'] &
                                        sig['S_AXI_ARVALID'] &
                                        ~sig['axi_rvalid'])])

    innercase = HDLSwitch(sig['axi_araddr']
                          [ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB],
                          tag='reg_read_switch')
    def_case = HDLCase('default',
                       stmts=[sig['reg_data_out'].assign(0)])
    innercase.add_case(def_case)
    seq = get_any_sequential_block(get_reset_if_else(-rst,
                                                     0,
                                                     sig['reg_data_out']
                                                     .assign(0),
                                                     innercase,
                                                     tag='reg_select'))

    mod.add([seq])

    # data output
    innerif = HDLIfElse(sig['slv_reg_rden'],
                        if_scope=sig['axi_rdata'].assign(sig['reg_data_out']))
    seq = get_clock_rst_block(-clk,
                              -rst,
                              'rise',
                              0,
                              rst_stmts=sig['axi_rdata'].assign(0),
                              stmts=innerif,
                              tag='data_out')

    mod.add(['data output', seq])

    # user logic assignments
    mod.add([HDLComment('Output assignment', tag='OUTPUT_ASSIGN')])

    return mod
