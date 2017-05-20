"""HDL Code generation."""


class HDLCodeGenerator(object):
    """Abstract class for code generators."""

    statements = []
    class_aliases = {}

    def add_class_alias(self, use_as, alias_class):
        """Add class alias."""
        self.class_aliases[alias_class] = use_as

    def dump_element(self, element, **kwargs):
        """Get code representation for an element."""
        cls_name = element.__class__.__name__
        gen_method_name = 'gen_{}'.format(cls_name)

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
