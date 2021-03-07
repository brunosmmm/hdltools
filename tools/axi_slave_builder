#!/usr/bin/env python3

"""Build AXI MM Slaves from specification files."""
import argparse
import os
import sys

from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.concat import HDLConcatenation
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.ifelse import HDLIfElse
from hdltools.abshdl.macro import HDLMacro
from hdltools.abshdl.signal import HDLSignal
from hdltools.abshdl.switch import HDLCase
from hdltools.hdllib.aximm import get_axi_mm_slave, get_register_write_logic
from hdltools.logging import DEFAULT_LOGGER
from hdltools.mmap import parse_mmap_file
from hdltools.mmap.builder import MMBuilder
from hdltools.verilog.codegen import VerilogCodeGenerator

DEFAULT_TEMPLATE = os.path.join("assets", "verilog", "axi_slave.v")

if __name__ == "__main__":

    # argument parser
    arg_parser = argparse.ArgumentParser(
        description="Build AXI MM" " Slaves from high-level description"
    )

    arg_parser.add_argument("model", help="Model file")
    arg_parser.add_argument("--template", help="Template file", action="store")
    arg_parser.add_argument(
        "--modname", help="Module name", default="aximm_slave", action="store"
    )
    arg_parser.add_argument("-v", help="verbose", action="store_true")
    arg_parser.add_argument(
        "--replace-param", help="replace parameter value", nargs="+"
    )
    arg_parser.add_argument("-o", help="output to file")

    args = arg_parser.parse_args()

    param_replacements = {}
    if args.replace_param is not None:
        for replacement in args.replace_param:
            try:
                param, value = replacement.split("=")
                value = int(value)
            except (IndexError, ValueError):
                print(f"FATAL: malformed parameter replacement: {replacement}")
            param_replacements[param] = value

    DEFAULT_LOGGER.set_dest(sys.stderr)
    if args.v:
        DEFAULT_LOGGER.set_level("debug")

    # parse file
    text, mmap_model = parse_mmap_file(args.model)
    mmbuilder = MMBuilder(text)
    mmap = mmbuilder.visit(mmap_model, param_replace=param_replacements)

    sys.stderr.write(mmap.dumps())

    # code generator
    vlog = VerilogCodeGenerator(indent=True)
    vlog.add_class_alias("HDLModulePort", "FlagPort")

    slave = get_axi_mm_slave(args.modname, mmap.reg_size, len(mmap.registers))

    # parameters (naive implementation)
    for name, value in mmap.parameters.items():
        slave.add_parameters(value)

    # bit field declarations
    for name, reg in mmap.registers.items():
        for field in reg.fields:
            def_name = "{}_{}_INDEX".format(name, field.name)
            def_value = field.get_range()[0]
            macro = HDLMacro(def_name, def_value)
            slave.add_constants(macro)

    for name, port in mmap.ports.items():
        slave.add_ports(port)

    for name, reg in mmap.registers.items():
        signal = HDLSignal("reg", "REG_" + name, reg.size)
        # TODO: fixme: allow only to insert list, because
        # signal will be iterated and bad things will happen
        # generate write mask parameter
        wrmask = HDLSignal(
            "const",
            "WRMASK_" + name,
            reg.size,
            default_val=HDLExpression(
                reg.get_write_mask(), size=reg.size, radix="h"
            ),
        )
        slave.insert_after("REG_DECL", [signal, wrmask])

    param_buffer_list = []
    for name, reg in mmap.registers.items():
        signal = HDLSignal("reg", "REG_" + name, reg.size)
        value = reg.get_default_value()
        if isinstance(value, (HDLIntegerConstant, int)):
            def_val = HDLIntegerConstant(value, size=reg.size)
        elif isinstance(value, HDLExpression):
            raise TypeError("HDLExpression not implemented at this time")
        elif isinstance(value, HDLConcatenation):
            def_val = value

            concat = HDLConcatenation(None)
            # build parameter buffers
            for field in reg.fields:
                if isinstance(field.default_value, HDLExpression):
                    param_name = field.default_value.dumps()
                    if param_name in mmap.parameters:
                        sig = HDLSignal(
                            "const",
                            "PRM_" + param_name,
                            size=len(field.default_value),
                            default_val=param_name,
                        )
                        slave.insert_before("USER_LOGIC", [sig])
                        new_expr = HDLExpression(
                            "PRM_" + param_name, size=len(field.default_value)
                        )
                        concat.append(new_expr)
                else:
                    concat.append(field.default_value)

            # check if size matches register size
            if len(concat) < reg.size:
                # fill with zeroes on left side.
                fill_size = reg.size - len(concat)
                concat.appendleft(HDLIntegerConstant(0, size=fill_size))
            def_val = concat
        else:
            raise TypeError("Invalid type")

        slave.insert_after("REG_RESET", [signal.assign(def_val)])

    # output assignments
    for name, port in mmap.ports.items():
        if port.direction != "out":
            continue
        # create a proxy signal
        sig = HDLSignal("comb", name, port.vector)
        reg_sig = HDLSignal(
            "reg",
            "REG_" + port.target_register.name,
            port.target_register.size,
        )
        if port.target_field is not None:
            target_field = port.target_register.get_field(port.target_field)
            target_bits = target_field.get_slice()
            assignment = HDLAssignment(sig, reg_sig[target_bits])
        else:
            assignment = HDLAssignment(sig, reg_sig)
        slave.insert_after("OUTPUT_ASSIGN", [assignment])

    # register write
    slave_signals = slave.get_signal_scope()
    slave_parameters = slave.get_parameter_scope()
    data_width = slave_parameters["C_S_AXI_DATA_WIDTH"]
    loop_var = slave_signals["byte_index"]
    axi_wstrb = slave_signals["S_AXI_WSTRB"]
    axi_wdata = slave_signals["S_AXI_WDATA"]
    scope, where = slave.find_by_tag("reg_write_case")
    index, wr_switch = where
    lsb_bits_sig = slave_signals["ADDR_LSB"]
    addr_width = slave_signals["OPT_MEM_ADDR_BITS"].default_val.evaluate()
    lsb_bits = lsb_bits_sig.default_val.evaluate(C_S_AXI_DATA_WIDTH=data_width)
    default_case = wr_switch.get_case("default")
    for name, reg in mmap.registers.items():
        reg_sig = slave_signals["REG_" + name]
        reg_addr = HDLIntegerConstant(
            reg.addr >> int(lsb_bits), size=addr_width, radix="h"
        )
        case = HDLCase(
            reg_addr,
            stmts=[
                get_register_write_logic(
                    loop_var, data_width, axi_wstrb, reg_sig, axi_wdata
                )
            ],
        )
        wr_switch.add_case(case)
        default_case.add_to_scope(reg_sig.assign(reg_sig))

    # add autoclear if present
    wr_if = wr_switch.get_parent().get_parent().get_parent()
    for name, reg in mmap.registers.items():
        for field in reg.fields:
            if "autoclear" in field.properties:
                if field.properties["autoclear"] == "true":
                    # insert auto clearing flag behavior
                    field_sig = slave_signals["REG_" + name]
                    clr_if = HDLIfElse(
                        field_sig[field.get_slice()],
                        if_scope=(field_sig[field.get_slice()]).assign(0),
                    )
                    wr_if.add(clr_if)

    # to generate register read, we must consider several aspects.
    # If a register field has both a flag input and an output pointing
    # to it, then the read will actually output the value from the
    # input signal and not from the register. This will also happen if
    # the field is read only. If a field is write only, then the read
    # always gets the default value.
    reg_data_out = slave_signals["reg_data_out"]
    where, (_, reg_select) = slave.find_by_tag("reg_read_switch")
    for name, reg in mmap.registers.items():
        # register signal
        reg_sig = slave_signals["REG_" + name]
        reg_addr = HDLIntegerConstant(
            reg.addr >> int(lsb_bits), size=addr_width, radix="h"
        )
        reg_fields = sorted(reg.fields, key=lambda x: min(x.get_range()))
        if not reg_fields:
            # no fields declared, so read entire register, respecting mask if available
            rmask = reg.properties.get("rmask")
            if rmask is None:
                reg_read = HDLExpression(reg_sig)
            else:
                try:
                    rmask = int(rmask)
                except ValueError:
                    try:
                        rmask = int(rmask, 16)
                    except ValueError:
                        raise ValueError("malformed value")

                reg_read = reg_sig & rmask
            this_case = HDLCase(
                reg_addr, stmts=[HDLAssignment(reg_data_out, reg_read)]
            )
            reg_select.add_case(this_case)
            continue
        reg_read = HDLConcatenation(None, size=reg.size, direction="lr")
        for field in reg_fields:
            done = False
            for name, port in mmap.ports.items():
                if port.direction == "out":
                    continue
                if port.target_field == field.name:
                    # print('found input target')
                    reg_read.insert(
                        HDLExpression(port.signal), min(field.get_range())
                    )
                    done = True
            if done is True:
                continue

            # write-only bits
            if field.permissions == "W":
                # put default value or zero?
                reg_read.insert(field.default_value, min(field.get_range()))
                continue
            elif field.permissions == "RW":
                # since not overriden by a target input, read from register
                reg_read.insert(
                    reg_sig[field.get_slice()], min(field.get_range())
                )
            else:
                # doesn't make sense!
                reg_read.insert(field.default_value, min(field.get_range()))

        # insert case
        this_case = HDLCase(
            reg_addr, stmts=[HDLAssignment(reg_data_out, reg_read.pack())]
        )
        reg_select.add_case(this_case)

    if args.o is not None:
        try:
            with open(args.o, "w") as dumpfile:
                dumpfile.write(vlog.dump_element(slave))
        except Exception:
            print("ERROR: could not output to file")
            exit(1)
    else:
        print(vlog.dump_element(slave))
