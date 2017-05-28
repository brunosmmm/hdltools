"""Comments."""

from .stmt import HDLStatement


def make_comment(text, tag=None):
    """Make comment."""
    if len(text.split('\n')) > 1:
        return HDLMultiLineComment(text, tag=tag)
    else:
        return HDLComment(text, tag=tag)


class HDLComment(HDLStatement):
    """Comments. Only useful for code generation."""

    def __init__(self, text, **kwargs):
        """Initialize."""
        super(HDLComment, self).__init__(stmt_type='null', **kwargs)
        if len(text.split('\n')) > 1:
            raise ValueError('cannot have multiline text')
        self.text = text

    def dumps(self):
        """Get representation."""
        return '//{}'.format(self.text)

    def is_legal(self):
        """Get legality."""
        return True


class HDLMultiLineComment(HDLStatement):
    """Multi-line comment."""

    def __init__(self, text, **kwargs):
        """Initialize."""
        super(HDLMultiLineComment, self).__init__(stmt_type='null', **kwargs)
        self.text = text

    def dumps(self):
        """Get Representation."""
        lines = self.text.split('\n')
        return '\n'.join('//{}'.format(line) for line in lines)

    def is_legal(self):
        """Get legality."""
        return True
