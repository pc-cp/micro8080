
import sys
sys.path.append("../src")
from utils import HalfAdder, FullAdder, NBitAdderWithCarryOut, NBitAdderWithOverflow, int_to_8bit_list, bit_list_to_int

def test_half_adder():
    """
    Test the physical logic of a Half Adder.
    It takes 2 inputs and produces a Sum and a Carry-Out.
    """
    my_half_adder = HalfAdder() # Note: HalfAdder in utils.py doesn't take nin in __init__
    
    # 0 + 0 = 0 (Carry 0)
    carry, sum_out = my_half_adder([0, 0])
    assert carry == 0 and sum_out == 0, "Hardware failure: 0+0 should result in Sum 0, Carry 0"

    # 0 + 1 = 1 (Carry 0)
    carry, sum_out = my_half_adder([0, 1])
    assert carry == 0 and sum_out == 1, "Hardware failure: 0+1 should result in Sum 1, Carry 0"

    # 1 + 0 = 1 (Carry 0)
    carry, sum_out = my_half_adder([1, 0])
    assert carry == 0 and sum_out == 1, "Hardware failure: 1+0 should result in Sum 1, Carry 0"

    # 1 + 1 = 0 (Carry 1)
    carry, sum_out = my_half_adder([1, 1])
    assert carry == 1 and sum_out == 0, "Hardware failure: 1+1 should result in Sum 0, Carry 1 (Overflow)"

def test_full_adder():
    """
    Test the physical logic of a Full Adder.
    It takes 3 inputs [Carry-In, A, B] and produces a Sum and a Carry-Out.
    """
    my_full_adder = FullAdder()
    
    # Truth table coverage:
    # [Cin, A, B] -> (Cout, Sum)
    test_cases = [
        ([0, 0, 0], (0, 0)),
        ([0, 0, 1], (0, 1)),
        ([0, 1, 0], (0, 1)),
        ([0, 1, 1], (1, 0)),
        ([1, 0, 0], (0, 1)),
        ([1, 0, 1], (1, 0)),
        ([1, 1, 0], (1, 0)),
        ([1, 1, 1], (1, 1)),
    ]
    
    for inputs, expected in test_cases:
        res_carry, res_sum = my_full_adder(inputs)
        assert (res_carry, res_sum) == expected, f"Hardware failure at inputs {inputs}: expected {expected}, got {(res_carry, res_sum)}"

def test_NBitAdderWithCarryOut_ripple_stress():
    """
    STRESS TEST: The Ripple Carry Effect.
    Adding 1 to a sequence of 1s (e.g., 255 + 1) must ripple the carry 
    through every single bit until the final Carry-Out is 1.
    """
    nbits = 8
    adder = NBitAdderWithCarryOut(nbits)
    
    # 255 (11111111) + 1 (00000001)
    x = [1] * nbits
    y = [0] * (nbits - 1) + [1]
    
    final_carry, sums = adder(x, y)
    
    assert sums == [0] * nbits, "Ripple failed: All bits should have flipped to 0"
    assert final_carry == 1, "Ripple failed: Carry did not propagate to the final bit"

def test_NBitAdderWithCarryOut_unsigned_math():
    """Test standard unsigned addition using bit lists."""
    adder = NBitAdderWithCarryOut(8)
    
    # 123 + 45 = 168
    x = int_to_8bit_list(123)
    y = int_to_8bit_list(45)
    
    carry, sums = adder(x, y)
    result = bit_list_to_int(sums, signed=False)
    
    assert result == 168, f"Math failure: 123 + 45 should be 168, got {result}"
    assert carry == 0

def test_NBitAdderWithCarryOut_with_two_complement_signed():
    """
    Test signed arithmetic and overflow detection using Two's Complement.
    """
    nbits = 8
    adder = NBitAdderWithOverflow(nbits)
    
    # Case 1: Standard negative addition: -5 + 10 = 5
    # -5 in 8-bit Two's Complement: 11111011
    x = int_to_8bit_list(-5)
    y = int_to_8bit_list(10)
    
    overflow, sums = adder(x, y)
    result = bit_list_to_int(sums, signed=True)
    
    assert result == 5, f"Two's Complement failure: -5 + 10 = 5, got {result}"
    assert overflow == 0, "There should be no signed overflow here"

    # Case 2: Signed Overflow (Positive + Positive = Negative)
    # Max positive 8-bit signed is 127. 127 + 1 = 128 (which overflows to -128)
    x = int_to_8bit_list(127)
    y = int_to_8bit_list(1)
    
    overflow, sums = adder(x, y)
    result = bit_list_to_int(sums, signed=True)
    
    assert overflow == 1, "Hardware failure: 127 + 1 should trigger a signed overflow bit"
    assert result == -128, f"Expected overflow result -128, got {result}"

    # Case 3: Signed Overflow (Negative + Negative = Positive)
    # -128 + (-1) = -129 (which overflows to +127)
    x = int_to_8bit_list(-128)
    y = int_to_8bit_list(-1)
    
    overflow, sums = adder(x, y)
    result = bit_list_to_int(sums, signed=True)
    
    assert overflow == 1, "Hardware failure: -128 + -1 should trigger a signed overflow bit"
    assert result == 127, f"Expected overflow result 127, got {result}"
