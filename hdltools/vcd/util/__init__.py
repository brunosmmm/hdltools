"""Utilities."""

from uuid import uuid4

PACKABLE_TYPES = {}


class PackableType:
    """Packable type description."""

    _pack_identifier = None
    _pack_header_fmt = None

    def __init_subclass__(cls, **kwargs):
        """Create subclass."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_pack_identifier") and cls._pack_identifier is not None:
            if cls._pack_identifier in PACKABLE_TYPES:
                raise ValueError("identifier '{}' already reserved".format(cls._pack_identifier))
        else:
            raise ValueError("_pack_identifier member must be specified")
        if len(cls._pack_identifier) > 1:
            raise ValueError("_pack_identifier member must be a single character")
        # create uuid
        cls._type_uuid = uuid4()

    @property
    def type_uuid(self):
        """Get type uuid."""
        return self._type_uuid

    @property
    def type_identifier(self):
        """Get type identifier."""
        return self._identifier

    @classmethod
    def pack(cls, what):
        """Pack."""
        raise NotImplementedError

    @classmethod
    def unpack(cls, src):
        """Unpack."""
        raise NotImplementedError

    def __eq__(self, other):
        """Equality check."""
        if not isinstance(other, PackableType):
            return False
        return self._type_uuid == other.type_uuid

    def __hash__(self):
        """Get hash."""
        return hash(tuple([self._type_uuid]))


class PackableObjectMeta:
    """Packable object meta class."""

    @property
    def pack_type(cls):
        """Get pack type."""
        return cls._pack_type


class PackableObject:
    """Packable object."""

    _pack_type = None

    def __init__(self):
        """Initialize."""
        if not issubclass(self.pack_type, PackableType):
            raise TypeError("_pack_type must be a PackableType object")

    def pack(self):
        """Pack into binary format."""
        # default to packed type function
        return self._pack_type.pack(self)

    @classmethod
    def unpack(cls, src):
        """Unpack from binary format."""
        return cls._pack_type.unpack(src)

    @property
    def pack_type(self):
        """Pack type."""
        return self._pack_type
