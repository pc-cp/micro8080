
import sys
sys.path.append("../src")
from utils import AND, OR, Inverter, NAND, NOR, XOR

def test_and_gate():
    """AND logic: 1 only when both inputs are 1."""
    my_and = AND(2)
    assert my_and([0, 0]) == 0
    assert my_and([0, 1]) == 0
    assert my_and([1, 0]) == 0
    assert my_and([1, 1]) == 1

def test_or_gate():
    """OR logic: 1 when at least one input is 1."""
    my_or = OR(2)
    assert my_or([0, 0]) == 0
    assert my_or([0, 1]) == 1
    assert my_or([1, 0]) == 1
    assert my_or([1, 1]) == 1

def test_inverter_gate():
    """Inverter (NOT) logic: Flips the input bit."""
    my_invert = Inverter()
    assert my_invert([0]) == 1
    assert my_invert([1]) == 0

def test_nand_gate():
    """NAND logic: 0 only when both inputs are 1 (All combinations: [0,0], [0,1], [1,0], [1,1])."""
    my_nand = NAND(2)
    assert my_nand([0, 0]) == 1
    assert my_nand([0, 1]) == 1
    assert my_nand([1, 0]) == 1
    assert my_nand([1, 1]) == 0

def test_nor_gate():
    """NOR logic: 1 only when both inputs are 0 (All combinations: [0,0], [0,1], [1,0], [1,1])."""
    my_nor = NOR(2)
    assert my_nor([0, 0]) == 1
    assert my_nor([0, 1]) == 0
    assert my_nor([1, 0]) == 0
    assert my_nor([1, 1]) == 0

def test_xor_gate():
    """XOR logic: 1 when inputs are different (All combinations: [0,0], [0,1], [1,0], [1,1])."""
    my_xor = XOR()
    assert my_xor([0, 0]) == 0
    assert my_xor([0, 1]) == 1
    assert my_xor([1, 0]) == 1
    assert my_xor([1, 1]) == 0
