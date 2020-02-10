"""VCD Value tracker."""

import re
from typing import Tuple, Optional, Union
from hdltools.vcd import VCDScope
from hdltools.vcd.parser import BaseVCDParser, VCDParserError
from hdltools.vcd.mixins import VCDHierarchyAnalysisMixin
from hdltools.patterns import Pattern


# TODO: multi value tracker
class VCDValueTracker(BaseVCDParser, VCDHierarchyAnalysisMixin):
    """VCD Value tracker.

    Track a tagged value through system hierarchy.
    """

    def __init__(
        self,
        track: Pattern,
        restrict_src: Optional[Union[Tuple[str], VCDScope]] = None,
        restrict_dest: Optional[Union[Tuple[str], VCDScope]] = None,
        inclusive_src=False,
        inclusive_dest=False,
        ignore_signals: Optional[Tuple[str]] = None,
        ignore_scopes: Optional[Tuple[str]] = None,
        anchors: Optional[Tuple[str, str]] = None,
    ):
        """Initialize."""
        super().__init__()
        if not isinstance(track, Pattern):
            raise TypeError("track must be a Pattern object")
        self._track_value = track
        self._track_history = []
        self._stmt_count = 0
        if isinstance(restrict_src, tuple):
            restrict_src = VCDScope(*restrict_src)
        if isinstance(restrict_dest, tuple):
            restrict_dest = VCDScope(*restrict_dest)
        self._restrict_src = restrict_src
        self._restrict_dest = restrict_dest
        self._inclusive_src = inclusive_src
        self._inclusive_dest = inclusive_dest
        if ignore_signals is not None:
            self._ignore_sig = [re.compile(ign) for ign in ignore_signals]
        else:
            self._ignore_sig = None
        if ignore_scopes is not None:
            self._ignore_scope = [re.compile(ign) for ign in ignore_scopes]
        else:
            self._ignore_scope = None

        # source, destination anchors
        src_anchor, dest_anchor = (
            anchors if anchors is not None else (None, None)
        )
        self._src_anchor = (
            re.compile(src_anchor) if src_anchor is not None else None
        )
        self._dest_anchor = (
            re.compile(dest_anchor) if dest_anchor is not None else None
        )
        self._maybe_src = None
        self._maybe_dest = None

    def _parse_progress(self):
        """Track parsing progress."""
        self._stmt_count += 1
        # print("DEBUG: #lines = {}".format(self._current_line))

    def header_statement_handler(self, stmt, fields):
        """Handle header statements.

        Build variable-scope map.
        """
        self._parse_progress()

    def initial_value_handler(self, stmt, fields):
        """Handle initial values."""
        self._parse_progress()
        if self._track_value.match(fields["value"]):
            # found
            var = self.variables[fields["var"]]
            self._add_to_history(var.scope, var.name)

    def value_change_handler(self, stmt, fields):
        """Handle value change."""
        self._parse_progress()
        var_scope = self.variables[fields["var"]].scope
        in_src_scope = self._restrict_src is not None and (
            var_scope == self._restrict_src
            or (self._restrict_src.contains(var_scope) and self._inclusive_src)
        )

        in_dest_scope = self._restrict_dest is not None and (
            var_scope == self._restrict_dest
            or (
                self._restrict_dest.contains(var_scope)
                and self._inclusive_dest
            )
        )
        if (self._restrict_src is not None and not in_src_scope) and (
            self._restrict_dest is not None and not in_dest_scope
        ):
            return
        if self._track_value.match(fields["value"]):
            if self._ignore_sig is not None:
                for patt in self._ignore_sig:
                    if (
                        patt.match(self.variables[fields["var"]].name)
                        is not None
                    ):
                        # ignore
                        return
            print("DEBUG: current time = {}".format(self.current_time))
            print(
                "DEBUG: found value match, variable is {}".format(
                    self.variables[fields["var"]]
                )
            )
            if fields["var"] not in self.variables:
                raise VCDParserError(
                    'unknown variable in change event: "{}"'.format(
                        fields["var"]
                    )
                )
            var = self.variables[fields["var"]]
            idx = self._add_to_history(var.scope, var.name, self.current_time)
            # FIXME: make sure that anchors are not used without scope restriction
            if in_src_scope:
                if self._src_anchor is not None and self._maybe_dest is None:
                    if (
                        self._src_anchor.match(
                            self.variables[fields["var"]].name
                        )
                        is not None
                    ):
                        # new probable source
                        self._maybe_src = idx
                else:
                    # anything that appears is probable source
                    self._maybe_src = idx

            if in_dest_scope:
                if self._maybe_dest is None and self._maybe_src is not None:
                    if (
                        self._dest_anchor is not None
                        and self._dest_anchor.match(
                            self.variables[fields["var"]].name
                        )
                        is not None
                    ):
                        self._maybe_dest = idx
                    elif self._dest_anchor is None:
                        self._maybe_dest = idx

    @property
    def current_scope_depth(self):
        """Get current sope depth."""
        return len(self._scope_stack)

    @property
    def current_scope(self):
        """Get current scope."""
        return tuple(self._scope_stack)

    @property
    def scope_hier(self):
        """Get scope hierarchy."""
        return self._scope_map

    @property
    def history(self):
        """Get tracking history."""
        return tuple(self._track_history)

    @property
    def maybe_src(self):
        """Get probable source."""
        return self._maybe_src

    @property
    def maybe_dest(self):
        """Get probable destination."""
        return self._maybe_dest

    def _add_to_history(self, scope, signal, time):
        """Add to history."""
        self._track_history.append((scope, signal, time))
        return len(self._track_history) - 1

    def parse(self, data):
        """Parse."""
        self._stmt_count = 0
        return super().parse(data)
