from src.utils import *

def test_page_318_16bit_addition():
    """Tests 16-bit addition using MVI, ADI, ACI, and STA (Page 318)."""
    print("[ RUN      ] 16-Bit Addition Test (Page 318)")
    
    cpu = CPUSubSet_8080()
    system_tick = Oscillator()
    
    program = [
        0x3E, 0x88,       # 0000h: MVI A, 88h  (Load low byte of 1388h)
        0xC6, 0xC4,       # 0002h: ADI C4h     (Add low byte of 09C4h)
        0x32, 0x10, 0x00, # 0004h: STA 0010h   (Store result at 0010h)
        0x3E, 0x13,       # 0007h: MVI A, 13h  (Load high byte of 1388h)
        0xCE, 0x09,       # 0009h: ACI 09h     (Add with Carry high byte of 09C4h)
        0x32, 0x11, 0x00, # 000Bh: STA 0011h   (Store result at 0011h)
        0x76              # 000Eh: HLT         (Halt CPU)
    ]
    
    cpu.load_program(program, start_address=0x0000)
    cpu.reset()
    
    for _ in range(1000):
        cpu.tick(system_tick.level())
        system_tick.tick()
        if cpu.current_halt_state == 1:
            break

    assert cpu.current_halt_state == 1, "CPU did not halt. Reached max ticks."

    low_byte_bits = cpu.ram.read(int_to_16bit_list(0x0010), enable=1)
    high_byte_bits = cpu.ram.read(int_to_16bit_list(0x0011), enable=1)
    final_16bit_val = bit_list_to_int(high_byte_bits + low_byte_bits, signed=True)
    
    assert final_16bit_val == 0x1D4C, f"16-bit sum is incorrect. Expected 0x1D4C, got 0x{final_16bit_val:04X}"
    print("[       OK ] 16-Bit Addition (1388h + 09C4h = 1D4Ch)")

def test_page_340_lda_sta_add():
    """Tests Direct Memory Access and Register Arithmetic (Page 340)."""
    print("[ RUN      ] LDA/STA and ADD B Test (Page 340)")
    
    cpu = CPUSubSet_8080()
    system_tick = Oscillator()
    
    program = [
        0x3A, 0x44, 0x20, # 0000h: LDA 2044h (Load A from 2044h)
        0x06, 0x33,       # 0003h: MVI B, 33h  (Load 33h into B)
        0x80,             # 0005h: ADD B       (Add B to A)
        0x32, 0x44, 0x20, # 0006h: STA 2044h   (Store A to 2044h)
        0x76              # 0009h: HLT         (Halt CPU)
    ]
    
    cpu.load_program(program, start_address=0x0000)
    
    # Inject initial data into RAM
    target_address = int_to_16bit_list(0x2044)
    cpu.ram(target_address, int_to_8bit_list(0x66), write=1)
    cpu.reset()
    
    for _ in range(1000):
        cpu.tick(system_tick.level())
        system_tick.tick()
        if cpu.current_halt_state == 1:
            break

    assert cpu.current_halt_state == 1, "CPU did not halt. Reached max ticks."

    result_bits = cpu.ram.read(target_address, enable=1)
    result_val = bit_list_to_int(result_bits, signed=False)
    
    assert result_val == 0x99, f"Calculation failed. Expected 0x99, got 0x{result_val:02X}"
    print("[       OK ] LDA/STA and ADD B (66h + 33h = 99h)")

def test_page_377_sum_program():
    """Tests sequential memory reading and accumulator addition (Page 377)."""
    print("[ RUN      ] Sum Array Program Test (Page 377)")
    
    cpu = CPUSubSet_8080()
    system_tick = Oscillator()
    
    program = [
        0x2E, 0x00,       # 0000h: MVI L, 00h
        0x26, 0x10,       # 0002h: MVI H, 10h   (HL is now 1000h)
        0x7E,             # 0004h: MOV A, M     (A = RAM[1000h])
        0x23,             # 0005h: INX HL       (HL = 1001h)
        0x86,             # 0006h: ADD M        (A = A + RAM[1001h])
        0x23,             # 0007h: INX HL
        0x86,             # 0008h: ADD M
        0x23,             # 0009h: INX HL
        0x86,             # 000Ah: ADD M
        0x23,             # 000Bh: INX HL
        0x86,             # 000Ch: ADD M
        0x32, 0x11, 0x00, # 000Dh: STA 0011h    (RAM[0011h] = A)
        0x76              # 0010h: HLT
    ]
    
    cpu.load_program(program, start_address=0x0000)
    
    # Array of data to sum up
    data_values = [0x01, 0x02, 0x03, 0x04, 0x05]
    cpu.load_program(data_values, start_address=0x1000)
    cpu.reset()
    
    for _ in range(1000):
        cpu.tick(system_tick.level())
        system_tick.tick()
        if cpu.current_halt_state == 1:
            break

    assert cpu.current_halt_state == 1, "CPU did not halt. Reached max ticks."

    result_bits = cpu.ram.read(int_to_16bit_list(0x0011), enable=1)
    result_val = bit_list_to_int(result_bits, signed=True)
    
    assert result_val == 15, f"Sum is incorrect. Expected 15, got {result_val}"
    print("[       OK ] Sum Array Program (1 + 2 + 3 + 4 + 5 = 15)")

if __name__ == "__main__":
    test_page_318_16bit_addition()
    test_page_340_lda_sta_add()
    test_page_377_sum_program()