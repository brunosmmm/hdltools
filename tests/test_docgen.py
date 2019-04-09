"""Test documentation generator."""
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

    bullets = MarkDownList(["some", "items"])
    ordered = MarkDownList(["ordered", "items"], ordered=True)

    print(bullets)
    print(ordered)


def test_mdheader():

    heading_1 = MarkDownHeader("Header 1")
    heading_2 = MarkDownHeader("Header 2", level=2)

    print(heading_1)
    print(heading_2)


def test_mdlink():

    link_1 = MarkDownLink("http://hello.world")
    link_2 = MarkDownLink("http://hello.world", "Hello World!")

    print(link_1)
    print(link_2)


def test_mdquote():

    quote_ungob = MarkDownQuote("Some Multiline\n   Text.", gobble=False)
    quote_gob = MarkDownQuote("Some Multiline\n   Text.", gobble=True)

    print(quote_ungob)
    print(quote_gob)


def test_mdtext():

    bold = MarkDownBold("Bold Text")
    italic = MarkDownItalic("Italic Text")

    print(bold)
    print(italic)


def test_mdcode():

    code = MarkDownCode("lambda x : x**2")

    print(code)


def test_mdstr():

    text = (
        MarkDownHeader("My header")
        + "\n"
        + MarkDownItalic("Some Italic Text")
        + "\nSome regular text"
    )
    print(text)


def test_mddoc():

    doc = MarkDownDocument()

    doc.append(MarkDownHeader("My document"), newline=True)
    doc.append("Some Text!!", newline=True)
    doc.append(MarkDownList(["An element", "Another Element"]))

    print(doc)


def test_ghtable():

    table = GHMarkDownTable(["Name", "Description", "Misc"])
    table.add_line("test", "A test", "??")
    print(table)

    # errors
    try:
        table.add_line("test")
        raise Exception
    except IndexError:
        pass
