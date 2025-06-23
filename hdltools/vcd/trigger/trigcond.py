"""Trigger condition mini-language."""

import re
from importlib.resources import files
from textx.metamodel import metamodel_from_file
from scoff.ast.visits import ASTVisitor, VisitError
from hdltools.vcd.trigger import VCDTriggerDescriptor

METAMODEL_FILE = str(files("hdltools") / "vcd" / "trigger" / "trigcond.tx")
OBJDUMP_METAMODEL = metamodel_from_file(METAMODEL_FILE)


class TriggerConditionVisitor(ASTVisitor):
    """Trigger condition ast visitor."""

    def __init__(self):
        """Initialize."""
        super().__init__()
        self._conditions = []
        self._mode = None

    @staticmethod
    def get_slice_size(node):
        """Get slice size."""
        if hasattr(node, "right") and node.right is not None:
            return abs(node.left - node.right.val) + 1
        return 1

    @staticmethod
    def get_signal_size(node):
        """Get slice size."""
        if hasattr(node, "right") and node.right is not None:
            return abs(node.left - node.right.val) + 1
        return node.left

    def visit_VCDSignalName(self, node):
        """Visit VCD signal name (includes array notation like signal[15:0])."""
        return node
    
    def visit_RuntimeSlicedSignal(self, node):
        """Visit runtime sliced signal (legacy slicing syntax)."""
        return node
    
    def visit_TriggerCondition(self, node):
        """Visit trigger condition."""
        # Get signal name from either VCDSignalName or RuntimeSlicedSignal
        if hasattr(node.sig, 'name'):
            signal_full_name = node.sig.name
        else:
            # Should not happen with new grammar, but handle legacy case
            signal_full_name = str(node.sig)
        
        parts = signal_full_name.split("::")
        if len(parts) < 2:
            raise RuntimeError(f"Invalid signal path '{signal_full_name}': must use format 'scope::signal_name'")
        
        name = parts[-1]
        scope = "::".join(parts[:-1])
        
        # Validate scope and signal name are not empty
        if not scope.strip():
            raise RuntimeError(f"Empty scope in signal path '{signal_full_name}': scope::signal_name format required")
        if not name.strip():
            raise RuntimeError(f"Empty signal name in signal path '{signal_full_name}': scope::signal_name format required")
        # Check if this is a RuntimeSlicedSignal (has explicit slicing)
        is_runtime_sliced = hasattr(node.sig, "slice") and node.sig.slice is not None
        
        if is_runtime_sliced:
            # create pattern with many don't cares
            m = re.match(r"[01xX]+", node.value)
            if m is None:
                raise RuntimeError("only binary is supported if using slices")
            pattern_len = len(node.value)
            slice_len = self.get_slice_size(node.sig.slice)
            if pattern_len != slice_len:
                raise RuntimeError(
                    f"pattern length error: expected {slice_len}, got {pattern_len}"
                )
            pattern = ["x" for _ in range(self.get_signal_size(node.sig.size))]
            invert_bit_order = False
            if (
                hasattr(node.sig.slice, "right")
                and node.sig.slice.right is not None
            ):
                bits = range(node.sig.slice.right.val, node.sig.slice.left + 1)
                if node.sig.slice.right.val < node.sig.slice.left:
                    bits = list(
                        range(
                            node.sig.slice.right.val, node.sig.slice.left + 1
                        )
                    )
                    invert_bit_order = True
                else:
                    bits = list(
                        range(
                            node.sig.slice.left, node.sig.slice.right.val + 1
                        )
                    )
                for i in bits:
                    if invert_bit_order:
                        pattern[i] = node.value[len(node.value) - i - 1]
                    else:
                        pattern[i] = node.value[i]
            else:
                pattern[node.sig.slice.left] = node.value

            # respect bit order
            if (
                hasattr(node.sig.size, "right")
                and node.sig.size.right is not None
                and node.sig.size.right.val < node.sig.size.left
            ):
                pattern = pattern[::-1]

            # create pattern with x's
            pattern = "".join(pattern)
        else:
            pattern = node.value

        try:
            cond = VCDTriggerDescriptor(
                scope, name, pattern, negate=node.op == "!="
            )
            self._conditions.append(cond)
        except Exception as e:
            # Provide context about which condition failed
            condition_str = f"{scope}::{name}{node.op}{node.value}"
            raise RuntimeError(
                f"Error parsing trigger condition '{condition_str}': {e}\n"
                f"Hint: Check that the pattern value is in correct format."
            ) from e

    def visit_SignalDescriptor(self, node):
        """Visit signal descriptor - delegates to VCDSignalName or RuntimeSlicedSignal."""
        # The grammar now handles VCDSignalName and RuntimeSlicedSignal separately
        # This method should not be called with the new grammar
        return node

    def visit_ConditionRight(self, node):
        """Visit rhs of statement."""
        if self._mode is None:
            if node.op == "&&":
                self._mode = "&&"
            elif node.op == "=>":
                self._mode = "=>"
            else:
                raise RuntimeError("only && or => operators supported for now")
        else:
            if node.op != self._mode:
                raise RuntimeError("all operators must be homonegeous")

    def get_conditions(self):
        """Get conditions."""
        return self._conditions

    def get_mode(self):
        """Get operation mode."""
        return self._mode

    def visit(self, node):
        """Visit."""
        super().visit(node)
        # default mode
        if self._mode is None:
            self._mode = "&&"


def parse_trigcond(text):
    """Parse vecgen file."""
    model = OBJDUMP_METAMODEL.model_from_str(text)
    return model


def build_descriptors_from_str(cond):
    """Build list of trigger descriptors from string."""
    try:
        ast = parse_trigcond(cond)
        visitor = TriggerConditionVisitor()
        visitor.visit(ast)
        return (visitor.get_conditions(), visitor.get_mode())
    except Exception as e:
        # Provide comprehensive error information
        error_msg = f"Failed to parse trigger condition: '{cond}'\n"
        
        # Check for common syntax errors
        if '==' not in cond and '!=' not in cond:
            error_msg += "Error: Missing comparison operator. Use '==' or '!=' to compare values.\n"
            error_msg += "Example: 'cpu::state==0011' or 'reset!=1'\n"
        elif '::' not in cond:
            error_msg += "Error: Missing scope separator. Use '::' to separate scope and signal name.\n"
            error_msg += "Example: 'module_name::signal_name==value'\n"
        else:
            # Extract the pattern value to provide specific feedback
            parts = cond.split('==') if '==' in cond else cond.split('!=')
            if len(parts) == 2:
                pattern_value = parts[1].strip()
                error_msg += f"Error: Invalid pattern value '{pattern_value}'\n"
                
                # Check if it's a decimal number that should be binary
                if pattern_value.isdigit():
                    decimal_val = int(pattern_value)
                    binary_suggestion = bin(decimal_val)[2:]
                    error_msg += f"Hint: '{pattern_value}' appears to be decimal. Try '{binary_suggestion}' (binary)\n"
                elif any(c in pattern_value for c in '23456789'):
                    error_msg += "Hint: VCD patterns must be binary (0,1,x,X) or hex with 'h' suffix\n"
            
            error_msg += f"Original error: {e}\n"
        
        error_msg += "\nValid condition formats:\n"
        error_msg += "  • scope::signal==binary_pattern (e.g., 'cpu::state==0011')\n"
        error_msg += "  • scope::signal==hex_pattern (e.g., 'bus::addr==A000h')\n"
        error_msg += "  • scope::signal!=pattern (for negated conditions)\n"
        error_msg += "  • Multiple conditions with && or =>\n"
        
        raise RuntimeError(error_msg) from e
