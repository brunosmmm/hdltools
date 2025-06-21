"""Value change dump stuff."""

from .compare import VCDComparator, VCDComparisonResult, VCDStreamingComparator, compare_vcd_files


class VCDObject:
    """Abstract VCD object class."""


class VCDScope(VCDObject):
    """VCD scope."""

    def __init__(self, *scopes: str):
        """Initialize.

        Parameters
        ----------
        scopes
          List of scope names
        """
        self._scopes = []
        for scope in scopes:
            if not isinstance(scope, str):
                raise TypeError("scope name must be string")
            if len(scope) < 1:
                # empty, ignore
                continue
            self._scopes.append(scope)

    def __repr__(self):
        """Get representation."""
        return "::".join(self._scopes)

    def __len__(self):
        """Get scope length."""
        return len(self._scopes)

    def __getitem__(self, idx):
        """Get scope by index."""
        return self._scopes[idx]

    def __eq__(self, other):
        """Scope equality."""
        # FIXME: raising TypeError is weird
        if not isinstance(other, VCDScope):
            raise TypeError(
                f"other must be a VCDScope object, got {type(other)}"
            )
        return self._scopes == other._scopes

    def __hash__(self):
        """Get hash."""
        return hash(tuple(self._scopes))

    def contains(self, other: "VCDScope") -> bool:
        """Get whether this scope contains other scope.

        Arguments
        ----------
        other
          other scope to compare against
        """
        if not isinstance(other, VCDScope):
            raise TypeError("other must be a VCDScope object")
        if len(self) >= len(other):
            # cannot contain, length must be less
            return False

        for idx, this_subscope in enumerate(self._scopes):
            if other[idx] != this_subscope:
                return False

        return True

    @staticmethod
    def from_str(scope_str: str) -> "VCDScope":
        """Build from string."""
        if not isinstance(scope_str, str):
            raise TypeError("must be a string")
        scopes = scope_str.split("::")
        inclusive = len(scopes[-1]) < 1
        return (VCDScope(*scopes), inclusive)

    def pack(self) -> str:
        """Pack."""
        return str(self)
