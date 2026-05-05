from src.utils import *

def test_petzold_loop_program():
    """
    Tests an 8080 program containing a loop and a conditional jump.
    The program sums an array of numbers until it encounters a zero.
    Based on Charles Petzold's 'Code' (Chapter 24).
    """
    print("Running Petzold Loop & Jump Program Test (Page 386)...")
    
    cpu = CPUSubSet_8080()
    system_tick = Oscillator()
    
    # 1. The Machine Code derived from Image 8 and Image 9 opcodes
    # This program will store the final sum at address 0x1100.
    program = [
        # Start:
        0x2E, 0x00,       # 0000h: MVI L,00h    (Load register L with 00h)
        0x26, 0x10,       # 0002h: MVI H,10h    (Load register H with 10h. HL points to data)
        0x06, 0x00,       # 0004h: MVI B,00h    (Load register B with 00h. B is the running sum)
        
        # Loop:
        0x7E,             # 0006h: MOV A,M      (Move data byte to Accumulator)
        0xFE, 0x00,       # 0007h: CPI 00h      (Compare Accumulator with zero)
        0xCA, 0x12, 0x00, # 0009h: JZ End       (Jump if Zero flag is set to address 0012h)
        0x80,             # 000Ch: ADD B        (Add running sum to current data byte)
        0x47,             # 000Dh: MOV B,A      (Store result back in register B)
        0x23,             # 000Eh: INX HL       (Increment memory pointer HL)
        0xC3, 0x06, 0x00, # 000Fh: JMP Loop     (Unconditional jump to start of loop at 0006h)
        
        # End:
        0x78,             # 0012h: MOV A,B      (Move final sum into Accumulator for storing)
        0x32, 0x00, 0x11, # 0013h: STA Result   (Store sum in Accumulator at Result address 1100h)
        0x76              # 0016h: HLT          (Halt CPU)
    ]
    
    cpu.load_program(program, start_address=0x0000)
    
    # 2. Prepare the Data Array
    # We use [1, 2, 3, 4, 5, 0]. The sum should be 15 (0x0F).
    data_values = [0x01, 0x02, 0x03, 0x04, 0x05, 0x00]
    data_start_address = 0x1000
    cpu.load_program(data_values, start_address=data_start_address)
    # 3. Boot the CPU
    cpu.reset()
    
    print("\n[SYSTEM] Executing Clock Cycles...\n")
    
    # Run the system clock until the CPU halts
    for _ in range(1000):
        cpu.tick(system_tick.level())
        system_tick.tick()
        if cpu.current_halt_state == 1:
            break

    # Ensure the CPU successfully executed the HLT instruction
    assert cpu.current_halt_state == 1, "CPU did not halt. Reached max ticks."

    # 4. Read the final result directly from RAM
    # Latch the result address [1100h] into PC to read it back (purely for demonstration)
    result_address = 0x1100
    result_bits = cpu.ram.read(int_to_16bit_list(result_address), enable=1)
    result_val = bit_list_to_int(result_bits, signed=True)
    
    # 5. Verify the result (1 + 2 + 3 + 4 + 5 = 15)
    assert result_val == 15, f"Sum is incorrect. Expected 15, got {result_val}"
    print("[       OK ] Sum Array Program (1 + 2 + 3 + 4 + 5 = 15)")


if __name__ == "__main__":
    test_petzold_loop_program()