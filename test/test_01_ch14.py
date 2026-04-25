from src.utils import *

# 14_full_adder.py
def test_and_gate():
    """Test the 2-input AND gate truth table."""
    my_and = AND(nin=2)
    assert my_and([0, 0]) == 0
    assert my_and([0, 1]) == 0
    assert my_and([1, 0]) == 0
    assert my_and([1, 1]) == 1

def test_or_gate():
    """Test the 2-input OR gate truth table."""
    my_or = OR(nin=2)
    assert my_or([0, 0]) == 0
    assert my_or([0, 1]) == 1
    assert my_or([1, 0]) == 1
    assert my_or([1, 1]) == 1

def test_inverter_gate():
    """Test the Inverter (NOT gate) truth table."""
    my_inverter = Inverter()
    assert my_inverter([0]) == 1
    assert my_inverter([1]) == 0

def test_nand_gate():
    """Test the 2-input NAND gate truth table."""
    my_nand = NAND(nin=2)
    assert my_nand([0, 0]) == 1
    assert my_nand([0, 1]) == 1
    assert my_nand([1, 0]) == 1
    assert my_nand([1, 1]) == 0

def test_nor_gate():
    """Test the 2-input NOR gate truth table."""
    my_nor = NOR(nin=2)
    assert my_nor([0, 0]) == 1
    assert my_nor([0, 1]) == 0
    assert my_nor([1, 0]) == 0
    assert my_nor([1, 1]) == 0

def test_xor_gate():
    """Test the 2-input XOR gate truth table."""
    my_xor = XOR()
    assert my_xor([0, 0]) == 0
    assert my_xor([0, 1]) == 1
    assert my_xor([1, 0]) == 1
    assert my_xor([1, 1]) == 0

def test_half_adder():
    my_halfadder = HalfAdder()
    # return (carry, sum)
    assert my_halfadder([0, 0]) == (0, 0)
    assert my_halfadder([0, 1]) == (0, 1)
    assert my_halfadder([1, 0]) == (0, 1)
    assert my_halfadder([1, 1]) == (1, 0)

def test_full_adder():
    my_fulladder = FullAdder()
    # accept (carry_in, x, y), return (carry_out, sum)
    assert my_fulladder([0, 0, 0]) == (0, 0)
    assert my_fulladder([0, 0, 1]) == (0, 1)
    assert my_fulladder([0, 1, 0]) == (0, 1)
    assert my_fulladder([0, 1, 1]) == (1, 0)
    assert my_fulladder([1, 0, 0]) == (0, 1)
    assert my_fulladder([1, 0, 1]) == (1, 0)
    assert my_fulladder([1, 1, 0]) == (1, 0)
    assert my_fulladder([1, 1, 1]) == (1, 1)

def test_1bit_addition():
    my_fulladder_1bit = NBitAdderWithCarryOut(1)
    # The __call__ method expects: (x_list, y_list, carry_in_int)
    # It returns: (carry_out_int, sum_list)
    # 0 + 0
    assert my_fulladder_1bit([0], [0], 0) == (0, [0]), "Failed on 0 + 0 + 0"
    assert my_fulladder_1bit([0], [0], 1) == (0, [1]), "Failed on 0 + 0 + 1"
    # 0 + 1
    assert my_fulladder_1bit([0], [1], 0) == (0, [1]), "Failed on 0 + 1 + 0"
    assert my_fulladder_1bit([0], [1], 1) == (1, [0]), "Failed on 0 + 1 + 1"
    # 1 + 0
    assert my_fulladder_1bit([1], [0], 0) == (0, [1]), "Failed on 1 + 0 + 0"
    assert my_fulladder_1bit([1], [0], 1) == (1, [0]), "Failed on 1 + 0 + 1"
    # 1 + 1
    assert my_fulladder_1bit([1], [1], 0) == (1, [0]), "Failed on 1 + 1 + 0"
    assert my_fulladder_1bit([1], [1], 1) == (1, [1]), "Failed on 1 + 1 + 1"

def test_8bit_addition():
    """Test standard 8-bit addition with signed (Two's Complement) results."""
    adder8 = NBitAdderWithCarryOut(8)

    # Test 1: Simple Addition (15 + 25 = 40)
    c, s = adder8(int_to_8bit_list(15), int_to_8bit_list(25))
    assert bit_list_to_int(s) == 40, "15 + 25 failed"
    assert c == 0, "15 + 25 should not carry out"

    # Test 2: Checkerboard Bits (170 + 85 = 255 -> Signed: -1)
    c, s = adder8(int_to_8bit_list(170), int_to_8bit_list(85))
    assert bit_list_to_int(s) == -1, "170 + 85 failed to evaluate to -1"
    assert c == 0, "170 + 85 should not carry out"

    # Test 3: The 8-Bit Ripple Overflow (-1 + 1 = 0)
    c, s = adder8(int_to_8bit_list(-1), int_to_8bit_list(1))
    assert bit_list_to_int(s) == 0, "-1 + 1 failed to overflow to 0"
    assert c == 1, "-1 + 1 failed to trigger final carry out"


def test_8bit_subtraction():
    """Test Two's Complement subtraction natively using negative inputs."""
    adder8 = NBitAdderWithCarryOut(8)

    # Test 4: Basic Subtraction (50 - 18 = 32)
    c, s = adder8(int_to_8bit_list(50), int_to_8bit_list(-18))
    assert bit_list_to_int(s) == 32, "50 - 18 failed to equal 32"
    assert c == 1, "50 - 18 failed to trigger carry out (normal for positive subtraction)"

    # Test 5: Negative Result (10 - 15 = -5)
    c, s = adder8(int_to_8bit_list(10), int_to_8bit_list(-15))
    assert bit_list_to_int(s) == -5, "10 - 15 failed to equal -5"
    assert c == 0, "10 - 15 should not trigger carry out (normal for negative result)"


def test_16bit_addition():
    """Test standard addition using a single 16-bit hardware component (Unsigned)."""
    adder16 = NBitAdderWithCarryOut(16)

    # Test 1: Basic Math (1024 + 2048 = 3072)
    c, s = adder16(int_to_16bit_list(1024), int_to_16bit_list(2048))
    assert bit_list_to_int(s, signed=False) == 3072, "1024 + 2048 failed"
    assert c == 0

    # Test 2: Alternating Bits (43690 + 21845 = 65535)
    c, s = adder16(int_to_16bit_list(43690), int_to_16bit_list(21845))
    assert bit_list_to_int(s, signed=False) == 65535, "Alternating bits failed"
    assert c == 0

    # Test 3: The 16-Bit Ripple Overflow (65535 + 1 = 0, Carry 1)
    c, s = adder16(int_to_16bit_list(65535), int_to_16bit_list(1))
    assert bit_list_to_int(s, signed=False) == 0, "65535 + 1 failed to overflow to 0"
    assert c == 1, "65535 + 1 failed to trigger final carry out"


def test_cascaded_16bit_addition():
    """Test 16-bit addition by chaining the carry wire between two 8-bit Adders."""
    adder8_low_byte = NBitAdderWithCarryOut(8)
    adder8_high_byte = NBitAdderWithCarryOut(8)

    def add_cascaded(num1, num2):
        x_bits = int_to_16bit_list(num1)
        y_bits = int_to_16bit_list(num2)

        # Process the right-most 8 bits (Low Byte)
        carry_low, sum_low = adder8_low_byte(x_bits[8:], y_bits[8:])
        
        # Process the left-most 8 bits (High Byte), passing the carry wire across!
        final_carry, sum_high = adder8_high_byte(x_bits[0:8], y_bits[0:8], last_carry_in=carry_low)
        
        # Recombine the arrays
        sum_16bit = sum_high + sum_low
        return final_carry, bit_list_to_int(sum_16bit, signed=False)

    # Test 1: Basic Math
    c, s_val = add_cascaded(1024, 2048)
    assert s_val == 3072, "Cascaded 1024 + 2048 failed"
    assert c == 0

    # Test 2: Alternating Bits
    c, s_val = add_cascaded(43690, 21845)
    assert s_val == 65535, "Cascaded Alternating bits failed"
    assert c == 0

    # Test 3: The Ultimate Ripple across components
    c, s_val = add_cascaded(65535, 1)
    assert s_val == 0, "Cascaded 65535 + 1 failed to overflow"
    assert c == 1, "Cascaded 65535 + 1 failed to carry out of the high byte"

if __name__ == "__main__":
    test_and_gate()
    test_or_gate()
    test_inverter_gate()
    test_nand_gate()
    test_nor_gate()
    test_xor_gate()

    test_half_adder()
    test_full_adder()

    test_1bit_addition()
    test_8bit_addition()
    test_8bit_subtraction()
    test_16bit_addition()
    test_cascaded_16bit_addition()