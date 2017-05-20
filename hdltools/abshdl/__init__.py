"""Common HDL declaration elements."""

import math
import ast
import operator as op
import copy

# TODO: EVALUATE ONLY INTEGERS, FAIL OTHERWISE


class HDLObject:
    """Abstract class from which all HDL objects derive from."""
    pass


class HDLValue(HDLObject):
    """Abstract class for deriving other values."""

    def dumps(self):
        """Get representation."""
        pass

    def evaluate(self, **kwargs):
        """Evaluate and return value."""
        pass


class HDLBuiltinFunction(HDLObject):
    """Builtin function."""

    def __init__(self, name, args, ret, cb):
        """Initialize.

        Args
        ----
        name: str
           Function name
        args: List
           Argument List: TBD
        ret: class
           Return type ? TBD
        """
        self.name = name
        self.arg_list = args
        self.ret_type = ret
        self.cb = cb

    def call(self, *args, **kwargs):
        """Perform function call.

        Args
        ----
        args: list
           Argument list
        """
        # perform argument checking?
        return self.cb(*args, **kwargs)


class HDLBuiltins(HDLObject):
    """Default builtin objects."""

    # placeholders
    _functions = {'_ceil':
                  HDLBuiltinFunction(
                      'ceil',
                      [],
                      None,
                      lambda x, **scope:
                      int(
                          math.ceil(
                              HDLBuiltins
                              ._decide_and_evaluate(x,
                                                    **scope)))),
                  '_log2':
                  HDLBuiltinFunction(
                      'log2',
                      [],
                      None,
                      lambda x, **scope:
                      math.log2(HDLBuiltins
                                ._decide_and_evaluate(x,
                                                      **scope))),
                  '_clog2':
                  HDLBuiltinFunction(
                      'clog2',
                      [],
                      None,
                      lambda x, **scope:
                      int(
                          math.ceil(
                              math.log2(
                                  HDLBuiltins.
                                  _decide_and_evaluate(x,
                                                       **scope)))))}

    @staticmethod
    def _decide_and_evaluate(value, **scope):
        if isinstance(value, int):
            return value
        elif isinstance(value, HDLExpression):
            return value.evaluate(**scope)
        else:
            raise TypeError('invalid type: "{}"'.format(type(value)))

    @classmethod
    def get_builtin_scope(cls):
        """Get dictionary with all available symbols."""
        scope = {}
        scope.update(cls._functions)
        return scope


class HDLExpression(HDLValue):
    """An expression involving parameters."""

    _ast_op_names = {ast.Sub: '-',
                     ast.Add: '+',
                     ast.Mult: '*',
                     ast.Div: '/'}
    _operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                  ast.Div: op.truediv, ast.Pow: op.pow,
                  ast.USub: op.neg}

    def __init__(self, value):
        """Initialize.

        Args
        ----
        expr_tree: ast.Expression
            Expression tree
        """
        super(HDLExpression, self).__init__()
        if isinstance(value, ast.Expression):
            self.tree = value
        elif isinstance(value, HDLIntegerConstant):
            self.tree = ast.Expression(body=ast.Num(n=value.value))
        elif isinstance(value, int):
            self.tree = ast.Expression(body=ast.Num(n=value))
        else:
            raise TypeError('invalid type provided')

    def evaluate(self, **kwargs):
        """Evaluate current expression.

        Args
        ----
        kwargs: dict
           Dictionary which must contain all necessary symbols to evaluate
        """
        return self._evaluate(self.tree, **kwargs)

    def _evaluate(self, node, **kwargs):
        """Evaluate current expression.

        Args
        ----
        kwargs: dict
           Dictionary which must contain all necessary symbols to evaluate
        """
        if isinstance(node, ast.Expression):
            return self._evaluate(node.body, **kwargs)
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in kwargs:
                return kwargs[node.id]
            else:
                raise KeyError(node.id)
        elif isinstance(node, ast.BinOp):
            return self._operators[type(node.op)](self._evaluate(node.left,
                                                                 **kwargs),
                                                  self._evaluate(node.right,
                                                                 **kwargs))
        elif isinstance(node, ast.UnaryOp):
            return self._operators[type(node.op)](self._evaluate(node.operand,
                                                                 **kwargs))
        elif isinstance(node, ast.Call):
            if node.func.id in kwargs:
                # evaluate arguments
                arg_eval = []
                for arg in node.args:
                    arg_eval.append(self._evaluate(arg, **kwargs))

                return kwargs[node.func.id].call(*arg_eval, **kwargs)
            else:
                raise KeyError('function "{}" not'
                               ' available'.format(node.func.id))
        else:
            raise TypeError(node)

    def _get_expr(self, node):
        # TODO: eliminate unnecessary parentheses
        if isinstance(node, ast.Expression):
            return self._get_expr(node.body)
        elif isinstance(node, ast.BinOp):
            left_expr = self._get_expr(node.left)
            right_expr = self._get_expr(node.right)

            return '({}{}{})'.format(left_expr,
                                     self._ast_op_names[node.op.__class__],
                                     right_expr)
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            arg_list = []
            for arg in node.args:
                arg_list.append(self._get_expr(arg))
            return '{}({})'.format(node.func.id,
                                   ','.join(arg_list))
        else:
            raise TypeError('invalid type: "{}"'.format(type(node)))

    def __repr__(self):
        """Get representation of expression."""
        return self._get_expr(self.tree)

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()

    @classmethod
    def _get_reverse_operator_mapping(cls):
        reverse_dict = {}
        for key, value in cls._ast_op_names.items():
            reverse_dict[value] = key

        return reverse_dict

    @classmethod
    def combine_expressions(cls, lhs, op, rhs):
        """Combine two expressions into a new BinOp.

        Args
        ----
        lhs: HDLExpression
           left-hand side operand
        op: str
           operation descriptor string
        rhs: HDLExpression
           right-hand side operand
        """
        if not isinstance(lhs, HDLExpression) or\
           not isinstance(rhs, HDLExpression):
            raise TypeError('can only combine two HDLExpression objects')

        # check operator?
        op_mapping = cls._get_reverse_operator_mapping()
        if op not in op_mapping:
            raise ValueError('illegal operator: "{}"'.format(op))

        new_op = ast.BinOp(left=copy.copy(lhs.tree),
                           op=op_mapping[op](),
                           right=copy.copy(rhs.tree))
        return HDLExpression(ast.Expression(body=new_op))

    def _new_binop(self, op, other, this_lhs=True):
        if isinstance(other, HDLExpression):
            rhs = other
        elif isinstance(other, HDLIntegerConstant):
            rhs = HDLExpression(other)
        elif isinstance(other, int):
            rhs = HDLExpression(other)
        else:
            raise TypeError('illegal type: "{}"'.format(type(rhs)))
        # create new BinOp
        if this_lhs is True:
            return self.combine_expressions(self, op, rhs)
        else:
            return self.combine_expressions(rhs, op, self)

    def __add__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('+', other)

    def __radd__(self, other):
        """Add expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('+', other, this_lhs=False)

    def __sub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('-', other)

    def __rsub__(self, other):
        """Subtract expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('-', other, this_lhs=False)

    def __mul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('*', other)

    def __rmul__(self, other):
        """Multiply expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as left-hand side
        """
        return self._new_binop('*', other, this_lhs=False)

    def __truediv__(self, other):
        """Divide expressions.

        Args
        ----
        other: HDLExpression, HDLIntegerConstant, int
           Value to be used as right-hand side
        """
        return self._new_binop('/', other)


class HDLConstant(HDLValue):
    """Abstract class from which other constants inherit."""

    pass


class HDLStringConstant(HDLConstant):
    """String constant value."""

    pass


class HDLIntegerConstant(HDLConstant):
    """A constant value."""

    def __init__(self, value):
        """Initialize.

        Args
        ----
        value: int
            A constant value
        """
        self.value = value

    def evaluate(self, **kwargs):
        """Evaluate."""
        return self.value

    def __repr__(self):
        """Get representation."""
        return str(self.value)

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()

    def __sub__(self, other):
        """Subtract two constants, return a new one.

        Args
        ----
        other: int or HDLIntegerConstant
           Other value
        """
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value - int(other))
        else:
            raise TypeError('can only subtract int and '
                            'HDLIntegerConstant types')

    def __abs__(self):
        """Return absolute value."""
        if self.value < 0:
            return HDLIntegerConstant(-self.value)
        else:
            return HDLIntegerConstant(self.value)

    def __int__(self):
        """Convert to integer."""
        return self.value

    def __add__(self, other):
        """Add two constants, return a new one.

        Args
        ----
        other: int, HDLIntegerConstant
           Other value to add
        """
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value + int(other))
        else:
            raise TypeError('can only add int and HDLIntegerConstant types')

    def __radd__(self, other):
        """Reverse add. Uses __add__."""
        return self.__add__(other)

    def __mul__(self, other):
        """Multiply two constants."""
        if isinstance(other, (int, HDLIntegerConstant)):
            return HDLIntegerConstant(self.value * int(other))
        else:
            raise TypeError('can only multiply int and'
                            ' HDLIntegerConstant types')

    def __eq__(self, other):
        """Equality test.

        Args
        ----
        other: int, HDLIntegerConstant
           Value to compare against
        """
        if isinstance(other, int):
            return bool(self.value == other)
        elif isinstance(other, HDLIntegerConstant):
            return bool(self.value == other.value)
        else:
            raise TypeError


class HDLVectorDescriptor(HDLObject):
    """Describe a vector signal."""

    def __init__(self, left_size, right_size=None, stored_value=None):
        """Initialize.

        Args
        ----
        left_size: int
           Size on the left of vector declaration
        right_size: int, NoneType
           Size on the right of vector declaration
        stored_value: int, NoneType
           A stored value
        """
        if not isinstance(left_size, (int, HDLExpression)):
            raise TypeError('only int or HDLExpression allowed as size')

        if not isinstance(right_size, (int, HDLExpression)):
            if right_size is None:
                # take this as zero
                right_size = 0
            else:
                raise TypeError('only int or HDLExpression allowed as size')

        if not isinstance(stored_value, (int, (type(None)))):
            raise TypeError('stored_value can only be int or None')

        # if integer, check bounds
        self._check_value(right_size)
        self._check_value(left_size)

        if isinstance(left_size, int):
            self.left_size = HDLIntegerConstant(left_size)
        else:
            self.left_size = left_size
        if isinstance(right_size, int):
            self.right_size = HDLIntegerConstant(right_size)
        else:
            self.right_size = right_size

        # check for value legality
        if stored_value is not None:
            if self.value_fits_width(len(self), stored_value) is True:
                self.stored_value = stored_value
            else:
                raise ValueError('vector cannot hold passed stored_value')

    def _check_value(self, value):
        if isinstance(value, int):
            if value < 0:
                raise ValueError('only positive values allowed for sizes')

    def evaluate_right(self, eval_scope={}):
        """Evaluate right side size."""
        return self.right_size.evaluate(**eval_scope)

    def evaluate_left(self, eval_scope={}):
        """Evaluate left side size."""
        return self.left_size.evaluate(**eval_scope)

    def evaluate(self, eval_scope={}):
        """Evaluate both sides."""
        return (self.evaluate_left(eval_scope),
                self.evaluate_right(eval_scope))

    def __len__(self):
        """Get vector length."""
        return abs(int(self.left_size) - int(self.right_size)) + 1

    def __repr__(self, eval_scope=None):
        """Represent."""
        if eval_scope is not None:
            left_size = self.evaluate_left(eval_scope)
            right_size = self.evaluate_right(eval_scope)
        else:
            left_size = self.left_size
            right_size = self.right_size
        return '[{}:{}]'.format(left_size, right_size)

    def dumps(self, eval_scope=None):
        """Dump description to string."""
        return self.__repr__(eval_scope)

    @staticmethod
    def value_fits_width(width, value):
        """Check if a value fits in a vector.

        Args
        ----
        width: int
           Bit Vector width
        value: int
           The value
        """
        return bool(value <= (int(math.pow(2, width)) - 1))


class HDLModuleParameter(HDLObject):
    """Module parameter / generic values."""

    def __init__(self, param_name, param_type, param_default=None):
        """Initialize.

        Args
        ----
        param_name: str
           Parameter name
        param_type: str
           Parameter type
        param_default: object
           Parameter value
        """
        self.name = param_name
        self.ptype = param_type
        self.value = param_default

    def __repr__(self):
        """Get readable representation."""
        if self.ptype is not None:
            ret_str = '#{} {}'.format(self.ptype.upper(),
                                      self.name.upper())
        else:
            ret_str = '#{}'.format(self.name.upper())
        if self.value is not None:
            ret_str += ' ({})'.format(self.value)

        return ret_str

    def dumps(self):
        """Alias for __repr__."""
        return self.__repr__()


class HDLModulePort(HDLObject):
    """HDL Module port."""

    _port_directions = ['in', 'out', 'inout']

    def __init__(self, direction, name, size=1):
        """Initialize.

        Args
        ----
        direction: str
           Port direction
        size: int, tuple or HDLVectorDescriptor
           Port description
        name: str
           Port name
        """
        if direction not in self._port_directions:
            raise ValueError('invalid port direction: "{}"'.format(direction))

        self.direction = direction
        self.name = name
        if isinstance(size, int):
            # default is [size-1:0] / (size-1 downto 0)
            if (size < 0):
                raise ValueError('only positive size allowed')
            self.vector = HDLVectorDescriptor(size-1, 0)
        elif isinstance(size, (tuple, list)):
            if len(size) != 2:
                raise ValueError('invalid vector '
                                 'dimensions: "{}"'.format(size))
            self.vector = HDLVectorDescriptor(*size)
        elif isinstance(size, HDLVectorDescriptor):
            self.vector = size
        else:
            raise TypeError('size can only be of types: int, list or'
                            ' HDLVectorDescriptor')

    def __repr__(self, eval_scope=None):
        """Get readable representation."""
        return '{} {}{}'.format(self.direction.upper(),
                                self.name,
                                self.vector.dumps(eval_scope))

    def dumps(self, eval_scope=None):
        """Alias for __repr__."""
        return self.__repr__(eval_scope)


class HDLModule(HDLObject):
    """HDL Module."""

    def __init__(self, module_name, ports=None, params=None):
        """Initialize.

        Args
        ----
        module_name: str
            Module or entity name
        ports: list
            List of ports in module declaration
        """
        self.name = module_name
        self.ports = []
        self.params = []
        if params is not None:
            self.add_parameters(params)
        if ports is not None:
            self.add_ports(ports)

    def add_ports(self, ports):
        """Add ports to module.

        Args
        ----
        ports: list or HDLModulePort
            List of ports to be added
        """
        # TODO: duplicate port verification
        if isinstance(ports, HDLModulePort):
            self.ports.append(ports)
        elif isinstance(ports, (tuple, list)):
            for port in ports:
                if not isinstance(port, HDLModulePort):
                    raise TypeError('list may only contain HDLModulePort'
                                    ' instances')
                self.ports.extend(ports)
        else:
            raise TypeError('ports must be a list or HDLModulePort')

    def add_parameters(self, params):
        """Add parameters to module.

        Args
        ----
        params: list or HDLModuleParameter
            List of parameters to be added.
        """
        # TODO: duplicate parameter verification
        if isinstance(params, HDLModuleParameter):
            self.params.append(params)
        elif isinstance(params, (tuple, list)):
            for param in params:
                if not isinstance(param, HDLModuleParameter):
                    raise TypeError('list may only contain HDLModuleParameter'
                                    ' instances')
                self.params.extend(params)
        else:
            raise TypeError('params must be a list or HDLModuleParameter')

    def get_parameter_scope(self):
        """Get parameters as dictionary."""
        scope = {}
        for param in self.params:
            scope[param.name] = param.value

        return scope

    def get_full_scope(self):
        """Get scope, including builtins."""
        scope = {}
        scope.update(self.get_parameter_scope())
        scope.update(HDLBuiltins.get_builtin_scope())
        return scope

    def __repr__(self, evaluate=False):
        """Get readable representation."""
        if evaluate is True:
            eval_scope = self.get_full_scope()
        else:
            eval_scope = None
        ret_str = '{} {{\n'.format(self.name.upper())

        for param in self.params:
            ret_str += '{}\n'.format(param.dumps())

        for port in self.ports:
            ret_str += '    {}\n'.format(port.dumps(eval_scope=eval_scope))

        ret_str += '}'
        return ret_str

    def dumps(self, evaluate=False):
        """Alias for __repr__."""
        return self.__repr__(evaluate)

    def get_param_names(self):
        """Return list of all parameters available."""
        return [x.name for x in self.params]

    def get_port_names(self):
        """Return list of all ports available."""
        return [x.name for x in self.ports]
