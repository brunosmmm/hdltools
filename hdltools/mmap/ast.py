"""AST classes pending implementation."""

from scoff.ast import ScoffASTObject


class AXIDescription(ScoffASTObject):
    """AXIDescription AST."""

    __slots__ = ("static_declarations", "params", "statements")

    def __init__(
        self,
        parent=None,
        static_declarations=None,
        params=None,
        statements=None,
        **kwargs
    ):
        """Initialize."""
        super().__init__(
            parent=parent,
            static_declarations=static_declarations,
            params=params,
            statements=statements,
            **kwargs
        )


class StaticStatement(ScoffASTObject):
    """StaticStatement AST."""

    __slots__ = ("var", "value")

    def __init__(self, parent, var, value, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, var=var, value=value, **kwargs)


class ParameterStatement(ScoffASTObject):
    """ParameterStatement AST."""

    __slots__ = ("name", "value")

    def __init__(self, parent, name, value, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, value=value, **kwargs)


class FnCall(ScoffASTObject):
    """FnCall AST."""

    __slots__ = ("fn", "args")

    def __init__(self, parent, fn, args=None, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, fn=fn, args=args, **kwargs)


class SlaveRegister(ScoffASTObject):
    """SlaveRegister AST."""

    __slots__ = ("name", "address", "properties")

    def __init__(self, parent, name, address, properties=None, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent,
            name=name,
            address=address,
            properties=properties,
            **kwargs
        )


class TemplatedNameSubstFragment(ScoffASTObject):
    """TemplatedNameSubstFragment AST."""

    __slots__ = ("fragment", "templates")

    def __init__(self, parent, fragment, templates=None, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent, fragment=fragment, templates=templates, **kwargs
        )


class TemplatedNameSubstFmt(ScoffASTObject):
    """TemplatedNameSubstFmt AST."""

    __slots__ = ("arg",)

    def __init__(self, parent, arg, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, arg=arg, **kwargs)


class TemplatedNameSubst(ScoffASTObject):
    """TemplatedNameSubstFmt AST."""

    __slots__ = ("fragments",)

    def __init__(self, parent, fragments, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, fragments=fragments, **kwargs)


class SlaveRegisterField(ScoffASTObject):
    """SlaveRegisterField AST."""

    __slots__ = (
        "source",
        "position",
        "position",
        "access",
        "access",
        "default",
        "default",
        "properties",
    )

    def __init__(
        self,
        parent,
        source,
        position=None,
        access=None,
        default=None,
        properties=None,
        **kwargs
    ):
        """Initialize."""
        super().__init__(
            parent=parent,
            source=source,
            position=position,
            access=access,
            default=default,
            properties=properties,
            **kwargs
        )


class SlaveOutput(ScoffASTObject):
    """SlaveOutput AST."""

    __slots__ = ("desc",)

    def __init__(self, parent, desc, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, desc=desc, **kwargs)


class SlaveInput(ScoffASTObject):
    """SlaveInput AST."""

    __slots__ = ("desc",)

    def __init__(self, parent, desc, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, desc=desc, **kwargs)


class OutputDescriptor(ScoffASTObject):
    """OutputDescriptor AST."""

    __slots__ = ("name", "sig")

    def __init__(self, parent, name, sig, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, sig=sig, **kwargs)


class InputDescriptor(ScoffASTObject):
    """InputDescriptor AST."""

    __slots__ = ("name", "sig")

    def __init__(self, parent, name, sig, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, sig=sig, **kwargs)


class SignalSource(ScoffASTObject):
    """SignalSource AST."""

    __slots__ = ("dest",)

    def __init__(self, parent, dest, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, dest=dest, **kwargs)


class SignalDestination(ScoffASTObject):
    """SignalDestination AST."""

    __slots__ = ("dest",)

    def __init__(self, parent, dest, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, dest=dest, **kwargs)


class SourceBitAccessor(ScoffASTObject):
    """SourceBitAccessor AST."""

    __slots__ = ("register", "bit")

    def __init__(self, parent, register, bit, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, register=register, bit=bit, **kwargs)


class FieldBitAccessor(ScoffASTObject):
    """FieldBitAccessor AST."""

    __slots__ = ("register", "bit")

    def __init__(self, parent, register, bit, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, register=register, bit=bit, **kwargs)


class GenerateStatement(ScoffASTObject):
    """GenerateStatement AST."""

    __slots__ = ("var", "range", "gen_scope")

    def __init__(self, parent, var, range, gen_scope, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent, var=var, range=range, gen_scope=gen_scope, **kwargs
        )


class Range(ScoffASTObject):
    """Range AST."""

    __slots__ = ("left", "right")

    def __init__(self, parent, left, right, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, left=left, right=right, **kwargs)


class RegisterProperty(ScoffASTObject):
    """RegisterProperty AST."""

    __slots__ = ("name", "value")

    def __init__(self, parent, name, value, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, value=value, **kwargs)


class PositiveIntegerValue(ScoffASTObject):
    """PositiveIntegerValue AST."""

    __slots__ = ("hex", "posint")

    def __init__(self, parent, hex, posint, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, hex=hex, posint=posint, **kwargs)


class BitField(ScoffASTObject):
    """BitField AST."""

    __slots__ = ("left", "right")

    def __init__(self, parent, left, right=None, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, left=left, right=right, **kwargs)


MMAP_AST_CLASSES = (
    AXIDescription,
    StaticStatement,
    ParameterStatement,
    FnCall,
    SlaveRegister,
    TemplatedNameSubstFragment,
    TemplatedNameSubstFmt,
    TemplatedNameSubst,
    SlaveRegisterField,
    SlaveOutput,
    SlaveInput,
    OutputDescriptor,
    InputDescriptor,
    SignalSource,
    SignalDestination,
    SourceBitAccessor,
    FieldBitAccessor,
    GenerateStatement,
    Range,
    RegisterProperty,
    PositiveIntegerValue,
    BitField,
)
