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

class TemplateRegister(ScoffASTObject):
    """TemplateRegister AST."""
    __slots__ = ("name", "properties", "scope", "_fields")

    def __init__(self, parent, name, properties=None, scope=None, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, properties=properties, scope=scope, **kwargs)
        self._fields = []

    def add_fields(self, *args):
        """Add fields."""
        self._fields.extend(args)

    def get_fields(self):
        """Get fields."""
        return self._fields

class SlaveRegister(ScoffASTObject):
    """SlaveRegister AST."""

    __slots__ = ("name", "address", "properties", "scope", "_fields")

    def __init__(self, parent, name, address, properties=None, scope=None, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent,
            name=name,
            address=address,
            properties=properties,
            scope=scope,
            **kwargs
        )
        self._fields = []

    def add_fields(self, *args):
        """Add fields."""
        self._fields.extend(args)

    def get_fields(self):
        """Get fields."""
        return self._fields


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


class SlaveRegisterFieldImplicit(ScoffASTObject):
    """SlaveRegisterField AST."""

    __slots__ = (
        "source",
        "position",
        "access",
        "default",
    )

    def __init__(
        self,
        parent,
        source,
        position=None,
        access=None,
        default=None,
        **kwargs
    ):
        """Initialize."""
        super().__init__(
            parent=parent,
            source=source,
            position=position,
            access=access,
            default=default,
            **kwargs
        )


class SlaveRegisterFieldExplicit(SlaveRegisterFieldImplicit):
    """SlaveRegisterField AST."""

    __slots__ = ("properties", "qualifiers")

    def __init__(self, parent, properties=None, qualifiers=None, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent,
            properties=properties,
            qualifiers=qualifiers,
            **kwargs
        )


class SlaveOutput(ScoffASTObject):
    """SlaveOutput AST."""

    __slots__ = ("desc", "trigger")

    def __init__(self, parent, desc, trigger, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, desc=desc, trigger=trigger, **kwargs)


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


class MainScopeGenerateStatement(ScoffASTObject):
    """MainScopeGenerateStatement AST."""

    __slots__ = ("var", "range", "gen_scope")

    def __init__(self, parent, var, range, gen_scope, **kwargs):
        """Initialize."""
        super().__init__(
            parent=parent, var=var, range=range, gen_scope=gen_scope, **kwargs
        )

class RegisterScopeGenerateStatement(ScoffASTObject):
    """MainScopeGenerateStatement AST."""

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


class IntProperty(ScoffASTObject):
    """IntProperty AST."""

    __slots__ = ("name", "value")

    def __init__(self, parent, name, value, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, name=name, value=value, **kwargs)

class StrProperty(ScoffASTObject):
    """StrProperty AST."""

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


class RegisterFieldPosition(ScoffASTObject):
    """Field position AST."""

    __slots__ = ("position",)

    def __init__(self, parent, position: BitField, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, position=position, **kwargs)


class RegisterFieldPermission(ScoffASTObject):
    """Field permission AST."""

    __slots__ = ("access",)

    def __init__(self, parent, access: str, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, access=access, **kwargs)


StaticValue = str | PositiveIntegerValue | int
DefaultValue = StaticValue | TemplatedNameSubst


class RegisterFieldDefault(ScoffASTObject):
    """Field default AST."""

    __slots__ = ("default",)

    def __init__(self, parent, default: DefaultValue, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, default=default, **kwargs)

class RegisterScope(ScoffASTObject):
    """RegisterScope AST."""

    __slots__ = ("statements",)

    def __init__(self, parent, statements, **kwargs):
        """Initialize."""
        super().__init__(parent=parent, statements=statements, **kwargs)


MMAP_AST_CLASSES = (
    AXIDescription,
    StaticStatement,
    ParameterStatement,
    FnCall,
    SlaveRegister,
    TemplatedNameSubstFragment,
    TemplatedNameSubstFmt,
    TemplatedNameSubst,
    SlaveRegisterFieldImplicit,
    SlaveRegisterFieldExplicit,
    SlaveOutput,
    SlaveInput,
    OutputDescriptor,
    InputDescriptor,
    SignalSource,
    SignalDestination,
    SourceBitAccessor,
    FieldBitAccessor,
    MainScopeGenerateStatement,
    RegisterScopeGenerateStatement,
    Range,
    IntProperty,
    StrProperty,
    PositiveIntegerValue,
    BitField,
    RegisterFieldPosition,
    RegisterFieldPermission,
    RegisterFieldDefault,
    TemplateRegister,
    RegisterScope
)
