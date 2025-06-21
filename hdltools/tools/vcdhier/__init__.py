#!/usr/bin/env python3
"""VCD hierarchy inspector."""

import re
from typing import Optional, Tuple
from argparse import ArgumentParser
from hdltools.vcd.mixins.hierarchy import VCDHierarchyAnalysisMixin
from hdltools.vcd.streaming_parser import StreamingVCDParser
from hdltools.vcd import VCDScope


class VCDHierarchyExplorer(StreamingVCDParser, VCDHierarchyAnalysisMixin):
    """Hierarchy explorer."""

    def __init__(
        self,
        restrict_scopes: Optional[Tuple[str, bool]] = None,
        signal_filters: Optional[Tuple[str]] = None,
    ):
        """Initialize."""
        super().__init__()
        self._allowed_scopes = (
            [VCDScope.from_str(scope) for scope in restrict_scopes]
            if restrict_scopes is not None
            else None
        )
        self._signal_regexes = (
            [re.compile(fltr) for fltr in signal_filters]
            if signal_filters is not None
            else None
        )
        self._selected_vars = {}

    def _filter_signal_by_name(self, sig_name):
        for pattern in self._signal_regexes:
            if pattern.match(sig_name) is not None:
                return True

        return False

    def _filter_signal_by_scope(self, sig_scope):
        for scope, inclusive in self._allowed_scopes:
            if sig_scope == scope or (scope.contains(sig_scope) and inclusive):
                return True

        return False

    def initial_value_handler(self, stmt, fields):
        """Initial values."""
        self._abort_parser()

    def value_change_handler(self, stmt, fields):
        """Value changes."""
        self._abort_parser()

    def parse(self, data):
        """Parse with efficient filtering when available."""
        super().parse(data)

        # Use efficient search if available, otherwise fall back to legacy
        if hasattr(self, '_use_efficient') and self._use_efficient:
            self._selected_vars = self._efficient_filtering()
        else:
            self._selected_vars = self._legacy_filtering()

    def _efficient_filtering(self):
        """Use efficient indexed searches for filtering."""
        selected_vars = {}
        
        try:
            # If no filters, get all variables efficiently  
            if self._allowed_scopes is None and self._signal_regexes is None:
                efficient_vars = self.find_variables_efficient()
                return {var.get_first_identifier(): var for var in efficient_vars}
            
            # Apply scope filtering using indexed lookups
            candidate_vars = []
            
            if self._allowed_scopes is not None:
                # Use indexed scope searches
                for scope, inclusive in self._allowed_scopes:
                    scope_str = str(scope)
                    if inclusive:
                        # Find all variables in scope and subscopes (pattern search)
                        pattern = f"{scope_str}.*" if scope_str else "*"
                        vars_in_scope = self.find_variables_efficient(pattern=pattern)
                    else:
                        # Find variables in exact scope only
                        vars_in_scope = self.find_variables_efficient(scope=scope_str)
                    
                    candidate_vars.extend(vars_in_scope)
            else:
                # No scope filter - get all variables
                candidate_vars = self.find_variables_efficient()
            
            # Apply name filtering
            if self._signal_regexes is not None:
                # Filter candidates by name regex
                for var in candidate_vars:
                    if self._filter_signal_by_name(var.name):
                        selected_vars[var.get_first_identifier()] = var
            else:
                # No name filter - use all scope-filtered candidates
                for var in candidate_vars:
                    selected_vars[var.get_first_identifier()] = var
                    
            return selected_vars
            
        except (AttributeError, KeyError):
            # Fall back to legacy filtering if efficient storage not available
            return self._legacy_filtering()
    
    def _legacy_filtering(self):
        """Legacy O(n) filtering implementation."""
        # filter by scope
        selected_vars = {
            var_id: var
            for var_id, var in self._vars.items()
            if self._allowed_scopes is None
            or self._filter_signal_by_scope(var.scope)
        }

        # filter by name
        selected_vars = {
            var_id: var
            for var_id, var in selected_vars.items()
            if self._signal_regexes is None
            or self._filter_signal_by_name(var.name)
        }
        
        return selected_vars

    @property
    def selected_vars(self):
        """Get selected variables."""
        return self._selected_vars


def main():
    parser = ArgumentParser()
    parser.add_argument("vcd", help="path to vcd file")
    cmds = parser.add_subparsers(dest="command")
    dump_parser = cmds.add_parser("dumphier", help="dump hierarchy")

    dump_parser.add_argument(
        "--print-level", help="print hierarchical levels", action="store_true"
    )

    sig_parser = cmds.add_parser("signals", help="filter and search signals")
    sig_parser.add_argument(
        "--filter-scope", help="add scope filter", nargs="+"
    )
    sig_parser.add_argument(
        "--filter-name", help="add regex name filter", nargs="+"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_usage()
        exit(0)

    if not hasattr(args, "filter_scope"):
        args.filter_scope = None
    if not hasattr(args, "filter_name"):
        args.filter_name = None

    vcdh = VCDHierarchyExplorer(
        restrict_scopes=args.filter_scope, signal_filters=args.filter_name
    )
    with open(args.vcd, "r") as data:
        vcddata = data.read()
    vcdh.parse(vcddata)

    if args.command == "dumphier":
        vcdh.scope_hier.dump(args.print_level)
    elif args.command == "signals":
        print("INFO: found {} signals".format(len(vcdh.selected_vars)))
        for var in vcdh.selected_vars.values():
            aliases = var.aliases
            print(var)
            if aliases:
                print(var.dump_aliases())


if __name__ == "__main__":
    main()
