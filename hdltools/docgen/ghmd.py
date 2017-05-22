"""GitHub flavored markdown."""

from .markdown import MarkDownString, MarkDownDocument


class GHMarkDownDocument(MarkDownDocument):
    """GitHub flavored markdown document."""

    pass


class GHMarkDownTable(MarkDownString):
    """Table."""

    def __init__(self, headers):
        """Initialize."""
        self.lines = []
        if not isinstance(headers, (tuple, list)):
            raise TypeError('headers can only be tuple or list')
        self.headers = headers

    def add_line(self, *args):
        """Add line."""
        if len(args) != len(self.headers):
            raise IndexError('incorrect number of'
                             ' elements! need {}'.format(len(self.headers)))
        self.lines.append(args)

    def dumps(self):
        """Dump Table."""
        ret_str = ' | '.join(self.headers) + '\n'
        hyphens = ['-'*len(x) for x in self.headers]
        ret_str += ' | '.join(hyphens) + '\n'

        for line in self.lines:
            the_line = [str(x) for x in line]
            ret_str += ' | '.join(the_line) + '\n'

        return ret_str


class GHMarkDownTaskList(MarkDownString):
    """Task List."""

    pass
