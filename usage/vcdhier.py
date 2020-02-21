"""VCD hierarchy inspector."""

import re
from typing import Optional, Tuple
from argparse import ArgumentParser
from hdltools.vcd.mixins import VCDHierarchyAnalysisMixin
from hdltools.vcd.parser import BaseVCDParser
from hdltools.vcd import VCDScope


class VCDHierarchyExplorer(BaseVCDParser, VCDHierarchyAnalysisMixin):
    """Hierarchy explorer."""

    def __init__(
        self,
        restrict_scopes: Optional[Tuple[str, bool]] = None,
        signal_filters: Optional[Tuple[str]] = None,
    ):
        """Initialize."""
        super().__init__()
        self._allowed_scopes = (
            [
                VCDScope.from_str(scope)
                for scope in restrict_scopes
            ]
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
        """Parse."""
        super().parse(data)

        # filter by scope
        self._selected_vars = {
            var_id: var
            for var_id, var in self._vars.items()
            if self._allowed_scopes is None
            or self._filter_signal_by_scope(var.scope)
        }

        # filter by name
        self._selected_vars = {
            var_id: var
            for var_id, var in self._selected_vars.items()
            if self._signal_regexes is None
            or self._filter_signal_by_name(var.name)
        }

    @property
    def selected_vars(self):
        """Get selected variables."""
        return self._selected_vars


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("vcd", help="path to vcd file")
    cmds = parser.add_subparsers(dest="command")
    cmds.add_parser("dumphier", help="dump hierarchy")
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
        vcdh.scope_hier.dump()
    elif args.command == "signals":
        print("INFO: found {} signals".format(len(vcdh.selected_vars)))
        for var in vcdh.selected_vars.values():
            print(var)
