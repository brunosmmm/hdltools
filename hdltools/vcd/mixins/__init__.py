"""VCD Parser mixins."""


class ScopeMap:
    """Scope map."""

    def __init__(self):
        """Initialize."""
        self._map = {}

    def __getitem__(self, index):
        """Get item."""
        if not isinstance(index, tuple):
            raise TypeError("index must be a tuple")

        current_map = self._map
        for element in index:
            current_map = current_map[element]

        return current_map

    def add_hierarchy(self, index, hier_name):
        """Add hierarchy."""
        outer = self[index]
        if hier_name in outer:
            raise ValueError("scope already exists.")
        outer[hier_name] = {}

    def dump(self, print_levels=False):
        """Print out."""
        ScopeMap._dump(self._map, print_levels)

    @staticmethod
    def _dump(hier, print_levels=False, indent=0):
        """Print out."""
        level = str(indent) + " " if print_levels else ""
        current_indent = "  " * indent
        for name, _hier in hier.items():
            print(level + current_indent + name)
            ScopeMap._dump(_hier, print_levels, indent + 1)

    def serialize(self):
        """Serialize."""
        return self._map.deepcopy()


class VCDParserMixin:
    """VCD Parser mixin abstract class."""

    def __init__(self, **kwargs):
        """Initialize."""
        super().__init__(**kwargs)
        self._mixin_init()

    def _mixin_init(self):
        """Mixin initialization."""
        raise NotImplementedError
