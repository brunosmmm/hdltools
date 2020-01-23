"""Memory mapped interface builder."""

from scoff.parsers.syntax import SyntaxChecker, SyntaxCheckerError
from scoff.parsers.syntax import SyntaxErrorDescriptor

from hdltools.abshdl.module import HDLModuleParameter
from hdltools.abshdl.const import HDLIntegerConstant
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.registers import HDLRegister, HDLRegisterField
from hdltools.mmap import FlagPort
from hdltools.abshdl.mmap import MemoryMappedInterface


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

    def visit_ParameterStatement(self, node):
        """Visit parameter statement."""
        if not isinstance(node.value, int):
            raise ValueError("identifier or expressions not supported")

        if node.name in self._parameters:
            # warning, re-defining!
            pass
        value = HDLIntegerConstant(node.value)
        self._parameters[node.name] = HDLModuleParameter(
            node.name, "integer", value
        )

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
            self._registers[register.name] = register
        else:
            (fragment,) = node.name.fragments
            (template,) = fragment.templates
            try:
                start, end = template.rule.split("-")
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
        src_reg = node.source.register
        if src_reg not in self._registers:
            raise ValueError("unknown register: {}".format(src_reg))

        ssize = self.slice_size(self.bitfield_pos_to_slice(node.position))
        if node.default is not None:
            if isinstance(node.default, int):
                param_size = HDLIntegerConstant.minimum_value_size(node.default)
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
            node.source.bit,
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

    def visit_TemplatedNameSubst(self, node):
        """Templated name."""
        if len(node.fragments) > 1:
            raise NotImplementedError
        (fragment,) = node.fragments
        if len(fragment.templates) > 1:
            raise NotImplementedError
        if not fragment.templates:
            # simple string, return
            return fragment.fragment
        # do not process yet
        return node

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
                fmt_str = "{{{}}}".format(src_reg.fragments[0].templates[0].arg)
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

    def visit(self, node):
        """Visit."""
        super().visit(node)
        mmap = MemoryMappedInterface(self._reg_size, self._reg_addr_offset)
        for register in self._registers.values():
            mmap.add_register(register)
        for port in self._ports.values():
            mmap.add_port(port)
        for param_name, param in self._parameters.items():
            mmap.add_parameter(param_name, param)

        return mmap
