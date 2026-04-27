from src.utils import *

# ==========================================
# 1. REGISTER ARRAY TEST
# ==========================================
def test_register_array():
    ra = RegisterArray(nbits=8)

    select_codes = {
        'B': [0, 0, 0], 'C': [0, 0, 1], 'D': [0, 1, 0], 'E': [0, 1, 1],
        'H': [1, 0, 0], 'L': [1, 0, 1], 'A': [1, 1, 1]
    }
    dummy_addr = [0] * 16

    def write_reg(val, select):
        """Simulates the Setup Time -> Rising Edge -> Falling Edge for registers."""
        data = int_to_8bit_list(val)
        ra(data, select, clock=0, addr=dummy_addr, hl_select=0, hl_clock=0) 
        ra(data, select, clock=1, addr=dummy_addr, hl_select=0, hl_clock=0) 
        ra(data, select, clock=0, addr=dummy_addr, hl_select=0, hl_clock=0) 

    # Test Standard Latches
    write_reg(0x11, select_codes['B'])
    write_reg(0x22, select_codes['C'])
    write_reg(0x33, select_codes['D'])
    write_reg(0x44, select_codes['E'])

    assert bit_list_to_int(ra.read_register(select_codes['B'], enable=1), False) == 0x11, "Reg B failed"
    assert bit_list_to_int(ra.read_register(select_codes['C'], enable=1), False) == 0x22, "Reg C failed"
    assert bit_list_to_int(ra.read_register(select_codes['D'], enable=1), False) == 0x33, "Reg D failed"
    assert bit_list_to_int(ra.read_register(select_codes['E'], enable=1), False) == 0x44, "Reg E failed"

    # Test Accumulator Path
    write_reg(0x77, select_codes['A'])
    assert bit_list_to_int(ra.read_accumulator(enable=1), False) == 0x77, "Acc read path failed"

    # ra.write_accumulator(int_to_8bit_list(0x88), clk=0)
    # ra.write_accumulator(int_to_8bit_list(0x88), clk=1)
    # ra.write_accumulator(int_to_8bit_list(0x88), clk=0)
    # assert bit_list_to_int(ra.read_register(select_codes['A'], enable=1), False) == 0x88, "Acc write path failed"

    # Test 16-bit HL Pointer Logic
    test_address = int_to_16bit_list(0xABCD)
    ra(data=[0]*8, select=[0,0,0], clock=0, addr=test_address, hl_select=1, hl_clock=0)
    ra(data=[0]*8, select=[0,0,0], clock=0, addr=test_address, hl_select=1, hl_clock=1)
    ra(data=[0]*8, select=[0,0,0], clock=0, addr=test_address, hl_select=1, hl_clock=0)

    hl_out = ra.read_hl(enable_hl=1)
    assert bit_list_to_int(hl_out, False) == 0xABCD, "HL 16-bit pointer write/read failed"
    assert bit_list_to_int(ra.read_register(select_codes['H'], enable=1), False) == 0xAB, "H register corrupted"
    assert bit_list_to_int(ra.read_register(select_codes['L'], enable=1), False) == 0xCD, "L register corrupted"


# ==========================================
# 2. INSTRUCTION LATCH TEST
# ==========================================
def test_inst_latch():
    latch = InstLatch(nbits=8)

    def pulse_latch(target_latch_num, val):
        data_bits = int_to_8bit_list(val)
        write_funcs = {
            1: latch.write_latch1,
            2: latch.write_latch2,
            3: latch.write_latch3
        }
        func = write_funcs[target_latch_num]
        func(data_bits, 0)
        func(data_bits, 1)
        func(data_bits, 0)

    # 1. Opcode Latch (Always feeding Control Unit)
    pulse_latch(1, 0x3E) # MVI A
    assert bit_list_to_int(latch.read_latch1(), False) == 0x3E, "Latch 1 failed to hold Opcode"

    # 2. Immediate Data Latch
    pulse_latch(2, 0x45) 
    assert bit_list_to_int(latch.read_latch2(enable=0), False) == 0x00, "Latch 2 leaked data when disabled!"
    assert bit_list_to_int(latch.read_latch2(enable=1), False) == 0x45, "Latch 2 failed to output to Data Bus!"

    # 3. 16-bit Address Construction (Little Endian Test)
    pulse_latch(2, 0xCD) # Low Byte
    pulse_latch(3, 0xAB) # High Byte
    assert bit_list_to_int(latch.read_latch2_3(enable_2_3=0), False) == 0x0000, "Latches 2&3 leaked data!"
    
    result_16bit = bit_list_to_int(latch.read_latch2_3(enable_2_3=1), False)
    assert result_16bit == 0xABCD, f"Combined Address failed! Expected 0xABCD, got 0x{result_16bit:04X}."


# ==========================================
# 3. PROGRAM COUNTER TEST
# ==========================================
def test_program_counter():
    pc = ProgramCounter()

    # Reset
    pc.Reset()
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0x0000, "PC failed to reset to 0."

    # Clock & Setup Time 
    test_addr = int_to_16bit_list(0x1234)
    pc(test_addr, clk=0)
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0x0000, "PC prematurely changed before clock pulse!"

    pc(test_addr, clk=1)
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0x1234, "PC failed to latch data on rising edge!"

    pc(test_addr, clk=0)
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0x1234, "PC lost data on falling edge!"

    # Tri-State & Direct Setters
    assert bit_list_to_int(pc.readAddr(enable=0), False) == 0x0000, "Tri-State leak on PC!"
    
    pc.SetMaxAddr()
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0xFFFF, "SetMaxAddr failed!"

    pc.SetAddr(int_to_16bit_list(0xABCD))
    assert bit_list_to_int(pc.readAddr(enable=1), False) == 0xABCD, "SetAddr failed!"
    

# ==========================================
# 4. INCREMENTER / DECREMENTER TEST
# ==========================================
def test_incrementer_decrementer():
    inc_dec = IncrementerDecrementer()

    def pulse_clock(val):
        addrs = int_to_16bit_list(val)
        inc_dec(addrs, clock=0)
        inc_dec(addrs, clock=1)
        inc_dec(addrs, clock=0)

    # Incrementing
    pulse_clock(0x1000)
    assert bit_list_to_int(inc_dec.readAddr(0, 1), False) == 0x1001, "Increment failed!"

    pulse_clock(0xFFFF)
    assert bit_list_to_int(inc_dec.readAddr(0, 1), False) == 0x0000, "Increment Rollover failed!"

    # Decrementing
    pulse_clock(0x2000)
    assert bit_list_to_int(inc_dec.readAddr(1, 0), False) == 0x1FFF, "Decrement failed!"

    pulse_clock(0x0000)
    assert bit_list_to_int(inc_dec.readAddr(1, 0), False) == 0xFFFF, "Decrement Underflow failed!"

    # Isolation
    pulse_clock(0xABCD)
    assert bit_list_to_int(inc_dec.readAddr(0, 0), False) == 0x0000, "Tri-State leak on Inc/Dec!"

# ==========================================
# TEST RUNNER
# ==========================================
if __name__ == "__main__":
    test_register_array()
    test_inst_latch()
    test_program_counter()
    test_incrementer_decrementer()