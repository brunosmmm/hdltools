"""HDL Code generation."""

from .stmt import HDLStatement


def indent(fn):
    """Indent decorator."""
    def wrapper(*args):
        if not isinstance(args[0], HDLCodeGenerator):
            raise TypeError('decorator can only be used on HDLCodeGenerator '
                            'objects')
        # generate indentation
        args[0].increase_indent()
        if args[0].indent is True:
            indent_str = args[0].indent_str
        else:
            indent_str = ''

        print(args[0].indent_level)
        ret = '\n'.join([indent_str + x for x in fn(*args).split('\n')])
        args[0].decrease_indent()
        return ret
    return wrapper


class HDLCodeGenerator(object):
    """Abstract class for code generators."""

    statements = []
    class_aliases = {}

    def __init__(self, indent=False, indent_str='    '):
        """Initialize."""
        self.indent_level = 0
        self.indent = indent
        self.indent_str = indent_str

    def increase_indent(self):
        """Increase indentation level."""
        self.indent_level += 1

    def decrease_indent(self):
        """Decrease indentation level."""
        if self.indent_level > 0:
            self.indent_level -= 1

    def add_class_alias(self, use_as, alias_class):
        """Add class alias."""
        self.class_aliases[alias_class] = use_as

    def dump_element(self, element, **kwargs):
        """Get code representation for an element."""
        cls_name = element.__class__.__name__
        gen_method_name = 'gen_{}'.format(cls_name)

        # check statement validity
        if isinstance(element, HDLStatement):
            if element.is_legal() is False:
                raise ValueError('illegal statement passed')

        # aliases
        if cls_name in self.class_aliases:
            cls_name = self.class_aliases[cls_name]
            gen_method_name = 'gen_{}'.format(cls_name)

        try:
            return getattr(self, gen_method_name)(element, **kwargs)
        except AttributeError:
            raise TypeError('cannot generate code for object type '
                            '"{}"'.format(cls_name))
    # basic types to be implemented

    def gen_HDLIntegerConstant(self, element, **kwargs):
        """Generate Integer constants."""
        raise NotImplementedError

    def gen_HDLStringConstant(self, element, **kwargs):
        """Generate String constants."""
        raise NotImplementedError

    def gen_HDLVectorDescriptor(self, element, **kwargs):
        """Generate Vector elements."""
        raise NotImplementedError

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate ports."""
        raise NotImplementedError

    # builtin types

    def gen_int(self, element, **kwargs):
        """Integer."""
        return str(element)

    def get_str(self, element, **kwargs):
        """String."""
        return element
