"""Test documentation generator."""

import pytest

from hdltools.docgen.markdown import (
    MarkDownList,
    MarkDownHeader,
    MarkDownLink,
    MarkDownQuote,
    MarkDownBold,
    MarkDownItalic,
    MarkDownCode,
    MarkDownDocument,
)
from hdltools.docgen.ghmd import GHMarkDownTable


def test_mdlist():

    MarkDownList(["some", "items"])
    MarkDownList(["ordered", "items"], ordered=True)


def test_mdheader():

    MarkDownHeader("Header 1")
    MarkDownHeader("Header 2", level=2)


def test_mdlink():

    MarkDownLink("http://hello.world")
    MarkDownLink("http://hello.world", "Hello World!")


def test_mdquote():

    MarkDownQuote("Some Multiline\n   Text.", gobble=False)
    MarkDownQuote("Some Multiline\n   Text.", gobble=True)


def test_mdtext():

    MarkDownBold("Bold Text")
    MarkDownItalic("Italic Text")


def test_mdcode():

    MarkDownCode("lambda x : x**2")


def test_mdstr():

    _ = (
        MarkDownHeader("My header")
        + "\n"
        + MarkDownItalic("Some Italic Text")
        + "\nSome regular text"
    )


def test_mddoc():

    doc = MarkDownDocument()

    doc.append(MarkDownHeader("My document"), newline=True)
    doc.append("Some Text!!", newline=True)
    doc.append(MarkDownList(["An element", "Another Element"]))


def test_ghtable():

    table = GHMarkDownTable(["Name", "Description", "Misc"])
    table.add_line("test", "A test", "??")

    # errors
    with pytest.raises(IndexError):
        table.add_line("test")
