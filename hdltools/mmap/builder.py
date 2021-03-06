"""Memory mapped interface builder."""

import copy
import re

from scoff.ast.visits.syntax import SyntaxChecker

# from scoff.ast.visits.control import SetFlag, ClearFlagAfter
import hdltools.util
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.mmap import MemoryMappedInterface
from hdltools.abshdl.module import HDLModuleParameter
from hdltools.abshdl.registers import HDLRegister, HDLRegisterField
from hdltools.logging import DEFAULT_LOGGER
from hdltools.mmap import FlagPort

EXPRESSION_REGEX = re.compile(r"[\+\-\*\/\(\)]+")


class MMBuilder(SyntaxChecker):
    """interface builder."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._reg_size = None
        self._reg_addr_offset = None
        self._parameters = {}
        self._registers = {}
        self._ports = {}
        self._cur_reg_addr = 0
        self._replacement_values = {}

    def _get_parameter_value(self, param_name):
        """Get parameter value."""
        if param_name in self._replacement_values:
            return self._replacement_values[param_name]
        return self._parameters[param_name]

    @staticmethod
    def slice_size(slic):
        """Get slice size in bits."""
        if len(slic) > 1:
            return slic[0] - slic[1] + 1
        else:
            return 1

    @staticmethod
    def bitfield_pos_to_slice(pos):
        """Convert to slice from parser object."""
        ret = [int(pos.left)]
        if pos.right is not None:
            ret.append(int(pos.right))

        return ret

    def _next_available_address(self):
        """Find next available address."""
        if not self._registers:
            if self._reg_addr_offset is None:
                raise RuntimeError("unknown addressing mode")
            self._cur_reg_addr += self._reg_addr_offset
            return 0

        addr_set = {register.addr for register in self._registers.values()}
        possible_offsets = range(
            0, max(addr_set) + self._reg_addr_offset, self._reg_addr_offset
        )
        for offset in possible_offsets:
            if offset in addr_set:
                continue
            else:
                self._cur_reg_addr = offset
                return offset

        # must increment
        self._cur_reg_addr = max(addr_set) + self._reg_addr_offset
        return self._cur_reg_addr

    def visit_StaticStatement(self, node):
        """Visit static statement."""
        if node.var == "register_size":
            if not isinstance(node.value, int):
                # placeholder for syntax error
                raise ValueError("identifier or expressions not supported")
            if self._reg_size is not None:
                # warning, re-defining
                pass
            self._reg_size = node.value
        elif node.var == "addr_mode":
            if not isinstance(node.value, str) or node.value not in (
                "byte",
                "word",
            ):
                raise ValueError("addr_mode can only be 'byte' or 'word'")
            if self._reg_addr_offset is not None:
                # warning, re-defining
                pass
            if node.value == "byte":
                self._reg_addr_offset = self._reg_size // 8
            else:
                self._reg_addr_offset = 1
        else:
            raise RuntimeError("unknown setting: '{}'".format(node.var))

    def visit_FnCall(self, node):
        """Visit function call."""
        # function calls only allowed for members of the hdltools.util module
        if not hasattr(hdltools.util, node.fn):
            raise NameError(f"function '{node.fn}' is unknown")

        fn = getattr(hdltools.util, node.fn)
        fn_args = []
        for arg in node.args:
            if isinstance(arg, str):
                # lookup parameter name
                if arg not in self._parameters:
                    raise NameError(f"unknown name '{arg}'")
                fn_args.append(self._get_parameter_value(arg).value.value)
            else:
                fn_args.append(arg)
        return fn(*fn_args)

    def visit_ParameterStatement(self, node):
        """Visit parameter statement."""
        if node.name in self._parameters:
            # warning, re-defining!
            pass
        value = HDLIntegerConstant(node.value)
        self._parameters[node.name] = HDLModuleParameter(
            node.name, "integer", value
        )

    def visit_Range(self, node):
        """Visit range."""
        if isinstance(node.left, str):
            if node.left not in self._parameters:
                raise NameError(f"unknown name '{node.left}'")
            node.left = self._get_parameter_value(node.left).value.value

        if isinstance(node.right, str):
            if node.right not in self._parameters:
                raise NameError(f"unknown name '{node.right}'")
            node.right = self._get_parameter_value(node.right).value.value

        return node

    def visitPre_GenerateStatement(self, node):
        """Enter generate statement."""
        generated_scope = []
        # visit ahead
        super().visit(node.range)
        for range_val in range(node.range.left, node.range.right):
            # HACK insert temporary parameter value
            self._parameters[node.var] = HDLModuleParameter(
                node.var, "integer", range_val
            )
            for stmt in node.gen_scope:
                cpy_stmt = copy.deepcopy(stmt)
                super().visit(cpy_stmt)
                generated_scope.append(cpy_stmt)
            del self._parameters[node.var]
        node.gen_scope = generated_scope

    def visit_TemplatedNameSubstFmt(self, node):
        """Visit template substitution."""

        def _find_name(name):
            """Find name."""
            if name not in self._parameters:
                raise NameError(f"in template: unknown name '{name}'")
            return self._get_parameter_value(name).value

        m = EXPRESSION_REGEX.findall(node.arg)
        if m:
            # is expression
            expr = ""
            names = re.findall(r"[_a-zA-Z]\w*", node.arg)
            for name in names:
                value = _find_name(name)
                expr = node.arg.replace(name, str(value))
            expr = expr.replace("/", "//")
            try:
                expr = eval(expr)
            except SyntaxError:
                raise RuntimeError("invalid expression in template")
            return expr
        # is name
        return _find_name(node.arg)

    def visit_SlaveRegister(self, node):
        """Visit register declaration."""
        if node.address is not None:
            reg_addr = node.address
        else:
            reg_addr = self._next_available_address()

        if isinstance(node.name, str):
            register = HDLRegister(
                node.name, size=self._reg_size, addr=reg_addr
            )
            # add properties
            for prop in node.properties:
                register.add_properties(**{prop.name: prop.value})

            if register.name in self._registers:
                # warning, re-defining!
                pass
            # add register
            DEFAULT_LOGGER.debug(f"adding register '{register.name}'")
            self._registers[register.name] = register
        else:
            (fragment,) = node.name.fragments
            (template,) = fragment.templates
            try:
                start, end = template.arg.split("-")
                _addr = reg_addr
                for reg in range(int(start), int(end) + 1):
                    reg_name = fragment.fragment + str(reg)
                    register = HDLRegister(
                        reg_name, size=self._reg_size, addr=_addr
                    )
                    for prop in node.properties:
                        register.add_properties(
                            **{prop.name: prop.value.format(str(reg))}
                        )
                    if register.name in self._registers:
                        # warning: re-defining!
                        pass
                    # add register
                    self._registers[register.name] = register
                    _addr = self._next_available_address()
            except:
                raise RuntimeError("error in template rule")

    def visit_SlaveRegisterField(self, node):
        """Visit register field."""
        src_reg, src_field = node.source
        if src_reg not in self._registers:
            raise ValueError("unknown register: {}".format(src_reg))

        ssize = self.slice_size(self.bitfield_pos_to_slice(node.position))
        if node.default is not None:
            if isinstance(node.default, int):
                param_size = HDLIntegerConstant.minimum_value_size(
                    node.default
                )
                defval = node.default
            else:
                if node.default.strip() in self._parameters:
                    param_size = 0
                    defval = HDLExpression(node.default.strip(), size=ssize)
                else:
                    raise RuntimeError(
                        "unknown identifier: {}".format(node.default.strip())
                    )

            if ssize < param_size:
                raise RuntimeError("value does not fit in field")
        else:
            defval = 0

        reg_field = HDLRegisterField(
            src_field,
            self.bitfield_pos_to_slice(node.position),
            node.access,
            default_value=defval,
        )

        for prop in node.properties:
            reg_field.add_properties(**{prop.name: prop.value})
        self._registers[src_reg].add_fields(reg_field)

    def visit_SourceBitAccessor(self, node):
        """Visit source bit accessor."""
        return (node.register, node.bit)

    def visit_TemplatedNameSubstFragment(self, node):
        """Visit fragments."""
        return node.fragment + "".join(
            [str(template) for template in node.templates]
        )

    def visit_TemplatedNameSubst(self, node):
        """Templated name."""
        return "".join(node.fragments)

    def visit_TemplatedNameDecl(self, node):
        """Visit templated name declaration."""
        if len(node.fragments) > 1:
            raise NotImplementedError
        (fragment,) = node.fragments
        if len(fragment.templates) > 1:
            raise NotImplementedError
        if not fragment.templates:
            return fragment.fragment
        return node

    def visit_SignalSource(self, node):
        """Visit signal source."""
        return node.dest

    def visit_SignalDestination(self, node):
        """Visit signal destination."""
        return node.dest

    def visit_OutputDescriptor(self, node):
        """Visit output descriptor."""
        self._visit_descriptor(node, "out")

    def visit_InputDescriptor(self, node):
        """Visit input descriptor."""
        self._visit_descriptor(node, "in")

    def _visit_descriptor(self, node, direction):
        """Visit output/input descriptor."""
        if direction not in ("in", "out"):
            raise RuntimeError("invalid direction")
        if isinstance(node.sig, str):
            src_reg = node.sig
            src_bit = None
        elif isinstance(node.sig, tuple):
            # SourceBitAccessor
            src_reg, src_bit = node.sig
        else:
            # templated name
            src_reg = node.sig
            src_bit = None
        if isinstance(node.name, str):
            # simple declaration
            if src_reg not in self._registers:
                raise KeyError("invalid register: {}".format(src_reg))
            src_reg = self._registers[src_reg]
            if src_bit is not None and src_reg.has_field(src_bit) is False:
                raise KeyError("invalid field: {}".format(src_bit))
            port = FlagPort(src_reg, src_bit, direction, node.name)
            if port.name in self._ports:
                # warning, re-define
                pass
            self._ports[port.name] = port
        else:
            (fragment,) = node.name.fragments
            try:
                start, end = fragment.templates[0].rule.split("-")
            except:
                raise RuntimeError("error in fragment rule")
            for port in range(int(start), int(end) + 1):
                fmt_str = "{{{}}}".format(
                    src_reg.fragments[0].templates[0].arg
                )
                _reg = src_reg.fragments[0].fragment + fmt_str.format(port)
                if _reg not in self._registers:
                    raise KeyError('invalid register: "{}"'.format(_reg))

                _reg = self._registers[_reg]
                if src_bit is not None and _reg.has_field(src_bit) is False:
                    raise KeyError('invalid field: "{}"'.format(src_bit))

                port = FlagPort(
                    _reg, src_bit, direction, fragment.fragment + str(port),
                )
                self._ports[port.name] = port

    def visit_PositiveIntegerValue(self, node):
        """Visit a static value."""
        if node.posint is not None:
            return int(node.posint)
        if node.hex is not None:
            try:
                if node.hex.startswith("0x"):
                    return int(node.hex[2:], 16)
                else:
                    return int(node.hex, 16)
            except ValueError:
                # placeholder for syntax error
                raise

    def visit(self, node, param_replace=None):
        """Visit."""
        self._replacement_values = (
            {
                name: HDLModuleParameter(
                    name, "integer", HDLIntegerConstant(value)
                )
                for name, value in param_replace.items()
            }
            if param_replace is not None
            else {}
        )
        super().visit(node)
        mmap = MemoryMappedInterface(self._reg_size, self._reg_addr_offset)
        for register in self._registers.values():
            mmap.add_register(register)
        for port in self._ports.values():
            mmap.add_port(port)
        for param_name, param in self._parameters.items():
            if param_name in self._replacement_values:
                mmap.add_parameter(
                    param_name, self._replacement_values[param_name]
                )
            else:
                mmap.add_parameter(param_name, param)

        return mmap
