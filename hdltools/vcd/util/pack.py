"""Pack into binary representations."""

import struct
from hdltools.vcd.util import PackableObject, PackableType


class PackInt(PackableType):
    """Pack integers."""

    _pack_identifier = "i"
    _pack_body_fmt = "I"

    @classmethod
    def pack(cls, what):
        """Pack."""
        if not isinstance(what, int):
            raise TypeError("must be integer")

        return struct.pack(cls._pack_body_fmt, what)


class PackStr(PackableType):
    """Pack strings."""

    _pack_identifier = "s"
    _pack_body_fmt = "s"

    @classmethod
    def pack(cls, what):
        """Pack."""
        if not isinstance(what, str):
            raise TypeError("must be string")

        return struct.pack(cls._pack_identifier, what)


class PackList(PackableType):
    """Pack a list."""

    _pack_identifier = "l"
    _pack_header_fmt = "Ic"

    @classmethod
    def pack(cls, what):
        """Pack."""
        if not isinstance(what, (list, tuple)):
            raise TypeError("must be a list or tuple")

        # we only support homogeneously typed lists
        for idx, item in enumerate(what):
            if idx == 0:
                continue
            if not isinstance(item, type(what[idx - 1])):
                raise RuntimeError("list type must be homogeneous")

        buffer = b""
        struct.pack_into("c", buffer, 0, cls._pack_identifier)
        struct.pack_into(cls._pack_header_fmt, buffer, 1, idx, pack_type(item))
        for item in what:
            buffer += pack(what)

        return buffer


class PackKeyValuePair(PackableType):
    """Pack key, value pair."""

    _pack_identifier = "p"
    _pack_body_fmt = "ss"

    @classmethod
    def pack(cls, what):
        """Pack."""
        if not isinstance(what, (list, tuple)):
            raise TypeError("must be list, tuple")
        if len(what) != 2:
            raise TypeError("must be tuple with 2 elements")

        return struct.pack(cls._pack_body_fmt, *what)


class PackDict(PackableType):
    """Pack a dictionary."""

    _pack_identifier = "d"
    _pack_header_fmt = "I"

    @classmethod
    def pack(cls, what):
        """Pack."""
        if not isinstance(what, dict):
            raise TypeError("must be a dict")

        buffer = b""
        struct.pack_into("c", buffer, 0, cls._pack_identifier)
        struct.pack_into(cls._pack_header_fmt, buffer, 1, len(what))

        for key, value in what.items():
            if not isinstance(key, str):
                raise TypeError("keys must be strings")
            if not isinstance(value, str):
                raise TypeError("values must be strings")

            buffer += PackKeyValuePair.pack(key, value)

        return buffer


def pack_type(what):
    """Get packing type."""
    if isinstance(what, (list, tuple)):
        return PackList
    if isinstance(what, dict):
        return PackDict
    if isinstance(what, int):
        return PackInt
    if isinstance(what, str):
        return PackStr
    if not isinstance(what, PackableObject):
        raise TypeError("what must be a PackableObject")

    return what.pack_type


def pack(what):
    """Pack automatically."""
    if isinstance(what, (list, tuple)):
        return PackList.pack(what)
    if isinstance(what, dict):
        return PackDict.pack(what)
    if isinstance(what, int):
        return PackInt.pack(what)
    if isinstance(what, str):
        return PackStr.pack(what)
    if not isinstance(what, PackableObject):
        raise TypeError("what must be a PackableObject")

    return what.pack()
