"""Test VCD extensions."""

from hdltools.vcd.parser import BaseVCDParser


def test_parser():
    """Test VCD parser."""
    with open("tests/assets/example.vcd", "r") as vcdfile:
        vcd_data = vcdfile.read()

    vparser = BaseVCDParser()
    vparser.parse(vcd_data)


if __name__ == "__main__":
    test_parser()
