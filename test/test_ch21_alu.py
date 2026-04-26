from src.utils import *

def test_logic_unit():
    """Validates pure bitwise operations."""
    logic = Logic(nin_data=8, nin_control=3)
    
    A = int_to_8bit_list(204) # 11001100
    B = int_to_8bit_list(170) # 10101010
    
    # 1. AND (100) -> 10001000 (136)
    res_and = logic(A, B, [1, 0, 0])
    assert bit_list_to_int(res_and, signed=False) == 136, "Logic AND failed!"
    
    # 2. XOR (101) -> 01100110 (102)
    res_xor = logic(A, B, [1, 0, 1])
    assert bit_list_to_int(res_xor, signed=False) == 102, "Logic XOR failed!"

    # 3. OR (110) -> 11101110 (238)
    res_or = logic(A, B, [1, 1, 0])
    assert bit_list_to_int(res_or, signed=False) == 238, "Logic OR failed!"

def test_add_subtract_unit():
    """Validates addition and hardware borrow/carry-in logic."""
    add_sub = Add_Subtract(nin_data=8, nin_control=2)
    
    A = int_to_8bit_list(100)
    B = int_to_8bit_list(50)
    
    # 1. ADD (00) -> 100 + 50 = 150
    cy, res = add_sub(A, B, F1_0=[0, 0], CY_In=0)
    assert bit_list_to_int(res, signed=False) == 150, "Standard ADD failed"
    assert cy == 0, "ADD Carry Out should be 0"

    # 2. ADC (01) -> 100 + 50 + 1 (Carry In) = 151
    cy, res = add_sub(A, B, F1_0=[0, 1], CY_In=1)
    assert bit_list_to_int(res, signed=False) == 151, "ADC (Add with Carry) failed"

    # 3. SUB (10) -> 100 - 50 = 50
    # Because 100 > 50, Intel hardware Borrow (CY) should be 0.
    cy, res = add_sub(A, B, F1_0=[1, 0], CY_In=0)
    assert bit_list_to_int(res, signed=False) == 50, "SUB failed"
    assert cy == 0, "SUB Borrow out should be 0"

    # 4. SBB (11) -> 100 - 50 - 1 (Borrow In) = 49
    cy, res = add_sub(A, B, F1_0=[1, 1], CY_In=1)
    assert bit_list_to_int(res, signed=False) == 49, "SBB (Sub with Borrow) failed"

def test_full_alu_compare_and_flags():
    """Validates the Full ALU integration, Tri-State buffers, and Flag Generation."""
    alu = ALU(nin_data=8, nin_control_signal=3)
    
    def pulse_alu(val_A, val_B, op_code):
        """Helper to fire the clock and extract result/flags."""
        A_bits = int_to_8bit_list(val_A)
        B_bits = int_to_8bit_list(val_B)
        
        alu(A_bits, B_bits, op_code, clock=0)
        alu(A_bits, B_bits, op_code, clock=1)
        alu(A_bits, B_bits, op_code, clock=0)
        
        res = bit_list_to_int(alu.read_out(enable=1), signed=False)
        flags = alu.read_flags() # [Sign, Zero, Carry]
        return res, flags

    # 1. Standard ADD (000)
    res, flags = pulse_alu(100, 50, [0, 0, 0])
    assert res == 150, "Full ALU ADD failed"

    # 2. Compare (CMP - 111): A = 100, B = 100
    # Expected: Bus remains A (100). Hidden sub makes Zero Flag = 1.
    res, flags = pulse_alu(100, 100, [1, 1, 1])
    assert res == 100, f"CMP should leave Accumulator intact (100), got {res}"
    assert flags[2] == 0, "CMP set Carry Flag incorrectly!"
    assert flags[1] == 1, "CMP did not set Zero Flag for A == B!"

    # 3. Compare (CMP - 111): A = 50, B = 100
    # Expected: Bus remains A (50). Hidden sub needs a borrow, so Carry Flag = 1.
    res, flags = pulse_alu(50, 100, [1, 1, 1])
    assert res == 50, f"CMP should leave Accumulator intact (50), got {res}"
    assert flags[2] == 1, "CMP did not set Carry (Borrow) Flag for A < B!"
    assert flags[1] == 0, "CMP Zero flag incorrect"
    
    # Sign flag is tied to Accumulator MSB, which is 0 for 50 (0x32)
    assert flags[0] == 0, "CMP Sign flag incorrect"

    # 4. Compare (CMP - 111): A = 100, B = 50
    # Expected: Bus remains A (100). No borrow, not zero.
    res, flags = pulse_alu(100, 50, [1, 1, 1])
    assert res == 100, f"CMP should leave Accumulator intact (100), got {res}"
    assert flags[2] == 0, "CMP set Carry (Borrow) Flag incorrectly for A > B!"
    assert flags[1] == 0, "CMP Zero flag incorrect"

if __name__ == "__main__":
    test_logic_unit()
    test_add_subtract_unit()
    test_full_alu_compare_and_flags()