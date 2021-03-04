"""HDL Primitives."""
import pytest
import ast

from hdltools.abshdl.vector import HDLVectorDescriptor
from hdltools.abshdl.module import HDLModule, HDLModuleParameter
from hdltools.abshdl.port import HDLModulePort
from hdltools.abshdl.expr import HDLExpression
from hdltools.abshdl.signal import HDLSignal, HDLSignalSlice
from hdltools.abshdl.const import HDLIntegerConstant, HDLStringConstant
from hdltools.abshdl.sens import HDLSensitivityList, HDLSensitivityDescriptor
from hdltools.abshdl.seq import HDLSequentialBlock
from hdltools.abshdl.assign import HDLAssignment
from hdltools.abshdl.concat import HDLConcatenation


def test_constants():
    """Test constants."""
    with pytest.raises(ValueError):
        fit_1 = HDLIntegerConstant(256, size=8)

    fit_1 = HDLIntegerConstant(255, size=8)
    fit_2 = HDLIntegerConstant(128, size=9)

    ret = 3 - fit_1
    ret = fit_1 - fit_2
    ret = fit_2 - fit_1
    ret = fit_1 + fit_2
    ret = 2 + fit_1
    ret = 2 * fit_1
    ret = fit_1 * 2

    with pytest.raises(TypeError):
        _ = HDLIntegerConstant(2) - "123"

    with pytest.raises(TypeError):
        _ = HDLIntegerConstant(2) + "123"

    with pytest.raises(TypeError):
        _ = HDLIntegerConstant(2) * 1.0

    ret = HDLIntegerConstant(2) == 2
    assert ret == True

    ret = HDLIntegerConstant(2) == "x"
    assert ret == False

    _ = abs(HDLIntegerConstant(-1))

    HDLStringConstant(value="some_value")


# test HDL primitives
def test_vector_descriptor():
    """Test vectors."""
    # basic testing
    vec = HDLVectorDescriptor(0, 0)
    print(vec.dumps())
    assert len(vec) == 1

    vec = HDLVectorDescriptor(7)

    # test failure modes
    with pytest.raises(ValueError):
        vec = HDLVectorDescriptor(-1, 0)

    with pytest.raises(TypeError):
        vec = HDLVectorDescriptor("1", 0)

    with pytest.raises(TypeError):
        vec = HDLVectorDescriptor(left_size=1, right_size="1")

    with pytest.raises(TypeError):
        vec = HDLVectorDescriptor(7, stored_value="a")

    vec = HDLVectorDescriptor(8, stored_value=256)
    left, right = vec.evaluate()

    with pytest.raises(ValueError):
        HDLVectorDescriptor(7, stored_value=256)


def test_module_port():
    """Test ports."""
    port = HDLModulePort("in", "myport", 3)
    port = HDLModulePort("out", "myport", (2, 0))
    port = HDLModulePort("inout", "myport", HDLVectorDescriptor(2, 0))

    # fail cases
    with pytest.raises(ValueError):
        HDLModulePort("unknown", "myport", 0)

    with pytest.raises(ValueError):
        HDLModulePort("in", "myport", -1)

    with pytest.raises(ValueError):
        HDLModulePort("in", "myport", (2, 3, 0))

    with pytest.raises(TypeError):
        HDLModulePort("in", "myport", "INVALID")


def test_hdl_parameter():
    """Test parameters."""
    param = HDLModuleParameter("myparam", "integer", param_default=0)
    print(param.dumps())


def test_hdl_module():
    """Test modules."""
    mod = HDLModule("my_module")
    mod = HDLModule("my_module", [HDLModulePort("in", "myport", 8)])
    mod = HDLModule(
        "my_module", params=[HDLModuleParameter("myparam", "integer", 0)]
    )

    expr = ast.parse("myparam-1", mode="eval")
    vec = HDLVectorDescriptor(left_size=HDLExpression(expr), right_size=0)
    mod = HDLModule(
        "my_module",
        ports=[HDLModulePort("in", "myport", vec)],
        params=HDLModuleParameter("myparam", "integer", 0),
    )
    print(mod.dumps(evaluate=True))

    _ = mod.get_parameter_scope()
    _ = mod.get_full_scope()
    _ = mod.get_param_names()
    _ = mod.get_port_names()

    # failures
    with pytest.raises(TypeError):
        mod = HDLModule("my_module", 0)

    with pytest.raises(TypeError):
        mod = HDLModule("my_module", [0])

    with pytest.raises(TypeError):
        mod = HDLModule("my_module", params=[0])

    with pytest.raises(TypeError):
        mod = HDLModule("my_module", params=0)


def test_hdl_expression():
    """Test expressions."""
    expr_1 = "PARAM-2"
    expr_2 = "PARAM_X+1"
    expr_3 = "a and ~b"
    hdl_expr_1 = HDLExpression(ast.parse(expr_1, mode="eval"))
    hdl_expr_2 = HDLExpression(ast.parse(expr_2, mode="eval"))
    hdl_expr_3 = HDLExpression(expr_3)
    print(hdl_expr_3.dumps())
    sum = hdl_expr_1 + hdl_expr_2
    neg = ~sum
    bool_neg = sum.bool_neg()
    bool_and = hdl_expr_1.bool_and(hdl_expr_2)
    bool_or = hdl_expr_1.bool_or(hdl_expr_2)
    print(sum.dumps())
    print(neg.dumps())
    print(bool_neg.dumps())
    print(bool_and.dumps())
    print(bool_or.dumps())

    _ = hdl_expr_1 & 0x1
    _ = 0x1 | hdl_expr_1
    _ = 0x1 & hdl_expr_1
    _ = 0x1 ^ hdl_expr_1
    _ = hdl_expr_1 ^ 0x1

    my_signal = HDLSignal("reg", "signal_a", size=2)
    _ = HDLExpression(HDLIntegerConstant(1))
    _ = HDLExpression(1)
    _ = HDLExpression(my_signal)
    _ = HDLExpression(HDLSignalSlice(my_signal, 1))
    _ = HDLExpression(my_signal[1:0])

    # test reduction
    expr_a = HDLExpression("value_a")
    expr_b = HDLExpression("value_b")
    full_expr = expr_a << 0 | expr_b << 16 | HDLExpression(0)

    case_1 = ast.BinOp(
        left=ast.Num(n=0), op=ast.BitOr(), right=ast.Name(id="VAR")
    )

    case_2 = ast.BinOp(
        left=ast.Num(n=1), op=ast.Mult(), right=ast.Name(id="VAR")
    )

    case_3 = ast.BinOp(
        left=ast.Num(n=0), op=ast.Mult(), right=ast.Name(id="VAR")
    )

    hdl_expr = HDLExpression(ast.Expression(body=case_1))
    hdl_expr_2 = HDLExpression(ast.Expression(body=case_2))
    hdl_expr_3 = HDLExpression(ast.Expression(body=case_3))
    print(hdl_expr.dumps())
    print(hdl_expr_2.dumps())

    reduced_1 = HDLExpression._reduce_binop(case_1)
    hdl_expr = HDLExpression(ast.Expression(body=reduced_1))
    print(hdl_expr.dumps())

    reduced_2 = HDLExpression._reduce_binop(case_2)
    hdl_expr_2 = HDLExpression(ast.Expression(body=reduced_2))
    print(hdl_expr_2.dumps())

    reduced_3 = HDLExpression._reduce_binop(case_3)
    hdl_expr_3 = HDLExpression(ast.Expression(body=reduced_3))
    print(hdl_expr_3.dumps())

    print(full_expr.dumps())
    full_expr.reduce_expr()
    print(full_expr.dumps())


def test_hdl_signal():
    """Test signals."""
    my_sig = HDLSignal("reg", "signal_x", size=(7, 0))
    print(my_sig.dumps())
    _ = my_sig[3:1]
    _ = my_sig[7]
    yet_another = my_sig[2:]
    _ = my_sig[:2]
    print(yet_another.dumps())
    _ = HDLSignal("reg", "sig", HDLVectorDescriptor(1, 0))

    # exceptions
    with pytest.raises(ValueError):
        _ = HDLSignal("unknown", "sig", 1)

    with pytest.raises(ValueError):
        _ = HDLSignal("reg", "sig", -1)

    with pytest.raises(ValueError):
        _ = HDLSignal("reg", "sig", (1, 2, 3))

    with pytest.raises(TypeError):
        _ = HDLSignal("reg", "sig", "invalid")

    _ = HDLSignalSlice(my_sig, HDLVectorDescriptor(1, 0))

    with pytest.raises(TypeError):
        _ = HDLSignalSlice(my_sig, "invalid")


def test_sens():
    """Test sensitivity list."""
    some_signal = HDLSignal("reg", "signal", size=1)
    sens_1 = HDLSensitivityDescriptor(sens_type="rise", sig=some_signal)

    sens_list = HDLSensitivityList()
    sens_list.add(sens_1)

    print(sens_list.dumps())


def test_seq():
    """Test sequential block."""
    some_signal = HDLSignal("reg", "signal", size=1)
    sens_1 = HDLSensitivityDescriptor(sens_type="rise", sig=some_signal)

    sens_list = HDLSensitivityList()
    sens_list.add(sens_1)

    ass_sig = HDLSignal("reg", "counter", size=2)
    ass_expr = HDLExpression(ass_sig) + 1
    assign = HDLAssignment(ass_sig, ass_expr)

    seq = HDLSequentialBlock(sens_list)
    seq.add(assign)

    print(seq.dumps())


def test_assign():
    """Test assignment."""
    # this module is extensively tested already, being used as a support
    # class for many others. here we test whatever is missing

    sig = HDLSignal("comb", "my_signal")
    assign = HDLAssignment(signal=sig, value=0)
    print(assign.dumps())

    # test fail cases
    with pytest.raises(TypeError):
        _ = HDLAssignment("not_allowed", 0)


def test_concat():
    """Test concatenation."""
    sig = HDLSignal("comb", "my_signal", size=4)
    concat = HDLConcatenation(sig, HDLExpression(0x0C, size=8))
    assert len(concat) == 12

    concat.append(HDLExpression(0x1, size=1))

    # failures
    with pytest.raises(TypeError):
        _ = HDLConcatenation(sig, "not_allowed")
