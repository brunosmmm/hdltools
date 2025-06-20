"""Generate VHDL code."""

import math
from scoff.codegen import indent
from hdltools.abshdl.codegen import HDLCodeGenerator


class VHDLCodeGenerator(HDLCodeGenerator):
    """Generate VHDL code."""

    VHDL_PORT_DIRECTION = ["in", "out", "inout"]
    VHDL_SIGNAL_TYPE = ["signal"]

    def gen_HDLModulePort(self, element, **kwargs):
        """Generate ports."""
        if "evaluate" in kwargs:
            evaluate = kwargs["evaluate"]
        else:
            evaluate = False

        if element.direction == "in":
            port_direction = "in"
        elif element.direction == "out":
            port_direction = "out"
        elif element.direction == "inout":
            port_direction = "inout"
        else:
            raise ValueError("invalid port type: {}".format(element.direction))

        # Determine port type based on vector size
        if element.vector is None:
            port_type = "std_logic"
            ext_str = ""
        else:
            # Check if this is a single bit (size 1) or multi-bit vector
            try:
                if hasattr(element.vector, 'left_size') and hasattr(element.vector, 'right_size'):
                    # Evaluate the vector size
                    left_val = element.vector.left_size.evaluate() if element.vector.left_size else 0
                    right_val = element.vector.right_size.evaluate() if element.vector.right_size else 0
                    size = abs(left_val - right_val) + 1
                    
                    if size == 1:
                        port_type = "std_logic"
                        ext_str = ""
                    else:
                        port_type = "std_logic_vector"
                        ext_str = self.dump_element(element.vector, evaluate=evaluate)
                else:
                    # Fallback to vector notation
                    port_type = "std_logic_vector"
                    ext_str = self.dump_element(element.vector, evaluate=evaluate)
            except:
                # If we can't determine the size, assume it's a vector
                port_type = "std_logic_vector"
                ext_str = self.dump_element(element.vector, evaluate=evaluate)

        if "last" in kwargs:
            last = kwargs.pop("last")
        else:
            last = False

        ret_str = "{} : {} {}{}".format(
            element.name, port_direction, port_type, ext_str
        )

        if last is False:
            ret_str += ";"

        return ret_str

    def gen_HDLMacro(self, element, **kwargs):
        """Generate constants."""
        value = self.dump_element(element.value, **kwargs)

        if "const_type" in kwargs:
            const_type = kwargs.pop("const_type")
        else:
            # integer by default
            const_type = "integer"

        ret_str = "constant {} : {} := {};".format(
            element.name, const_type, value
        )
        return ret_str

    def gen_HDLConcatenation(self, element, **kwargs):
        """Concatenations."""
        ret_str = "({})".format(
            ",".join([self.dump_element(x) for x in element.items])
        )
        return ret_str

    def gen_HDLSwitch(self, element, **kwargs):
        """Switch / case."""
        ret_str = "case {} is\n".format(
            self.dump_element(element.switch, evaluate=False)
        )

        for name, case in element.cases.items():
            ret_str += self.dump_element(case, evaluate=False)

        ret_str += "\nend case;"
        return ret_str

    def gen_HDLCase(self, element, **kwargs):
        """Case."""
        ret_str = "when {} =>".format(
            self.dump_element(element.case_value, format="int")
        )
        ret_str += self.dump_element(element.scope)
        return ret_str

    def gen_HDLModule(self, element, **kwargs):
        """Generate module."""
        ret_str = ""
        for constant in element.constants:
            ret_str += self.dump_element(constant) + "\n"
        ret_str += "entity {} is\n".format(element.name)
        if len(element.params) > 0:
            ret_str += "generic("
            ret_str += ";\n".join(
                [self.dump_element(p, last=True) for p in element.params]
            )
            ret_str += ");"
        if len(element.ports) > 0:
            ret_str += "port("
            ret_str += ";\n".join(
                [self.dump_element(p, last=True) for p in element.ports]
            )
            ret_str += ");"

        ret_str += "end {};\n".format(element.name)

        if "arch_name" in kwargs:
            arch_name = kwargs.pop("arch_name")
        else:
            arch_name = "DEFAULT"

        ret_str += "architecture {} of {} is\n".format(arch_name, element.name)
        
        # Collect and generate signal declarations
        signals = self._collect_signals(element.scope)
        for signal in signals:
            ret_str += self.dump_element(signal, declaration_only=True) + "\n"
        
        ret_str += "begin\n"
        ret_str += self.dump_element(element.scope)
        ret_str += "end {};\n".format(arch_name)
        return ret_str

    def _collect_signals(self, scope):
        """Collect all signal declarations from scope recursively."""
        signals = []
        if hasattr(scope, 'statements'):
            for stmt in scope.statements:
                if hasattr(stmt, '__class__') and 'HDLSignal' in str(stmt.__class__):
                    signals.append(stmt)
                elif hasattr(stmt, 'scope'):
                    signals.extend(self._collect_signals(stmt.scope))
                elif hasattr(stmt, 'if_scope'):
                    signals.extend(self._collect_signals(stmt.if_scope))
                    if hasattr(stmt, 'else_scope') and stmt.else_scope is not None:
                        signals.extend(self._collect_signals(stmt.else_scope))
        return signals

    def gen_HDLComment(self, element, **kwargs):
        """Generate comment."""
        return "--{}".format(element.text)

    def gen_HDLMultiLineComment(self, element, **kwargs):
        """Generate multi-line comments."""
        return "\n".join(
            ["--{}".format(line) for line in element.text.split("\n")]
        )

    def gen_HDLIntegerConstant(self, element, **kwargs):
        """Generate an integer constant."""
        if "format" in kwargs:
            fmt = kwargs["format"]
            if fmt == "hex":
                return 'x"{:x}"'.format(element.evaluate())
            elif fmt == "bin":
                return 'b"{:b}"'.format(element.evaluate()) 
            elif fmt == "int":
                return str(element.evaluate())
        
        # Default decimal format
        return str(element.evaluate())

    def gen_HDLSignal(self, element, **kwargs):
        """Generate signal declarations."""
        # Check if this is being called for declaration only
        declaration_only = kwargs.get("declaration_only", False)
        
        # Determine VHDL signal type
        if element.sig_type == "comb":
            st = "signal"
        elif element.sig_type == "reg":
            st = "signal"  # VHDL uses signals for both
        elif element.sig_type == "const":
            st = "constant"
        elif element.sig_type == "var":
            st = "variable"
        else:
            st = "signal"  # Default

        # Determine signal data type
        if element.vector is None:
            signal_type = "std_logic"
        else:
            try:
                if hasattr(element.vector, 'left_size') and hasattr(element.vector, 'right_size'):
                    # Evaluate the vector size
                    left_val = element.vector.left_size.evaluate() if element.vector.left_size else 0
                    right_val = element.vector.right_size.evaluate() if element.vector.right_size else 0
                    size = abs(left_val - right_val) + 1
                    
                    if size == 1:
                        signal_type = "std_logic"
                    else:
                        signal_type = "std_logic_vector{}".format(
                            self.dump_element(element.vector, evaluate=False)
                        )
                else:
                    signal_type = "std_logic_vector{}".format(
                        self.dump_element(element.vector, evaluate=False)
                    )
            except:
                signal_type = "std_logic_vector{}".format(
                    self.dump_element(element.vector, evaluate=False)
                )

        # For declaration context, include initialization
        if declaration_only:
            init_value = ""
            if hasattr(element, 'init_value') and element.init_value is not None:
                init_value = " := {}".format(self.dump_element(element.init_value))
            return "{} {} : {}{};".format(st, element.name, signal_type, init_value)
        else:
            # For expression context, just return the signal name
            return element.name

    def gen_HDLSignalSlice(self, element, **kwargs):
        """Generate signal slicing."""
        sig_name = self.dump_element(element.signal, evaluate=False)
        
        if element.range_high is not None and element.range_low is not None:
            # Range slice: signal(high downto low)
            high = self.dump_element(element.range_high, evaluate=False)
            low = self.dump_element(element.range_low, evaluate=False)
            return "{}({} downto {})".format(sig_name, high, low)
        elif element.index is not None:
            # Single bit: signal(index)
            idx = self.dump_element(element.index, evaluate=False)
            return "{}({})".format(sig_name, idx)
        else:
            return sig_name

    def gen_HDLVectorDescriptor(self, element, **kwargs):
        """Generate vector range descriptors."""
        if "evaluate" in kwargs:
            evaluate = kwargs["evaluate"]
        else:
            evaluate = True

        if element.left_size is not None and element.right_size is not None:
            if evaluate:
                left_val = element.left_size.evaluate()
                right_val = element.right_size.evaluate()
            else:
                left_val = self.dump_element(element.left_size, evaluate=False)
                right_val = self.dump_element(element.right_size, evaluate=False)
            return "({} downto {})".format(left_val, right_val)
        else:
            return ""

    def gen_HDLAssignment(self, element, **kwargs):
        """Generate signal assignments."""
        # For assignments, we just want the signal name, not its declaration
        if hasattr(element.signal, 'name'):
            target = element.signal.name
        else:
            target = self.dump_element(element.signal, evaluate=False)
        
        source = self.dump_element(element.value, evaluate=False)
        
        # Determine assignment type based on signal type
        if hasattr(element.signal, 'sig_type'):
            if element.signal.sig_type == "var":
                return "{} := {};".format(target, source)  # Variable assignment
            else:
                return "{} <= {};".format(target, source)  # Signal assignment
        elif hasattr(element, 'assign_type'):
            if element.assign_type == "blocking":
                return "{} := {};".format(target, source)  # Variable assignment
            else:
                return "{} <= {};".format(target, source)  # Signal assignment
        
        # Default to signal assignment
        return "{} <= {};".format(target, source)

    def gen_HDLExpression(self, element, **kwargs):
        """Generate expressions."""
        # Handle format for evaluation
        if "format" in kwargs:
            fmt = kwargs.pop("format")
            if fmt == "int":
                try:
                    return str(element.evaluate())
                except:
                    # Couldn't evaluate, continue with normal processing
                    pass
        
        # Get the expression string and convert operators to VHDL
        expr_str = element.dumps()
        
        # Convert Verilog/C-style operators to VHDL (order matters!)
        vhdl_expr = expr_str
        vhdl_expr = vhdl_expr.replace("&&", " and ")
        vhdl_expr = vhdl_expr.replace("||", " or ")
        vhdl_expr = vhdl_expr.replace("!=", "/=")  # Must come before ! replacement
        vhdl_expr = vhdl_expr.replace("==", "=")
        vhdl_expr = vhdl_expr.replace("!", "not ")
        vhdl_expr = vhdl_expr.replace("=<", "<=")  # Fix from Verilog generator
        vhdl_expr = vhdl_expr.replace("&", " and ")
        vhdl_expr = vhdl_expr.replace("|", " or ")
        vhdl_expr = vhdl_expr.replace("^", " xor ")
        
        return vhdl_expr

    def gen_HDLModuleParameter(self, element, **kwargs):
        """Generate generic parameters."""
        param_type = "integer"  # Default type
        if "param_type" in kwargs:
            param_type = kwargs.pop("param_type")
        
        if element.value is not None:
            value = self.dump_element(element.value, **kwargs)
            return "{} : {} := {}".format(element.name, param_type, value)
        else:
            return "{} : {}".format(element.name, param_type)

    def gen_HDLIfElse(self, element, **kwargs):
        """Generate if-else statements."""
        condition = self.dump_element(element.condition, evaluate=False)
        ret_str = "if {} then\n".format(condition)
        # Manually indent each line
        if_code = self.dump_element(element.if_scope)
        ret_str += "\n".join(["  " + line if line.strip() else line for line in if_code.split("\n")])
        
        if element.else_scope is not None and len(element.else_scope) > 0:
            ret_str += "\nelse\n"
            else_code = self.dump_element(element.else_scope)
            ret_str += "\n".join(["  " + line if line.strip() else line for line in else_code.split("\n")])
        
        ret_str += "\nend if;"
        return ret_str

    def gen_HDLIfExp(self, element, **kwargs):
        """Generate conditional expressions."""
        condition = self.dump_element(element.condition, evaluate=False)
        
        # Handle signal names properly in conditional expressions
        def get_signal_name(value):
            if hasattr(value, 'name'):
                return value.name
            elif isinstance(value, str):
                return value  # Already a string, use as-is (no quotes for signal names)
            else:
                result = self.dump_element(value, evaluate=False, signal_context=True)
                # Remove quotes if they were added for signal names
                if isinstance(result, str) and result.startswith('"') and result.endswith('"'):
                    return result[1:-1]
                return result
        
        if_expr = get_signal_name(element.if_value)
        else_expr = get_signal_name(element.else_value)
        
        # VHDL conditional assignment
        return "{} when {} else {}".format(if_expr, condition, else_expr)

    def gen_HDLScope(self, element, **kwargs):
        """Generate scopes (statement blocks)."""
        ret_str = ""
        for stmt in element.statements:
            # Skip signal declarations at this level - they're handled in architecture
            if hasattr(stmt, '__class__') and 'HDLSignal' in str(stmt.__class__):
                continue
            
            stmt_code = self.dump_element(stmt, **kwargs)
            if stmt_code:
                ret_str += stmt_code + "\n"
        return ret_str

    def gen_HDLSensitivityDescriptor(self, element, **kwargs):
        """Generate sensitivity list descriptors."""
        # Force signal to be treated as just a name in sensitivity context
        if hasattr(element.signal, 'name'):
            signal_name = element.signal.name
        else:
            signal_name = self.dump_element(element.signal, evaluate=False)
        
        # In VHDL sensitivity lists, we can only use signal names
        # Edge detection must be done inside the process
        return signal_name

    def gen_HDLSensitivityList(self, element, **kwargs):
        """Generate complete sensitivity lists."""
        sensitivities = []
        for sens in element.items:
            sensitivities.append(self.dump_element(sens, **kwargs))
        return "({})".format(", ".join(sensitivities))

    def gen_HDLSequentialBlock(self, element, **kwargs):
        """Generate process blocks."""
        ret_str = ""
        
        # Generate process with sensitivity list
        if hasattr(element, 'sens_list') and element.sens_list:
            sens_list = self.dump_element(element.sens_list, **kwargs)
            ret_str += "process {}\n".format(sens_list)
        else:
            ret_str += "process\n"
        
        # Add variable declarations if any
        if hasattr(element, 'variables') and element.variables:
            for var in element.variables:
                ret_str += "  variable {};\n".format(self.dump_element(var))
        
        ret_str += "begin\n"
        
        # Check if this is a clocked process that needs edge detection
        has_edge_sensitivity = False
        if hasattr(element, 'sens_list') and element.sens_list:
            for sens in element.sens_list.items:
                if sens.sens_type in ['rise', 'fall']:
                    has_edge_sensitivity = True
                    clock_signal = sens.signal.name if hasattr(sens.signal, 'name') else str(sens.signal)
                    edge_func = "rising_edge" if sens.sens_type == "rise" else "falling_edge"
                    ret_str += "  if {}({}) then\n".format(edge_func, clock_signal)
                    break
        
        # Manually indent each line
        scope_code = self.dump_element(element.scope)
        indent_level = "    " if has_edge_sensitivity else "  "
        ret_str += "\n".join([indent_level + line if line.strip() else line for line in scope_code.split("\n")])
        
        if has_edge_sensitivity:
            ret_str += "\n  end if;"
        
        ret_str += "\nend process;"
        
        return ret_str

    def gen_HDLInstanceStatement(self, element, **kwargs):
        """Generate component instantiation statements."""
        ret_str = "{} : {}".format(element.instance_name, element.module_name)
        
        # Generic map
        if hasattr(element, 'generic_map') and element.generic_map:
            generic_assignments = []
            for param, value in element.generic_map.items():
                value_str = self.dump_element(value, evaluate=False)
                generic_assignments.append("{} => {}".format(param, value_str))
            ret_str += "\n  generic map (\n"
            ret_str += ",\n".join(["    " + g for g in generic_assignments])
            ret_str += "\n  )"
        
        # Port map
        if hasattr(element, 'port_map') and element.port_map:
            port_assignments = []
            for port, signal in element.port_map.items():
                signal_str = self.dump_element(signal, evaluate=False)
                port_assignments.append("{} => {}".format(port, signal_str))
            ret_str += "\n  port map (\n"
            ret_str += ",\n".join(["    " + p for p in port_assignments])
            ret_str += "\n  );"
        else:
            ret_str += ";"
        
        return ret_str

    def gen_HDLInstance(self, element, **kwargs):
        """Generate instance (alias for HDLInstanceStatement)."""
        return self.gen_HDLInstanceStatement(element, **kwargs)

    def gen_HDLForLoop(self, element, **kwargs):
        """Generate for loops."""
        loop_var = element.loop_variable
        start_val = self.dump_element(element.start_value, evaluate=False)
        end_val = self.dump_element(element.end_value, evaluate=False)
        
        ret_str = "for {} in {} to {} loop\n".format(loop_var, start_val, end_val)
        # Manually indent each line
        scope_code = self.dump_element(element.scope)
        ret_str += "\n".join(["  " + line if line.strip() else line for line in scope_code.split("\n")])
        ret_str += "\nend loop;"
        
        return ret_str

    def gen_HDLMacroValue(self, element, **kwargs):
        """Generate macro value references."""
        return element.name

    def gen_str(self, element, **kwargs):
        """Generate string literals."""
        # Check if this string is actually a signal name in quotes
        # Signal names shouldn't be quoted in VHDL identifiers
        if kwargs.get("signal_context", False):
            return element  # Just return the name without quotes
        return '"{}"'.format(element)

    def gen_HDLStringConstant(self, element, **kwargs):
        """Generate string constants."""
        return '"{}"'.format(element.value)

    # Helper methods for cleaner code generation
    @staticmethod
    def dumps_vector(value, width, base="dec"):
        """Format vector values in VHDL notation."""
        if base == "hex":
            return 'x"{:0{}x}"'.format(value, (width + 3) // 4)
        elif base == "bin":
            return 'b"{:0{}b}"'.format(value, width)
        elif base == "oct":
            return 'o"{:0{}o}"'.format(value, (width + 2) // 3)
        else:
            # Decimal or default
            return str(value)

    @staticmethod
    def dumps_generic(name, param_type="integer", value=None):
        """Format generic parameter declarations."""
        if value is not None:
            return "{} : {} := {}".format(name, param_type, value)
        else:
            return "{} : {}".format(name, param_type)

    @staticmethod
    def dumps_port(direction, name, signal_type, last=False):
        """Format port declarations."""
        ret_str = "{} : {} {}".format(name, direction, signal_type)
        if not last:
            ret_str += ";"
        return ret_str

    @staticmethod
    def dumps_signal(name, signal_type, init_value=None):
        """Format signal declarations."""
        if init_value is not None:
            return "signal {} : {} := {};".format(name, signal_type, init_value)
        else:
            return "signal {} : {};".format(name, signal_type)
