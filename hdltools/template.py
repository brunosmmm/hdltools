"""Use HDL files as template."""

import re


class HDLTemplateParser:
    """Parse templates."""

    _TEMPLATE_REGEX = re.compile(r"\/\*!\s*([0-9a-zA-Z_]+)\s*!\*\/")

    def __init__(self):
        """Initialize."""
        self.locations = {}
        self.text_lines = []

    def parse_str(self, text):
        """Parse and find template locations."""
        lines = text.split("\n")

        for linum, line in enumerate(lines):
            m = self._TEMPLATE_REGEX.match(line.strip())

            # add to locations
            if m is not None:
                self.locations[linum] = m.group(1)

        self.text_lines = lines

    def insert_contents(self, location, contents):
        """Substitute template for some content."""
        if location not in self.locations:
            raise KeyError("invalid location: {}".format(location))

        content_lines = contents.split("\n")
        offset = len(content_lines) - 1  # -1 because the original line is gone

        text_before = self.text_lines[0:location]
        text_after = self.text_lines[location + 1 :]

        # insert contents
        text_before.extend(content_lines)
        text_before.extend(text_after)
        self.text_lines = text_before

        del self.locations[location]
        self._update_locations(location, offset)

    def _update_locations(self, inserted_at, offset):
        new_locations = {}
        for location, template in self.locations.items():
            new_locations[location + offset] = template

        self.locations = new_locations

    def parse_file(self, filename):
        """Parse file."""
        with open(filename, "r") as f:
            self.parse_str(f.read())

    def _dumps_templated(self):
        return "\n".join(self.text_lines)

    def dump_templated(self, filename):
        """Dump templated file."""
        if len(self.locations) > 0:
            raise ValueError("must fill in all template fields before dumping")

        with open(filename, "w") as f:
            f.write("\n".join(self.text_lines))

    def find_template_tag(self, tag):
        for location, loc_tag in self.locations.items():
            if loc_tag == tag:
                return location

        return None


if __name__ == "__main__":
    parser = HDLTemplateParser()
    parser.parse_file("assets/verilog/axi_slave.v")
    parser.insert_contents(3, "line1\nline2\nline3")
