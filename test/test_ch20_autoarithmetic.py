from src.utils import *

class ControlSignals_Ch20:
    """
    Generates the core timing signals for the automated CPU.
    Takes a raw oscillator clock and splits it into two distinct signals:
    1. clk_input_to_counter: Ticks the Program Counter (PC) forward.
    2. pulse: Triggers the registers to latch data.
    """
    def __init__(self):
        self.edge_flipflop1 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.edge_flipflop2 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.invert1 = Inverter()
        self.and_gate = AND()
        
    def __call__(self, clock):
        not_clk = self.invert1([clock])

        # NOTE (Hardware Physics):
        # We use a frequency divider setup here. 
        # Flip-Flop 1 divides the clock. Flip-Flop 2 creates a delayed copy.
        # By ANDing FF1's inverse with FF2, we create a short "Pulse" that 
        # happens precisely in the middle of the counter's stable cycle.
        self.edge_flipflop1([self.edge_flipflop1.getQ_bar(), clock])
        self.edge_flipflop2([self.edge_flipflop1.getQ(), not_clk])
        
        clk_input_to_counter = self.edge_flipflop1.getQ()
        pulse = self.and_gate([self.edge_flipflop1.getQ_bar(), self.edge_flipflop2.getQ()])
        
        return [clk_input_to_counter, pulse]
    
class Counter16Bit:
    """
    A 16-Bit Ripple Counter used as the Program Counter (PC) or Memory Address Register.
    """
    def __init__(self):
        self.nbits = 16
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs)) # MSB on the left
    
    def SetMaxAddr(self):
        """Forces the counter to 0xFFFF. The next tick will overflow it to 0x0000."""
        for ff in self.flipflops:
            ff([0, 0, 1, 0]) # PRE = 1, CLR = 0

    def __call__(self, clk=0, clear_wire=0):
        # Hardware stabilization loop for the 16-bit ripple
        while True:
            old_qs = [ff.getQ() for ff in self.flipflops]

            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            new_qs = [ff.getQ() for ff in self.flipflops]
            if old_qs == new_qs:
                break

        return list(reversed(new_qs))
    
class Decoder_2_4:
    """
    A 2-to-4 Decoder (Reverse Mapping).
    Takes 2 input bits and decodes them into 4 output lines.
    Input 00 -> output[3] is 1
    Input 11 -> output[0] is 1
    
    Used in the AutomatedAccumulatingAdderV2 to control the 4-phase instruction cycle.
    """
    def __init__(self, nin=2, nout=4):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(2) for _ in range(self.nout)]
        
        # A separate layer of AND gates to safely combine the decoded lines with a Write Enable signal
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
        """Safely merges the decoded address lines with a global Write Enable signal."""
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs

    def __call__(self, address):
        assert len(address) == self.nin, "Input must be 2 bits long"
        idxs = [[0, 0], [0, 1], [1, 0], [1, 1]]
        address = [[address[i]] for i in range(len(address))] 
        output = [0] * self.nout
        
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            
            # REVERSE MAPPING: 00 -> index 3
            output[self.nout - 1 - i] = self.and_gates[i](input_and)
            
        return output

class AutomatedAccumulatingAdder:
    """
    A simple 1-Byte (8-bit) Automated Accumulator.
    
    Hardware Flow:
    1. The Counter ticks and outputs an address.
    2. It fetches exactly 1 byte (8 bits) of data from RAM.
    3. It adds that byte to its internal 8-bit register.
    
    Limitation: It can only add numbers up to 255. It has no concept 
    of "Instructions" or multi-byte math.
    """
    def __init__(self, nbits=8):
        self.nbits = nbits
        self.counter = Counter16Bit()  
        self.ram64KB = RAM_64KB()

        self.adder = NBitAdderWithOverflow(self.nbits)
        self.register = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        self.nor_gate = NOR(self.nbits) 
        self.and_gate = AND(2)

    def SetMaxAddr(self):
        self.counter.SetMaxAddr()

    def __call__(self, clk_input_to_counter, pulse):
        # 1. Tick and fetch 1 byte
        self.counter(clk_input_to_counter)
        addr = self.counter.getQs()
        data_out_from_memory = self.ram64KB.read(addr)
        
        # 2. Add and Latch
        overflow, sum_bits = self.adder(data_out_from_memory, self.register.getQ())
        self.register(sum_bits, pulse)  

        # 3. RAM Write Logic (Petzold Page 297)
        # Writes the accumulated sum to the first memory location that holds 0x00.
        ram_write = self.and_gate([self.nor_gate(data_out_from_memory), pulse])
        if ram_write:
            self.write_to_memory(addr, self.register.getQ())

    def write_to_memory(self, address, data):
        self.ram64KB(address, data, write=1)

    def read_register(self):
        return self.register.getQ()
    
class AutomatedAccumulatingAdderV2:
    """
    An advanced 3-Byte (24-bit) Automated Accumulator.
    
    Hardware Flow:
    This machine uses a 4-phase instruction cycle, driven by the last 2 bits of the address:
    - Phase 00 (Enable Instruct): Fetches the Operation Code (Add, Sub, Halt, Write).
    - Phase 01 (Enable Low): Fetches and computes the Low 8 bits.
    - Phase 10 (Enable Middle): Fetches the Middle 8 bits, adds the carry from Low.
    - Phase 11 (Enable High): Fetches the High 8 bits, adds the carry from Middle.
    
    By cascading the carry bits, it can add numbers up to 16,777,215!
    """
    def __init__(self, nbits=8):
        self.nbits = nbits
        self.counter = Counter16Bit()  
        self.ram64KB = RAM_64KB()
        self.adder = NBitAdderWithOverflow(self.nbits)

        self.inst_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        # =====================================================================
        # EDUCATIONAL NOTE: THE CARRY-OUT LATCH (nbits + 1)
        # Why are the Low and Middle latches 9 bits instead of 8 bits?
        # Because we need to save the "carry_out" bit for the NEXT clock cycle!
        # When Phase 01 ends, we latch the 8 sum bits PLUS the 1 carry bit.
        # When Phase 10 starts, we feed that saved carry bit back into the adder.
        # =====================================================================
        self.low_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits + 1)    
        self.middle_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits + 1) 
        self.high_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)   

        self.decoder_2_4_for_clock = Decoder_2_4() # Uses Reverse Mapping
        
        self.and_gate_use_for_instruct_clk = AND()
        self.and_gate_use_for_low_byte_clk = AND(3)
        self.and_gate_use_for_middle_byte_clk = AND(3)
        self.and_gate_use_for_high_byte_clk = AND(3)

        self.xor_gates_for_complements = [XOR() for _ in range(self.nbits)]
        self.and_gate_for_carry_in_adder = AND()
        self.or_gate_for_carry_in_adder = OR()

        self.invert_for_write_ram = Inverter()
        self.and_gate_for_write_ram = AND(3)

        self.enable_low_byte = -1
        self.enable_mid_byte = -1
        self.enable_hig_byte = -1
        self.carry_in_adder = -1
        self.input_a = [-1] * self.nbits
        self.enable_instruct = -1
        self.halt_instruct = -1

    def SetMaxAddr(self):
        self.counter.SetMaxAddr()

    # --- Debugging / State Retrieval Methods ---
    def getEnableLow(self): return self.enable_low_byte
    def getEnableMiddle(self): return self.enable_mid_byte
    def getEnableHigh(self): return self.enable_hig_byte
    def getHaltInst(self): return self.halt_instruct
    def getCarryInAdder(self): return self.carry_in_adder
    def getInputA(self): return self.input_a
    def getEnableInstruc(self): return self.enable_instruct

    def __call__(self, clk_input_to_counter, pulse):
        self.counter(clk_input_to_counter)
        addr = self.counter.getQs()
        data_out_from_memory = self.ram64KB.read(addr)

        # 1. Decode the 4 Phases
        enable_high_byte, enable_middle_byte, enable_low_byte, enable_instruct = self.decoder_2_4_for_clock([addr[-2], addr[-1]])

        self.enable_instruct = enable_instruct
        self.enable_low_byte = enable_low_byte
        self.enable_mid_byte = enable_middle_byte
        self.enable_hig_byte = enable_high_byte

        # 2. Phase 00: Latch Instruction Code
        instruction_latch_clk = self.and_gate_use_for_instruct_clk([enable_instruct, pulse])
        self.inst_latch(data_out_from_memory, instruction_latch_clk)  
        Q_from_inst_latch = self.inst_latch.getQ()

        self.halt_instruct = Q_from_inst_latch[-4] # Q3 is Halt
        Q1_math_en = Q_from_inst_latch[-2]
        Q0_sub = Q_from_inst_latch[-1]

        # 3. Prepare Phase Clocks
        low_byte_latch_clk = self.and_gate_use_for_low_byte_clk([Q1_math_en, pulse, enable_low_byte])
        mid_byte_latch_clk = self.and_gate_use_for_middle_byte_clk([Q1_math_en, pulse, enable_middle_byte])
        high_byte_latch_clk = self.and_gate_use_for_high_byte_clk([Q1_math_en, pulse, enable_high_byte])

        # 4. Prepare Data A (1's Complement for Subtraction)
        outputs_from_complements_of_one = []
        for idx, xor_gate in enumerate(self.xor_gates_for_complements):
            outputs_from_complements_of_one.append(xor_gate([Q0_sub, data_out_from_memory[idx]]))
        self.input_a = outputs_from_complements_of_one

        # 5. Route Carry and Data B based on Phase
        if enable_low_byte:
            carry_signal_from_tri_state_buffers = 0 # Low byte has no carry in from previous    
            input_b = self.low_latch.getQ()[1:]
        elif enable_middle_byte:
            carry_signal_from_tri_state_buffers = self.low_latch.getQ()[0]  # Carry-out from Low
            input_b = self.middle_latch.getQ()[1:]
        elif enable_high_byte:
            carry_signal_from_tri_state_buffers = self.middle_latch.getQ()[0]  # Carry-out from Mid
            input_b = self.high_latch.getQ()
        else:
            input_b = [0] * self.nbits
            carry_signal_from_tri_state_buffers = 0

        # Subtraction needs +1 added to the very first carry_in
        self.carry_in_adder = self.or_gate_for_carry_in_adder([self.and_gate_for_carry_in_adder([enable_low_byte, Q0_sub]), carry_signal_from_tri_state_buffers])
        
        # 6. Execute Math
        overflow, sum_bits = self.adder(self.input_a, input_b, self.carry_in_adder)
        carry_out = self.adder.get_carry_out()

        # 7. Latch Sum (and Carry Out for the next phase)
        if enable_low_byte:
            self.low_latch([carry_out] + sum_bits, low_byte_latch_clk)  
        elif enable_middle_byte:
            self.middle_latch([carry_out] + sum_bits, mid_byte_latch_clk)  
        elif enable_high_byte:
            self.high_latch(sum_bits, high_byte_latch_clk)  

        # 8. RAM Write Logic
        Q2_write_en = Q_from_inst_latch[-3]
        ram_write = self.and_gate_for_write_ram([Q2_write_en, pulse, self.invert_for_write_ram([enable_instruct])])

        if ram_write:
            if enable_low_byte:
                self.write_to_memory(addr, self.low_latch.getQ()[1:]) # Ignore carry bit
            elif enable_middle_byte:
                self.write_to_memory(addr, self.middle_latch.getQ()[1:]) 
            elif enable_high_byte:
                self.write_to_memory(addr, self.high_latch.getQ())
            
    def write_to_memory(self, address, data):
        self.ram64KB(address, data, write=1)

    def read_low_register(self):
        return self.low_latch.getQ()[0], self.low_latch.getQ()[1:]
    
    def read_middle_register(self):
        return self.middle_latch.getQ()[0], self.middle_latch.getQ()[1:]        
    
    def read_high_register(self):
        return self.high_latch.getQ()
    

# ==========================================
# OPCODES (Instruction Set Mapping)
# ==========================================
INST_ADD   = 0x02  # 0000 0010 (Math Enable = 1)
INST_SUB   = 0x03  # 0000 0011 (Math Enable = 1, Subtract = 1)
INST_WRITE = 0x04  # 0000 0100 (Write Enable = 1)
INST_HALT  = 0x08  # 0000 1000 (Halt = 1)

# ==========================================
# TEST HELPERS (The "Elegant" Way)
# ==========================================
def run_cpu_program(program_bytes, max_ticks=500):
    """
    A mini-assembler and execution engine. 
    Loads a list of bytes into RAM, primes the CPU, and runs until HALT.
    """
    oscillator = Oscillator()
    ctrl = ControlSignals_Ch20()
    cpu = AutomatedAccumulatingAdderV2()
    
    # 1. Program the RAM automatically
    for addr, byte_val in enumerate(program_bytes):
        cpu.ram64KB(int_to_16bit_list(addr), int_to_8bit_list(byte_val), write=1)
        
    # 2. Prime the Program Counter
    cpu.SetMaxAddr() 
    
    # 3. Run the Hardware Clock
    ticks = 0
    while ticks < max_ticks:
        clk_cnt, pulse = ctrl(oscillator.level())
        cpu(clk_cnt, pulse)
        
        if cpu.halt_instruct == 1:
            break
            
        oscillator.tick()
        ticks += 1
        
    assert cpu.halt_instruct == 1, "FATAL: CPU reached max ticks without hitting HALT!"
    return cpu

def get_24bit_result(cpu):
    """Elegantly combines the 3 latches into a single human-readable Python integer."""
    low = bit_list_to_int(cpu.low_latch.getQ()[1:], signed=False)
    mid = bit_list_to_int(cpu.middle_latch.getQ()[1:], signed=False)
    hi  = bit_list_to_int(cpu.high_latch.getQ(), signed=False)
    
    # Shift and combine (Hi << 16) | (Mid << 8) | (Low)
    return (hi << 16) | (mid << 8) | low

# ==========================================
# THE TEST SUITE
# ==========================================

def test_control_signals():
    """Proves the clock dividing and pulse logic correctly fires."""
    oscillator = Oscillator()
    ctrl = ControlSignals_Ch20()
    
    pulses_seen = 0
    for i in range(8):
        clk_cnt, pulse = ctrl(oscillator.level())
        if pulse == 1:
            pulses_seen += 1
        oscillator.tick()
        
    assert pulses_seen == 2, "Control signals failed! Expected 2 precise pulses over 8 ticks."

def test_counter16Bit():
    my_oscillator = Oscillator()
    nbits = 16
    my_counter = Counter16Bit()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0
    for clk in range(65537):
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_counter(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected counter value on the rising edge of the clock
            golden_value = (golden_value + 1) % (2 ** nbits)  # Increment and wrap around at 2^nbits
            golden_qs = int_to_nbit_list(golden_value, nbits)

        assert golden_qs == my_counter.getQs(), f"At clock {clk}, expected counter value {golden_value} but got {int(''.join(str(bit) for bit in my_counter.getQs()))}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for

def test_counter16BitMaxAddr():
    nbits = 16
    my_counter = Counter16Bit()
    
    my_counter.SetMaxAddr()
    golden_value = 65535
    golden_qs = int_to_nbit_list(golden_value, nbits)
    assert golden_qs == my_counter.getQs(), f"expected counter value {golden_value} but got {int(''.join(str(bit) for bit in my_counter.getQs()))}"
    
def test_addition_with_massive_carry_ripple():
    """
    Tests if a carry bit successfully ripples through all 3 bytes.
    Equation: 0x00FFFF + 0x000002 = 0x010001
    """
    program = [
        # 1. Add 0x00FFFF
        INST_ADD, 0xFF, 0xFF, 0x00,
        # 2. Add 0x000002
        INST_ADD, 0x02, 0x00, 0x00,
        # 3. Halt
        INST_HALT, 0x00, 0x00, 0x00
    ]
    
    cpu = run_cpu_program(program)
    result = get_24bit_result(cpu)
    
    assert result == 0x010001, f"Massive Carry Failed! Expected 0x010001, got {hex(result)}"

def test_subtraction_with_borrow():
    """
    Tests 1's complement subtraction and borrow logic across bytes.
    Equation: 0x000500 - 0x000001 = 0x0004FF
    """
    program = [
        # 1. Add 0x000500 (Base value)
        INST_ADD, 0x00, 0x05, 0x00,
        # 2. Subtract 0x000001
        INST_SUB, 0x01, 0x00, 0x00,
        # 3. Halt
        INST_HALT, 0x00, 0x00, 0x00
    ]
    
    cpu = run_cpu_program(program)
    result = get_24bit_result(cpu)
    
    assert result == 0x0004FF, f"Subtraction Borrow Failed! Expected 0x0004FF, got {hex(result)}"

def test_memory_write_back():
    """
    Tests if the CPU can save its accumulator back into RAM.
    Equation: Add 0x123456 -> Write to RAM -> Halt.
    """
    program = [
        # 1. Add 0x123456
        INST_ADD, 0x56, 0x34, 0x12,
        # 2. Write to RAM (The CPU will overwrite the next 3 dummy bytes)
        INST_WRITE, 0x00, 0x00, 0x00, 
        # 3. Halt
        INST_HALT, 0x00, 0x00, 0x00
    ]
    
    cpu = run_cpu_program(program)
    
    # Verify the latches are correct
    assert get_24bit_result(cpu) == 0x123456, "Initial addition failed before write."
    
    # VERIFY THE RAM!
    # The Write instruction was at Address 4. 
    # Therefore, the CPU should have written the Low byte to Addr 5, Mid to 6, High to 7.
    ram_low = bit_list_to_int(cpu.ram64KB.read(int_to_16bit_list(5)), False)
    ram_mid = bit_list_to_int(cpu.ram64KB.read(int_to_16bit_list(6)), False)
    ram_hi  = bit_list_to_int(cpu.ram64KB.read(int_to_16bit_list(7)), False)
    
    assert ram_low == 0x56, f"RAM Write Low Byte failed. Got {hex(ram_low)}"
    assert ram_mid == 0x34, f"RAM Write Mid Byte failed. Got {hex(ram_mid)}"
    assert ram_hi == 0x12, f"RAM Write High Byte failed. Got {hex(ram_hi)}"


if __name__ == "__main__":
    test_control_signals()
    test_addition_with_massive_carry_ripple()
    test_subtraction_with_borrow()
    test_memory_write_back()
    test_counter16Bit()
    test_counter16BitMaxAddr()