"""Memory mapped interface builder."""

import copy
import re

from scoff.ast.visits.syntax import SyntaxChecker
from scoff.ast.visits.control import no_child_visits

# from scoff.ast.visits.control import SetFlag, ClearFlagAfter
import hdltools.util
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.mmap import MemoryMappedInterface
from hdltools.abshdl.module import HDLModuleParameter
from hdltools.abshdl.registers import HDLRegister, HDLRegisterField
from hdltools.logging import DEFAULT_LOGGER
from hdltools.mmap import FlagPort
from hdltools.mmap.ast import (
    SlaveRegisterFieldExplicit,
    SlaveRegisterFieldImplicit,
)
from hdltools.util import clog2

EXPRESSION_REGEX = re.compile(r"[\+\-\*\/\(\)]+")
TEMPLATE_REGEX = re.compile(r"\{([_a-zA-Z]\w*)\}")


class MMBuilderSemanticError(Exception):
    """Semantic error."""


class MMBuilder(SyntaxChecker):
    """interface builder."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._reg_size = None
        self._reg_addr_mode = None
        self._reg_addr_offset = None
        self._parameters = {}
        self._registers = {}
        self._ports = {}
        self._cur_reg_addr = 0
        self._replacement_values = {}
        self._templates = {}

    def _get_parameter_value(self, param_name):
        """Get parameter value."""
        if param_name in self._replacement_values:
            return self._replacement_values[param_name]
        return self._parameters[param_name]

    def _parse_properties(self, properties, node):
        """Parse properties."""
        reset_value = properties.get("default", None)
        if reset_value is not None:
            if isinstance(reset_value, str):
                try:
                    int_val = int(reset_value, 16)
                    properties["default"] = int_val
                except ValueError:
                    raise MMBuilderSemanticError(
                        f"invalid reset value: '{reset_value}'"
                    )
            if isinstance(
                node,
                (SlaveRegisterFieldExplicit, SlaveRegisterFieldImplicit),
            ):
                field_size = self.slice_size(
                    self.bitfield_pos_to_slice(node.position.position)
                )
                if field_size < HDLIntegerConstant.minimum_value_size(
                    properties["default"]
                ):
                    reset_value = properties["default"]
                    raise MMBuilderSemanticError(
                        f"default value {hex(reset_value)} does not fit in field with size {field_size}"
                    )
        return properties

    @staticmethod
    def slice_size(slic):
        """Get slice size in bits."""
        if len(slic) > 1:
            return slic[0] - slic[1] + 1
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
            if self._reg_addr_mode is not None:
                # warning, re-defining
                pass
            self._reg_addr_mode = node.value
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

    @no_child_visits
    def visitPre_RegisterScopeGenerateStatement(self, node):
        """Enter generate in register scope."""
        self.visitPre_MainScopeGenerateStatement(node)

    @no_child_visits
    def visitPre_MainScopeGenerateStatement(self, node):
        """Enter generate statement."""
        if self.get_flag_state("first_visit"):
            return
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

    def _templated_name_subst(self, node):
        def _find_name(name):
            """Find name."""
            if name not in self._parameters:
                raise NameError(f"in template: unknown name '{name}'")
            return self._get_parameter_value(name).value

        m = EXPRESSION_REGEX.findall(node)
        if m:
            # is expression
            expr = ""
            names = re.findall(r"[_a-zA-Z]\w*", node)
            for name in names:
                value = _find_name(name)
                expr = node.replace(name, str(value))
            expr = expr.replace("/", "//")
            try:
                expr = eval(expr)
            except SyntaxError:
                raise RuntimeError("invalid expression in template")
            return expr
        # is name
        return _find_name(node)

    def visit_TemplatedNameSubstFmt(self, node):
        """Visit template substitution."""
        return self._templated_name_subst(node.arg)

    def visitPre_SlaveRegister(self, node):
        """Enter register declaration."""
        if self.get_flag_state("first_visit"):
            self.dont_visit_children()

    def visit_SlaveRegister(self, node):
        """Visit register declaration."""
        if self.get_flag_state("first_visit"):
            return node
        if node.address is not None:
            reg_addr = node.address
        else:
            reg_addr = self._next_available_address()

        if node.template is not None and node.template:
            # using template
            if node.template not in self._templates:
                raise MMBuilderSemanticError(
                    f"unknown template '{node.template}'"
                )
            template = self._templates[node.template]
            register = copy.deepcopy(template)
            register.name = node.name
            register.addr = reg_addr
        elif isinstance(node.name, str):
            register = HDLRegister(
                node.name, size=self._reg_size, addr=reg_addr
            )
        # add properties
        for prop in node.properties:
            register.add_properties(
                **self._parse_properties({prop.name: prop.value}, node)
            )

        if register.name in self._registers:
            # warning, re-defining!
            pass
        # add fields
        for field in node.get_fields():
            register.add_fields(field)
        # add register
        DEFAULT_LOGGER.debug(f"adding register '{register.name}'")
        self._registers[register.name] = register

    def visit_TemplateRegister(self, node):
        """Visit register template."""
        if node.name in self._templates:
            raise RuntimeError(f"re-defining template '{node.name}'")
        register = HDLRegister(node.name, size=self._reg_size, addr=None)
        # add properties
        for prop in node.properties:
            register.add_properties(
                **self._parse_properties({prop.name: prop.value}, node)
            )
        # add fields
        for field in node.get_fields():
            register.add_fields(field)

        DEFAULT_LOGGER.debug(f"adding template '{register.name}'")
        self._templates[register.name] = register

    def visit_SlaveRegisterFieldImplicit(self, node):
        """Visit register field."""
        src_reg = node.parent.parent
        src_field = node.source
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
            reg_field.add_properties(
                **self._parse_properties({prop.name: prop.value}, node)
            )
        src_reg.add_fields(reg_field)

    def visit_SlaveRegisterFieldExplicit(self, node):
        """Visit register field."""
        src_reg = node.parent.parent
        src_field = node.source
        ssize = self.slice_size(
            self.bitfield_pos_to_slice(node.position.position)
        )
        if node.default is not None:
            if isinstance(node.default.default, str):
                try:
                    int_val = int(node.default.default)
                    node.default.default = int_val
                except ValueError:
                    pass
            if isinstance(node.default.default, int):
                param_size = HDLIntegerConstant.minimum_value_size(
                    node.default.default
                )
                defval = node.default.default
            else:
                if node.default.default.strip() in self._parameters:
                    param_size = 0
                    defval = HDLExpression(
                        node.default.default.strip(), size=ssize
                    )
                else:
                    raise RuntimeError(
                        "unknown identifier: {}".format(
                            node.default.default.strip()
                        )
                    )

            if ssize < param_size:
                raise RuntimeError("value does not fit in field")
        else:
            defval = 0

        reg_field = HDLRegisterField(
            src_field,
            self.bitfield_pos_to_slice(node.position.position),
            node.access.access,
            default_value=defval,
        )

        for prop in node.properties:
            reg_field.add_properties(
                **self._parse_properties({prop.name: prop.value}, node)
            )
        for qualifier in node.qualifiers:
            reg_field.add_properties(**{qualifier: True})
        src_reg.add_fields(reg_field)

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
        return self._visit_descriptor(node, "out")

    def visit_InputDescriptor(self, node):
        """Visit input descriptor."""
        return self._visit_descriptor(node, "in")

    def _visit_descriptor(self, node, direction):
        """Visit output/input descriptor."""
        if self.get_flag_state("first_visit"):
            return node
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
        if direction == "out" and node.parent.trigger:
            is_trigger = True
        else:
            is_trigger = False
        if isinstance(node.name, str):
            # simple declaration
            if src_reg not in self._registers:
                raise MMBuilderSemanticError(f"invalid register: {src_reg}")
            src_reg = self._registers[src_reg]
            if src_bit is not None and src_reg.has_field(src_bit) is False:
                raise MMBuilderSemanticError(f"invalid field: {src_bit}")
            port = FlagPort(src_reg, src_bit, direction, node.name, is_trigger)
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
                    raise MMBuilderSemanticError(f'invalid register: "{_reg}"')

                _reg = self._registers[_reg]
                if src_bit is not None and _reg.has_field(src_bit) is False:
                    raise MMBuilderSemanticError(f'invalid field: "{src_bit}"')

                port = FlagPort(
                    _reg,
                    src_bit,
                    direction,
                    fragment.fragment + str(port),
                    is_trigger,
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
                return int(node.hex, 16)
            except ValueError:
                raise MMBuilderSemanticError(
                    f"invalid hex value: '{node.hex}'"
                )
        if node.bin is not None:
            try:
                if node.bin.startswith("0b"):
                    return int(node.bin[2:], 2)
                return int(node.bin, 2)
            except ValueError:
                raise MMBuilderSemanticError(
                    f"invalid binary value: '{node.bin}'"
                )

    def visit_StrProperty(self, node):
        """Visit register property."""

        def _replace_template(value):
            return str(self._templated_name_subst(value.group(1)))

        # find and replace templates.
        templated_str = TEMPLATE_REGEX.sub(_replace_template, node.value)

        node.value = templated_str
        return node

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
        self.set_flag("first_visit")
        super().visit(node)
        self.clear_flag("first_visit")
        if self._reg_size is None:
            DEFAULT_LOGGER.warning("register size not defined, using 32 bits")
            self._reg_size = 32
        if self._reg_addr_mode is None:
            DEFAULT_LOGGER.warning("addressing mode not defined, using 'byte'")
            self._reg_addr_mode = "byte"
        if self._reg_addr_mode == "byte":
            self._reg_addr_offset = self._reg_size // 8
        else:
            self._reg_addr_offset = 1
        self.set_flag("second_visit")
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
