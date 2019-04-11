"""Generate markdown documentation."""


class MarkDownObject:
    """Abstract class for markdown-related objects."""

    def dumps(self):
        """Dump representation."""
        pass

    def __str__(self):
        """Alias for dumps."""
        return self.dumps()


class MarkDownString(MarkDownObject):
    """Generic markdown text."""

    def __init__(self, text):
        """Initialize."""
        self.text = str(text)

    def __add__(self, other):
        """Add operator."""
        return str(self) + other

    def __radd__(self, other):
        """Reverse add operator."""
        return other + str(self)


class MarkDownItalic(MarkDownString):
    """Italic text."""

    def __init__(self, text):
        """Initialize."""
        super().__init__(text)

    def dumps(self):
        """Get italic text."""
        return "_{}_".format(self.text)


class MarkDownBold(MarkDownString):
    """Bold text."""

    def __init__(self, text):
        """Initialize."""
        super().__init__(text)

    def dumps(self):
        """Get bold text."""
        return "**{}**".format(self.text)


class MarkDownHeader(MarkDownString):
    """Markdown header."""

    def __init__(self, text, level=1):
        """Initialize."""
        super().__init__(text)
        if level not in range(1, 7):
            raise ValueError("heading level must be between 1 and 6")

        self.level = level

    def dumps(self):
        """Dump string."""
        ret_str = "#" * self.level + " " + self.text
        return ret_str


class MarkDownList(MarkDownString):
    """Lists."""

    def __init__(self, objects=None, ordered=False):
        """Initialize."""
        self.items = []
        self.ordered = ordered
        if objects is not None:
            self.items.extend(objects)

    def dumps(self):
        """Dump list string."""
        ret_str = ""
        for count, item in enumerate(self.items):
            if self.ordered is False:
                ret_str += "* {}\n".format(str(item))
            else:
                ret_str += "{}. {}\n".format(count + 1, str(item))

        return ret_str


class MarkDownLink(MarkDownString):
    """URLs."""

    def __init__(self, url, text=None):
        """Initialize."""
        super().__init__(text)
        self.url = url

    def dumps(self):
        """Dump link."""
        if self.text is None:
            return str(self.url)
        else:
            return "[{}]({})".format(str(self.text), self.url)


class MarkDownQuote(MarkDownString):
    """Block Quotes."""

    def __init__(self, text, gobble=True):
        """Initialize."""
        super().__init__(text)
        self.gobble = gobble

    def dumps(self):
        """Dump quoted text."""
        ret_str = ""
        for line in self.text.split("\n"):
            if self.gobble is True:
                the_line = str(line).strip()
            else:
                the_line = str(line)
            ret_str += "> {}\n".format(the_line)

        return ret_str


class MarkDownCode(MarkDownString):
    """Code blocks."""

    def __init__(self, text):
        """Initialize."""
        super().__init__(text)

    def dumps(self):
        """Dump code."""
        return "`{}`".format(str(self.text))


class MarkDownDocument(MarkDownObject):
    """Markdown document."""

    def __init__(self):
        """Initialize."""
        self.elements = []

    def append(self, element, newline=False):
        """Add element to document."""
        self.elements.append(element)
        if newline is True:
            self.elements.append("\n")

    def dumps(self):
        """Dump document."""
        return "".join([str(x) for x in self.elements])
