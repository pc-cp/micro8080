"""
utils.py

some components to build CPU, from basic Gates, Adder, Flip-Flop to complex ALU, RAM.

"""
# ----------------- chapter 14 -----------------
class AND:
    def __init__(self, nin=2):
        self.nin = nin

    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        result = x[0]
        # Chain bitwise AND over all inputs
        for val in x[1:]:
            result &= val
        return result

class OR:
    def __init__(self, nin=2):
        self.nin = nin

    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        result = x[0]
        # Chain bitwise OR over all inputs
        for val in x[1:]:
            result |= val
        return result

class Inverter:
    def __init__(self):
        self.nin = 1

    def __call__(self, x):
        assert len(x) == self.nin, "Inverter takes exactly 1 input"
        return 1 - x[0]

# Composing Complex Gates
class NAND:
    def __init__(self, nin=2):
        self.nin = nin
        self.and_gate = AND(nin)
        self.inverter = Inverter()

    def __call__(self, x):
        # x -> and -> invert -> out
        return self.inverter([self.and_gate(x)])

class NOR:
    def __init__(self, nin=2):
        self.nin = nin
        # NOR is just an OR gate followed by an Inverter
        self.or_gate = OR(nin)
        self.inverter = Inverter()

    def __call__(self, x):
        # x -> or -> invert -> out
        return self.inverter([self.or_gate(x)])

# Composing XOR gate use OR, NAND and AND gate
class XOR:
    def __init__(self):
        self.nin = 2

        self.or_gate = OR(self.nin)
        self.nand_gate = NAND(self.nin)
        self.and_gate = AND(self.nin)

    def __call__(self, x):
        assert len(x) == self.nin, "XOR takes exactly 2 inputs"
        # x -> or -> o1
        # x -> nand -> o2
        # and(o1, o2) -> out
        o1 = self.or_gate(x)
        o2 = self.nand_gate(x)
        return self.and_gate([o1, o2])

class HalfAdder:
    """
    Implement HalfAdder:
        Adding two binary numbers produces a sum bit and carry bit.

    Refer to Charles Petzold's 'Code': https://codehiddenlanguage.com/Chapter14/.
    This implement different with website, but same with page 176 of the book.
    """
    def __init__(self):
        self.nin = 2
        self.xor_gate = XOR()
        self.and_gate = AND(self.nin)

    def __call__(self, x):
        assert len(x) == self.nin, "Half Adder takes exactly 2 inputs"
        final_sum = self.xor_gate(x)
        final_carry = self.and_gate(x)

        return final_carry, final_sum
    
class FullAdder:
    """
    Implement FullAdder:
        Adding two binary numbers with the carry produces a sum bit and carry bit.

    This implement different with website, but same with page 177 of the book.
    """
    def __init__(self):
        self.nin = 3

        # A full adder is literally just two half adders and an OR gate
        self.ha1 = HalfAdder()
        self.ha2 = HalfAdder()
        self.or_gate = OR(2)

    def __call__(self, x):
        if len(x) == self.nin:
            carry_in, a, b = x[0], x[1], x[2]
        else:
            carry_in = 0
            a, b = x[0], x[1]

        # First Half-Adder adds A and B
        carry1, sum1 = self.ha1([a, b])
        # Second Half-Adder adds previous sum and the Carry-In
        carry2, final_sum = self.ha2([carry_in, sum1])
        # The OR gate catches the carry from either Half-Adder
        final_carry = self.or_gate([carry2, carry1])
        return final_carry, final_sum

class NBitAdderWithCarryOut:
    """
    Implement n bits fulladder with carry out flag:
        Adding n bits with carry produces n bits sum and carry bit.
    
    Refer to Charles Petzold's 'Code': https://codehiddenlanguage.com/Chapter14/.
    This implement same with page 180 of the book.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.fulladders = [FullAdder() for _ in range(self.nbits)]

    def __call__(self, x, y, last_carry_in=0):
        assert len(x) == self.nbits and len(y) == self.nbits, f"Inputs must be {self.nbits} bits long"
        final_sums = []
        final_carrys = last_carry_in

        # Iterate backwards: start from the far right and move left
        for idx in reversed(range(self.nbits)):
            carry_in = final_carrys
            a = x[idx]
            b = y[idx]
            # Run the Full Adder for this column bit
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            final_carrys = carry_out
            final_sums = [sum_out] + final_sums
        return final_carrys, final_sums

"""
NOTE: some basic data process functions, but they not correctly simulated by hardware,
      because they use condition sentences.
      now we want use it generate some bits and use for components.
"""
def int_to_nbit_list(num, nbits=8):
    """
    Converts an integer to an n-bit list using our simulated hardware 
    for Two's Complement (Invert and Add 1).
    """
    abs_val = abs(num)
    bin_str = format(abs_val, f'0{nbits}b')
    bit_list = [int(bit) for bit in bin_str]

    if num >= 0:
        return bit_list
    
    # Step A: Pass the bits through our simulated Inverters
    my_inverter = Inverter()
    inverted_bits = [my_inverter([bit]) for bit in bit_list]

    # Step B: Wire up an adder to add 1
    adder = NBitAdderWithCarryOut(nbits)
    
    # Step B: Add 0, but set the Carry-In pin to 1
    zero_bits = [0 for _ in range(nbits)]
    overflow_carry, final_bits = adder(inverted_bits, zero_bits, last_carry_in=1)
    return final_bits

def int_to_8bit_list(num):
    return int_to_nbit_list(num, nbits=8)

def int_to_16bit_list(num):
    return int_to_nbit_list(num, nbits=16)

def bit_list_to_int(bit_list, signed=True):
    """Converts a bit list (MSB at index 0) back to a standard integer."""
    bin_str = "".join(str(bit) for bit in bit_list)
    val = int(bin_str, 2)
    # If we are treating this as a signed Two's Complement number...
    if signed:
        msb = bit_list[0]
        if msb == 1:
            # If MSB is 1, it's negative.
            val = val - (1 << len(bit_list)) 
    return val

# ----------------- chapter 14 end -----------------
# ----------------- chapter 16 start -----------------
class NBitAdderWithOverflow:
    """
    Implement n bits fulladder with carry out flag:
        Adding n bits with carry produces n bits sum, carry bit and overflow bit.
    
    Refer to Charles Petzold's 'Code': https://codehiddenlanguage.com/Chapter16/.
    This implement same with page 210 of the book.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.fulladders = [FullAdder() for _ in range(self.nbits)]
        # below gate use for overflow
        self.inverter = Inverter()
        # AND gate detects an overflow condition for negative numbers.
        # the sign bit of x and y inputs are both 1 and the sign of the sum is 0.
        self.and_gate = AND(nin=3)
        # NOR gate detects an overflow condition for positive numbers.
        # the sign bit of x and y inputs are both 0 and the sign of the sum is 1.
        self.nor_gate = NOR(nin=3)
        self.or_gate = OR(nin=2)        
        # FIXME: should return from __call__, because gate no memory.
        self.carry_out = -1

    def __call__(self, x, y, last_carry_in=0):
        assert len(x) == self.nbits and len(y) == self.nbits, f"Inputs must be {self.nbits} bits long"
        final_sums = []
        final_carrys = last_carry_in

        # Iterate backwards: start from the far right and move left
        for idx in reversed(range(self.nbits)):
            carry_in = final_carrys
            a = x[idx]
            b = y[idx]
            # Run the Full Adder for this column
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            final_carrys = carry_out
            final_sums = [sum_out] + final_sums
        # The final carry out of the MSB is still sitting at index 0
        self.carry_out = final_carrys
        # we return third result that reflect overflow use two-complement
        invert_msb_of_final_sum = self.inverter([final_sums[0]])
        msb_of_x = x[0]
        msb_of_y = y[0]
        out_of_and_gate = self.and_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        out_of_nor_gate = self.nor_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        overflow = self.or_gate([out_of_and_gate, out_of_nor_gate])
        # overflow just test MSB bit whether is 1 for two positive and 0 for two negative
        return overflow, final_sums

    # carry_out just test whether result can use self.nbits to represent.
    def get_carry_out(self):
        return self.carry_out
# ----------------- chapter 16 end -----------------
# ----------------- chapter 17 start -----------------
class Oscillator:
    """
    Simulates a simple system clock that alternates between 0 and 1.
    Based on Charles Petzold's 'Code' (Chapter 17, Page 213).
    """
    def __init__(self):
        self.state = 0

    def level(self):
        return self.state
        
    def tick(self):
        # Time moves forward one step
        self.state = 1 - self.state
        return self.state

class ResetSetFlipFlop:
    """
    Simulates an SR (Set-Reset) Latch.
    Latches are level-sensitive storage elements that can hold one bit of memory.
    Based on Charles Petzold's 'Code' (Chapter 17, Page 220).

    The key limitation of the basic SR latch is its potential illegal condition 
    **when both set and reset inputs are asserted simultaneously**.
    This combination drives the latch into an unstable state,
    creating ambiguity and possible race conditions.
    https://www.wevolver.com/article/understanding-the-sr-latch-theory-design-truth-tables-and-practical-implementations?utm_source=chatgpt.com
    """
    def __init__(self):
        self.nin = 2
        self.nor_gate1 = NOR()
        self.nor_gate2 = NOR()
        # Default state
        self.q = 0
        self.q_bar = 1

    def getQ(self):
        return self.q

    def getQ_bar(self):
        return self.q_bar
    
    def __call__(self, x):
        assert len(x) == self.nin, "RS_FlipFlop takes exactly 2 inputs"
        r, s = x
        
        # NOTE:
        # The 'while True' loop mimics physical electron bouncing.
        # It loops until the outputs stabilize (meaning the gates stop changing).
        while True:
            old_q = self.q
            old_q_bar = self.q_bar
        
            self.q = self.nor_gate1([r, self.q_bar])
            self.q_bar = self.nor_gate2([s, self.q])
        
            if self.q == old_q and self.q_bar == old_q_bar:
                break
        return self.q, self.q_bar

class LevelTriggeredDTypeFlipFlop:
    """
    Simulates a Level-Triggered D-Type Latch.
    Data is captured only when the clock level is high (1).
    Based on Charles Petzold's 'Code' (Chapter 17, Page 225).
    """
    def __init__(self):
        self.nin = 2
        self.invert = Inverter()
        self.and_gate1 = AND()
        self.and_gate2 = AND()
        self.rs_flipflop = ResetSetFlipFlop()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]
        
        not_data = self.invert([data])
        r_wire = self.and_gate1([not_data, clock])
        s_wire = self.and_gate2([data, clock])
        
        q, q_bar = self.rs_flipflop([r_wire, s_wire])
        return q, q_bar

class EdgeTriggeredDTypeFlipFlop:
    """
    Simulates an Edge-Triggered D-Type Flip-Flop.
    Data is captured ONLY exactly when the clock transitions from 0 to 1 (Rising Edge).
    Based on Charles Petzold's 'Code' (Chapter 17, Page 229).
    """
    def __init__(self):
        self.nin = 2
        self.level_d_latchs_stage1 = LevelTriggeredDTypeFlipFlop()
        self.level_d_latchs_stage2 = LevelTriggeredDTypeFlipFlop()
        self.invert1 = Inverter()

    def getQ(self):
        return self.level_d_latchs_stage2.getQ()

    def getQ_bar(self):
        return self.level_d_latchs_stage2.getQ_bar()
        
    def __call__(self, x):
        """
        Executes one hardware tick for the flip-flop.
        
        NOTE (Hardware Physics: Setup & Hold Time): 
        Changing the Data pin at the exact same microsecond the Clock pin rises 
        creates a race condition. 
        
        Example of a violation:
        my_flipflop([0, 0]) # D = 0, CLK = 0. Internal latches prime to 0.
        my_flipflop([1, 1]) # D = 0, CLK = 0 -> 1. Race condition!
        
        Because simulated electrons take time to route through the gates, the 
        internal latches will still trigger using the old '0' state. 
        Rule: Data must remain stable before and during the clock's rising edge.
        """
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]
        
        not_clk = self.invert1([clock])
        q1, q_bar1 = self.level_d_latchs_stage1([data, not_clk])
        q2, q_bar2 = self.level_d_latchs_stage2([q1, clock])
        return q2, q_bar2

class LevelTriggeredDTypeFlipFlopWithClear:
    """
    Simulates a Level-Triggered D-Type Latch with a Clear pin.
    NOTE: This implementation slightly differs from the book (Page 238) 
    by adding an inverter to protect the set pin from conflict.
    """
    def __init__(self):
        self.nin = 3 # data, clk, clr
        self.invert_data = Inverter()
        self.invert_clr = Inverter()
        
        self.and_gate_r = AND(2)
        self.and_gate_s = AND(3)
        self.or_gate = OR()
        self.rs_flipflop = ResetSetFlipFlop()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) in (self.nin, self.nin - 1), f"Expected {self.nin} or {self.nin - 1} inputs"
        if len(x) == self.nin:
            data, clock, clr = x
        else:
            data, clock = x
            clr = 0
            
        not_data = self.invert_data([data])
        not_clr = self.invert_clr([clr])

        and_r = self.and_gate_r([not_data, clock])
        r_wire = self.or_gate([clr, and_r])
        s_wire = self.and_gate_s([data, clock, not_clr])
        
        q, q_bar = self.rs_flipflop([r_wire, s_wire])
        return q, q_bar

class NBitLevelTriggeredDTypeFlipFlopWithClear:
    """
    Simulates an N-bit wide Register using Level-Triggered D-Type Latches.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.level_d_latchs = [LevelTriggeredDTypeFlipFlopWithClear() for _ in range(self.nbits)]
    
    def getQ(self):
        return [latch.getQ() for latch in self.level_d_latchs]

    def getQ_bar(self):
        return [latch.getQ_bar() for latch in self.level_d_latchs]

    def __call__(self, datas, clk, clr=0):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"        
        qs = []
        for idx in range(self.nbits):
            q, q_bar = self.level_d_latchs[idx]([datas[idx], clk, clr])
            qs.append(q)
        return qs

class ResetSetFlipFlop4Input:
    """
    A subcomponent: An SR Latch that accepts 4 inputs (R0, R1, S0, S1).
    Used to build complex Edge-Triggered Flip-Flops.
    """
    def __init__(self):
        self.nin = 4
        self.rs_flipflop = ResetSetFlipFlop()
        self.or_gate1 = OR()
        self.or_gate2 = OR()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) == self.nin, f"RS_FlipFlop takes exactly {self.nin} inputs"
        r0, r1, s0, s1 = x
        r = self.or_gate1([r0, r1])
        s = self.or_gate2([s0, s1])
        q, q_bar = self.rs_flipflop([r, s])
        return q, q_bar

class EdgeTriggeredDTypeFlipFlopWithPresetAndClear:
    """
    Simulates an Edge-Triggered D-Type Flip-Flop with asynchronous Preset and Clear.
    Based on Charles Petzold's 'Code' (Chapter 17, Page 238).
    """
    def __init__(self):
        self.nin = 4
        self.rs_flipflop1 = ResetSetFlipFlop4Input()
        self.rs_flipflop2 = ResetSetFlipFlop4Input()
        self.rs_flipflop3 = ResetSetFlipFlop4Input()
        self.invert1 = Inverter()

    # NOTE: page 368 use this interface for timing of the cpu    
    def Reset(self):
        self.__call__([0, 0, 0, 1]) # D = 0, CLK = 0, PRE = 0, CLR = 1

    def getQ(self):
        return self.rs_flipflop3.getQ()

    def getQ_bar(self):
        return self.rs_flipflop3.getQ_bar()

    def __call__(self, x):
        """
        Executes one hardware tick for the flip-flop.
        
        NOTE (Hardware Physics: Setup & Hold Time): 
        Changing the Data pin at the exact same microsecond the Clock pin rises 
        creates a race condition. 
        
        Example of a violation:
        my_flipflop([1, 0, 0, 0]) # D = 1, CLK = 0. Internal latches prime to 1.
        my_flipflop([0, 1, 0, 0]) # D = 0, CLK = 0 -> 1. Race condition!
        
        Because simulated electrons take time to route through the gates, the 
        internal latches will still trigger using the old '1' state. 
        Rule: Data must remain stable before and during the clock's rising edge.
        """
        assert len(x) in (self.nin, self.nin-2), f"Expected {self.nin} inputs"
        
        # Unpack inputs safely
        if len(x) == self.nin:
            data, clock, preset, clear = x
        else:
            data, clock = x
            preset, clear = 0, 0

        not_clk = self.invert1([clock])
        
        # Loop until the circuit stabilizes (electrons finish routing)
        while True:
            # 1. Snapshot the old reality
            old_q1, old_q_bar1 = self.rs_flipflop1.getQ(), self.rs_flipflop1.getQ_bar()
            old_q2, old_q_bar2 = self.rs_flipflop2.getQ(), self.rs_flipflop2.getQ_bar()
            old_q3, old_q_bar3 = self.rs_flipflop3.getQ(), self.rs_flipflop3.getQ_bar()
            
            # NOTE: swap FF1 with FF2 will lead potential bug.
            # 2. Let electricity flow (SEQUENCE CHANGED FOR SETUP STRICTNESS)
    
            # Evaluate FF2 FIRST: The Clock triggers this gate to lock out FF1.
            self.rs_flipflop2([clear, old_q_bar1, preset, not_clk])
            
            # Evaluate FF1 SECOND: The Data tries to enter, but FF2's output might block it.
            self.rs_flipflop1([self.rs_flipflop2.getQ_bar(), not_clk, data, preset])
            
            # Evaluate FF3 LAST: The final output latch.
            q3, q_bar3 = self.rs_flipflop3([clear, self.rs_flipflop2.getQ_bar(), self.rs_flipflop1.getQ(), preset])

            # 3. Check if any gates changed state. If everything is the same, we are stable.
            if (old_q1 == self.rs_flipflop1.getQ() and old_q_bar1 == self.rs_flipflop1.getQ_bar() and 
                old_q2 == self.rs_flipflop2.getQ() and old_q_bar2 == self.rs_flipflop2.getQ_bar() and 
                old_q3 == self.rs_flipflop3.getQ() and old_q_bar3 == self.rs_flipflop3.getQ_bar()):
                break
                
        return q3, q_bar3

class NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear:
    """
    Simulates an N-bit wide Register using Edge-Triggered Flip-Flops.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.flip_flops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]

    def SetMaxData(self):
        for ff in self.flip_flops:
            ff([0, 0, 1, 0]) # PRE = 1, CLR = 0
    
    def SetData(self, data):
        for idx, ff in enumerate(self.flip_flops):
            if data[idx] == 1:
                ff([0, 0, 1, 0]) 
            else:
                ff([0, 0, 0, 1]) 

    def getQ(self):
        return [ff.getQ() for ff in self.flip_flops]
    
    def getQ_bar(self):
        return [ff.getQ_bar() for ff in self.flip_flops]

    def __call__(self, datas, clk, preset=0, clr=0):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        qs = []
        for idx in range(self.nbits):
            q, q_bar = self.flip_flops[idx]([datas[idx], clk, preset, clr])
            qs.append(q)
        return qs

class NBitsAccumulator:
    """
    Simulates an N-Bit Accumulator (Adder + Register loop).
    Based on Charles Petzold's 'Code' (Chapter 17, Page 231).
    
    NOTE (Clock Abstraction): 
    In a fully wired CPU, this component would not manually toggle 
    its own clock pulses. The `clk` signal would be passed in as a 
    parameter from the global Control Unit. We simulate the full 
    rising/falling edge cycle (0 -> 1 -> 0) internally here to make 
    the component easier to test in isolation.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.adder = NBitAdderWithOverflow(self.nbits)
        self.register = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.current_memory = [0 for _ in range(self.nbits)]

    def get_register(self):
        return self.current_memory

    def __call__(self, inputs_sequence):
        for data_in in inputs_sequence:
            assert len(data_in) == self.nbits, f"Data bus must be {self.nbits} bits long"
            
            # 1. Adder combines incoming data with current memory
            overflow, sum_bits = self.adder(data_in, self.current_memory)

            # 2. Toggle the clock to lock in the new sum
            self.register(sum_bits, 0)
            self.current_memory = self.register(sum_bits, 1) # RISING EDGE
            self.register(sum_bits, 0)
            
        return self.current_memory

    def clear(self):
        """
        Clears the accumulator using pure hardware math.
        X + NOT(X) + 1 = 0
        """
        my_inverter = Inverter()
        inverted_memory = [my_inverter([bit]) for bit in self.current_memory]
        overflow, sum_bits = self.adder(inverted_memory, self.current_memory, last_carry_in=1)

        self.register(sum_bits, 0)
        self.current_memory = self.register(sum_bits, 1) # RISING EDGE
        self.register(sum_bits, 0) 

# ----------------- chapter 17 end -----------------
# ----------------- chapter 19 start -----------------
class NBitsMemory:
    """
    one time store nbits data, not flexible but simple to implement.
    """
    def __init__(self, n_bits):
        self.n_bits = n_bits
        self.latches = [LevelTriggeredDTypeFlipFlopWithClear() for _ in range(n_bits)]
    
    def __call__(self, data, write_enable):
        assert len(data) == self.n_bits, f"Data bus must be {self.n_bits} bits long"
        assert write_enable in [0, 1], f"Write enable must be 0 or 1"
        # data[0] is the MSB, data[-1] is the LSB
        for i in range(self.n_bits):
            self.latches[i]([data[i], write_enable])  # D = data[i], CLK = write_enable

    def read(self):
        bits = [bit.getQ() for bit in self.latches]
        return bits # return MSB first, LSB last
    
class Decoder_3_8:
    """
    A 3-to-8 Decoder with an Enable Pin.
    Translates a 3-bit binary address into exactly one active output line (out of 8).
    Acts as the row-selector for memory banks. If Enable=0, all outputs remain 0.
    """
    def __init__(self, nin=3, nout=8):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        # We now use 4-input AND gates: 3 for address, 1 for the Enable pin
        self.and_gates = [AND(4) for _ in range(self.nout)] 

    def __call__(self, address, enable=1):
        assert len(address) == self.nin, "Input must be 3 bits long"

        idxs = [[(i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(self.nout)]
        address = [[address[i]] for i in range(len(address))] 
        output = [0] * self.nout
        # =====================================================================
        # EDUCATIONAL NOTE: HARDWARE WIRING vs. SOFTWARE LOOPS
        # In physical hardware, there are no "if" statements. The wires are 
        # permanently soldered to either the raw input or the Inverter output. 
        # The loop below is just a "virtual breadboard" to automate this wiring:
        #
        # output[0] = self.and_gates[0]([enable, self.inverters[0](address[0]), self.inverters[1](address[1]), self.inverters[2](address[2])]) # 000 -> index 0
        # output[1] = self.and_gates[1]([enable, self.inverters[0](address[0]), self.inverters[1](address[1]), address[2][0]])                 # 001 -> index 1
        # output[2] = self.and_gates[2]([enable, self.inverters[0](address[0]), address[1][0],                 self.inverters[2](address[2])]) # 010 -> index 2
        # output[3] = self.and_gates[3]([enable, self.inverters[0](address[0]), address[1][0],                 address[2][0]])                 # 011 -> index 3
        # output[4] = self.and_gates[4]([enable, address[0][0],                 self.inverters[1](address[1]), self.inverters[2](address[2])]) # 100 -> index 4
        # output[5] = self.and_gates[5]([enable, address[0][0],                 self.inverters[1](address[1]), address[2][0]])                 # 101 -> index 5
        # output[6] = self.and_gates[6]([enable, address[0][0],                 address[1][0],                 self.inverters[2](address[2])]) # 110 -> index 6
        # output[7] = self.and_gates[7]([enable, address[0][0],                 address[1][0],                 address[2][0]])                 # 111 -> index 7
        # =====================================================================
        for i, idx in enumerate(idxs):
            input_and = [enable] # The Enable pin is the first input to the AND gate!
            
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            output[i] = self.and_gates[i](input_and)
            
        return output


class Selector_8_1:
    """
    An 8-to-1 Multiplexer (Selector).
    Takes 8 input data lines and a 3-bit address. Uses the address to 
    funnel exactly one of those input lines to the single output line.
    """
    def __init__(self, nin=3, nout=8):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)]
        self.or_gate = OR(self.nout)
    
    def __call__(self, address, out_from_memory):
        assert len(address) == self.nin, "Input must be 3 bits long"

        # Dynamically generate all 8 possible binary states: 000 to 111
        idxs = [[(i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(self.nout)]
        address = [[address[i]] for i in range(len(address))] 
        output = [0] * self.nout
        
        for i, idx in enumerate(idxs):
            input_and = [out_from_memory[i]] # The data from the memory cell
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            output[i] = self.and_gates[i](input_and)
        # Combine all filtered lines (only the selected one will pass its data through)
        out = self.or_gate(output)
        return [out]

class Decoder_4_16:
    """
    A 4-to-16 Decoder.
    Translates a 4-bit hexadecimal address (0x0 to 0xF) into 16 distinct output wires.
    """
    def __init__(self, nin = 4, nout = 16):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
        """Combines the decoded address lines with the global Write Enable pin."""
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        # This function will take the write signal and the inputs, and return the output of the AND gate
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs

    def __call__(self, address):
        assert len(address) == self.nin, "Input must be 4 bits long"
        idxs = [[(i >> 3) & 1, (i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(self.nout)]
        address = [[address[i]] for i in range(len(address))]
        output = [0] * self.nout
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            output[i] = self.and_gates[i](input_and)
        return output

class Selector_16_1:
    """A 16-to-1 Multiplexer (Selector)."""
    def __init__(self, nin = 4, nout = 16):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(5) for _ in range(self.nout)]
        self.or_gate = OR(self.nout)

    def __call__(self, address, out_from_memory):
        assert len(address) == self.nin, f"Input must be {self.nin} bits long"
        assert len(out_from_memory) == self.nout, f"Out_from_memory must be {self.nout} bits long"
        idxs = [[(i >> 3) & 1, (i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(self.nout)]
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
        output = [0] * self.nout
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            output[i] = self.and_gates[i]([out_from_memory[i]] + input_and)  # outdata is the first input to the AND gate
        out = self.or_gate(output)
        return [out]


class RAM_16_1:
    """A 16x1 Memory Chip (16 words, 1 bit per word)."""
    def __init__(self):
        self.capacity = 16  # 8 words
        self.word_size = 1  # 1 bit per word

        self.decoder = Decoder_4_16()
        self.memory_cells = [NBitsMemory(self.word_size) for _ in range(self.capacity)]  # 8 words of 1 bit each
        self.selector = Selector_16_1()

    def __call__(self, address, data_in, write):
        assert len(address) == 4, "Address must be 4 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        
        # Use the decoder to determine which memory cell to write to
        write_lines = self.decoder(address)
        write_lines = self.decoder.write(write_lines, write)

        for i in range(self.capacity):
            self.memory_cells[i](data_in, write_lines[i])  # Write data to the selected memory cell

    def read(self, address):
        # Read from all memory cells and use the selector to get the output from the selected cell
        out_from_memory = [cell.read()[0] for cell in self.memory_cells]  # Get the output from all memory cells
        return self.selector(address, out_from_memory)  # Select the output from the addressed cell

class RAM_16_8:
    """A 16x8 Memory Chip (16 Bytes total)."""
    def __init__(self, word_size=8):
        self.capacity = 16  # 16 words
        self.word_size = word_size
        self.ram_16_1_cells = [RAM_16_1() for _ in range(self.word_size)]  # 16 words of 8 bits each
        
    def __call__(self, address, data_in, write):
        assert len(address) == 4, "Address must be 4 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        for bit in range(self.word_size):
            self.ram_16_1_cells[bit](address, [data_in[bit]], write)  # Write each bit to the selected memory cell

    def read(self, address):
        bits = []
        for bit in range(self.word_size):
            bits += self.ram_16_1_cells[bit].read(address)
        return bits

class RAM_64KB:
    """
    64-Kilobyte Memory Bank.
    Uses a 16-bit address bus to navigate 65,536 bytes of memory.
    Architecture:
        - Top 12 bits are decoded to act as "Chip Select" lines for 4,096 RAM_16_8 chips.
        - Bottom 4 bits select the exact byte within the active chip.
    Includes a Tri-State Buffer output to safely share the main Data Bus.
    """
    def __init__(self, word_size=8):
        self.capacity = 65536
        self.word_size = word_size
        self.ram_16_8_cells = [RAM_16_8() for _ in range(self.capacity // 16)]  # Each RAM_16_8 can handle 16 addresses
        self.decoder0 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[0:4]
        self.decoder1 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[4:8]
        self.decoder2 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[8:12]
        self.tri = TriStateBuffer(self.word_size)

    def _get_active_chip_index(self, address):
        """Helper to compute which of the 4,096 chips is selected."""
        out0 = self.decoder0(address[:4])
        out1 = self.decoder1(address[4:8])
        out2 = self.decoder2(address[8:12])
        
        idx0 = [i for i, val in enumerate(out0) if val == 1]
        idx1 = [i for i, val in enumerate(out1) if val == 1]
        idx2 = [i for i, val in enumerate(out2) if val == 1]
        
        assert len(idx0) == 1 and len(idx1) == 1 and len(idx2) == 1, "Decoder error: Multiple Chip Select lines active!"
        return (idx0[0] << 8) | (idx1[0] << 4) | idx2[0]
    
    def __call__(self, address, data_in, write):
        assert len(address) == 16, "Address must be 16 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        chip_idx = self._get_active_chip_index(address)
        self.ram_16_8_cells[chip_idx](address[12:], data_in, write)

    def read(self, address, enable=1):
        # =====================================================================
        # EDUCATIONAL NOTE: THE MEMORY WALL (Why RAM is "Slow")
        # In Python, reading from an array is instant. In physical silicon, 
        # reading from a 64KB RAM array is a grueling physical journey:
        #
        # 1. The Address Delay: The address bits must physically propagate 
        #    down the copper bus to the 4-to-16 Decoders.
        # 2. The Wake-Up Delay: The decoders trigger a cascade of AND gates 
        #    to blast voltage into ONE specific 16x8 memory chip.
        # 3. The Selector Delay: The tiny voltage from the memory latch must 
        #    physically push its way through the Selector's multiplexer tree.
        # 4. The Bus Delay: Finally, the Tri-State Buffer must push enough 
        #    current to flip the voltage on the massive global Data Bus.
        #
        # This RC (Resistance-Capacitance) delay means RAM is incredibly slow 
        # compared to the CPU. The larger the RAM, the longer the wires, and 
        # the worse the delay!
        # =====================================================================
        chip_idx = self._get_active_chip_index(address)
        outputs = self.ram_16_8_cells[chip_idx].read(address[12:])
        return self.tri(outputs, enable)

# ----------------- chapter 19 start -----------------
# ----------------- chapter 20 start -----------------

class Decoder_2_4_V2:
    """
    A 2-to-4 Decoder (Forward Mapping).
    Takes 2 input bits and decodes them into 4 output lines.
    Input 00 -> output[0] is 1
    Input 11 -> output[3] is 1
    
    Crucial for the final CPU Control Unit (Chapter 23).
    """
    def __init__(self, nin=2, nout=4):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(2) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
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
                    
            # FORWARD MAPPING: 00 -> index 0
            output[i] = self.and_gates[i](input_and)
            
        return output

# ----------------- chapter 20 end -----------------
# ----------------- chapter 21 start -----------------
class Logic:
    """
    Simulates the Logic sub-unit of the ALU.
    Executes bitwise AND, XOR, and OR operations based on the F2_0 control signals.
    """
    def __init__(self, nin_data=8, nin_control=3):
        self.nin_data = nin_data
        self.nin_control = nin_control

        self.and_gates_of_input = [AND(2) for _ in range(self.nin_data)]
        self.xor_gates_of_input = [XOR() for _ in range(self.nin_data)]
        self.or_gates_of_input = [OR(2) for _ in range(self.nin_data)]

        self.and_gate_of_enable_and = AND(3)
        self.and_gate_of_enable_xor = AND(3)
        self.and_gate_of_enable_or = AND(3)

        self.invert_gate_of_f0 = Inverter()
        self.invert_gate_of_f1 = Inverter()

        self.enable_and_output = 0
        self.enable_xor_output = 0
        self.enable_or_output = 0

    def __call__(self, input_A, input_B, F2_0):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F2_0) == self.nin_control, f"Input must be {self.nin_control} bits long"

        invert_of_f0 = self.invert_gate_of_f0([F2_0[-1]])
        invert_of_f1 = self.invert_gate_of_f1([F2_0[-2]])

        self.enable_and_output = self.and_gate_of_enable_and([invert_of_f0, invert_of_f1, F2_0[0]])
        self.enable_xor_output = self.and_gate_of_enable_xor([F2_0[-1], invert_of_f1, F2_0[0]])
        self.enable_or_output = self.and_gate_of_enable_or([invert_of_f0, F2_0[1], F2_0[0]])

        output = []
        
        # FIXME (Hardware Physics Violation):
        # In real silicon, ALL logic gates (AND, OR, XOR) evaluate simultaneously. 
        # Their outputs are routed to a shared local bus through Tri-State Buffers.
        # Software `if/elif` prevents the other gates from running. To be 100% physically 
        # accurate, this should be replaced by 3 Tri-State Buffers feeding a mini DataBus.
        if self.enable_and_output:
            for idx, and_gate in enumerate(self.and_gates_of_input):
                output.append(and_gate([input_A[idx], input_B[idx]]))

        elif self.enable_xor_output:
            for idx, xor_gate in enumerate(self.xor_gates_of_input):
                output.append(xor_gate([input_A[idx], input_B[idx]]))
                
        elif self.enable_or_output:
            for idx, or_gate in enumerate(self.or_gates_of_input):
                output.append(or_gate([input_A[idx], input_B[idx]]))
        else:
            # If not selected (e.g., ALU is doing Addition), output 8 dead wires
            output = [0] * self.nin_data

        return output
    
class Add_Subtract:
    """
    Simulates the Arithmetic sub-unit of the ALU.
    Handles ADD, ADC (Add with Carry), SUB, and SBB (Subtract with Borrow).
    """
    def __init__(self, nin_data=8, nin_control=2):
        self.nin_data = nin_data
        self.nin_control = nin_control

        # ones' complement
        self.xor_gates_for_complements = [XOR() for _ in range(self.nin_data)]

        self.adder = NBitAdderWithOverflow(self.nin_data)

        self.invert_gate_of_f0 = Inverter()
        self.and_gate_of_f0_CY_in = AND(2)
        self.and_gate_of_f0_f1 = AND(2)
        self.or_gate_of_CI = OR(2)

        # NOTE: This implementation differs slightly from the circuit shown in the book.
        # For subtraction operations, both Carry-In (CY_in) and Carry-Out (CY_out)
        # are treated as inverted signals.
        # In particular, the entry in the lower-right corner of the table on page 322
        # should be interpreted as CY_bar (inverted carry) for subtract with borrow.
        self.xor_for_cy = XOR()

    def __call__(self, input_A, input_B, F1_0, CY_In=0):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F1_0) == self.nin_control, f"Input must be {self.nin_control} bits long"

        invert_of_f0 = self.invert_gate_of_f0([F1_0[1]])
        invert_flag = F1_0[0]
        
        CI_flag = self.or_gate_of_CI([
            self.and_gate_of_f0_CY_in([F1_0[1], self.xor_for_cy([CY_In, F1_0[0]])]), 
            self.and_gate_of_f0_f1([invert_of_f0, F1_0[0]])
        ])
        
        outputs_from_complements_of_one = []
        for idx, xor_gate in enumerate(self.xor_gates_for_complements):
            outputs_from_complements_of_one.append(xor_gate([invert_flag, input_B[idx]]))
        operand_B = outputs_from_complements_of_one

        overflow, sum_bits = self.adder(input_A, operand_B, CI_flag)
        
        # Invert the physical Carry Out back into a logical Borrow Out
        carry_out = self.xor_for_cy([self.adder.get_carry_out(), F1_0[0]])

        return carry_out, sum_bits

class ALU:
    """
    The full Arithmetic Logic Unit.
    Combines the Logic unit, the Add/Sub unit, and the Flag Registers.
    Routes data via an internal DataBus and Tri-State Buffers.
    """
    def __init__(self, nin_data=8, nin_control_signal=3):
        self.nin_data = nin_data
        self.nin_control = nin_control_signal

        self.add_and_subtract = Add_Subtract(self.nin_data, self.nin_control-1)
        self.logic = Logic(self.nin_data, self.nin_control)

        self.enable_add_or_sub = 0

        # flags[0]: Sign(S), flags[1]: Zero(Z), flags[2]: Carry(CY)
        self.flags_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)
        self.result_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)

        self.invert_of_f2 = Inverter()
        self.and_gate_of_f0_f1 = AND()
        self.or_gate_of_invert_of_f2_other = OR()
        self.and_gate_of_cy_out_other = AND()

        self.nor_gates_of_flags = NOR(self.nin_data)

        self.tri_add_sub = TriStateBuffer(self.nin_data)
        # input_A, add/sub output and logic output
        self.data_bus = DataBus(num_buffers=3, nbits=self.nin_data)
        self.tri_result = TriStateBuffer(self.nin_data)

        self.and_gate_of_f0_f1_f2 = AND()
        self.and_gate_cy_in = AND()
        self.tri_acc = TriStateBuffer(self.nin_data)

        self.and_used_in_zero_flag_0 = AND()
        self.and_used_in_zero_flag_1 = AND()
        self.invert_used_in_zero_flag_0 = Inverter()
        self.or_used_in_zero_flag_0 = OR()

    def read_flags(self):
        return self.flags_latch.getQ()[:3]
    
    def read_out(self, enable):
        assert enable in [0, 1], f"enable signal must be 0 or 1"
        return self.tri_result(self.result_latch.getQ(), enable)

    # A comes from Acc of RA, B comes from out of data bus, output is send to data bus and Acc too. (page 345)
    # below function according page 332
    def __call__(self, input_A, input_B, F2_0, clock):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F2_0) == self.nin_control, f"Input must be {self.nin_control} bits long"
        assert clock in [0, 1], f"clock signal must be 0 or 1"

        invert_of_f2 = self.invert_of_f2([F2_0[0]])
        self.enable_add_or_sub = invert_of_f2
        and_of_f1_f0 = self.and_gate_of_f0_f1([F2_0[1], F2_0[2]])

        # NOTE (Hardware Physics): "The Hidden Subtraction"
        # If F2, F1, F0 = 111, this is a COMPARE instruction.
        # The ALU performs a subtraction to calculate the flags, but enables the 
        # original Accumulator (Input A) to pass through to the result bus!
        self.enable_acc = self.and_gate_of_f0_f1_f2([and_of_f1_f0, F2_0[0]])

        or_of_and_invert_f2 = self.or_gate_of_invert_of_f2_other([invert_of_f2, and_of_f1_f0])
        flags = self.flags_latch.getQ()
        """
        But for a Compare operation, it’s also necessary to know if the result of
        the operation was zero, which indicates that the two bytes are equal to each
        other. This implies the need for another flag, called the Zero flag, which
        must be saved along with the Carry flag.

        While we’re at it, let’s add another flag, called the Sign flag. This flag is
        set if the most significant bit of the result of an operation is 1. If the number
        is in two’s complement, the Sign flag indicates whether the number is nega-
        tive or positive. The flag is 1 if the number is negative and 0 if the number
        is positive.
        """
        # CY in is set to 0 during a Compare operation
        CY_IN = self.and_gate_cy_in([flags[2], invert_of_f2]) 
        carry_out, sum_bits = self.add_and_subtract(input_A, input_B, F2_0[1:], CY_IN) 
        and_of_cy_out_or = self.and_gate_of_cy_out_other([carry_out, or_of_and_invert_f2])
        """
        new flags, if this clock operation on logic, flags should keep same instead of update.
        update: zero bit and sign flag both influenced by add/sub, compare/acc and logic
        carry flag only influenced add/sub and compare
        """
        new_flags = [0] * len(flags)
        new_flags[2] = and_of_cy_out_or

        output_of_logic = self.logic(input_A, input_B, F2_0)
        output_from_add_sub = self.tri_add_sub(sum_bits, self.enable_add_or_sub)
        output_from_acc = self.tri_acc(input_A, self.enable_acc)
        
        # Combine them on the bus. Tri-State buffers ensure only one has data!
        final_alu_result = self.data_bus([output_from_acc, output_from_add_sub, output_of_logic])
        self.result_latch(final_alu_result, clock)

        # Zero Flag Logic
        """
        for compare op: 
          1. if equal: zero flag is 1 and carry out flag is 0
          2. if A < B: carry out is 1
          3. if A > B: carry out is 0
          for sign bit, now influenced by acc, i.e., input_A
        """
        nor_from_add_sub = self.nor_gates_of_flags(sum_bits)
        and_used_in_zero_flag_0_ = self.and_used_in_zero_flag_0([nor_from_add_sub, or_of_and_invert_f2])
        nor_from_logic = self.nor_gates_of_flags(output_of_logic)
        and_used_in_zero_flag_1_ = self.and_used_in_zero_flag_1([nor_from_logic, self.invert_used_in_zero_flag_0([or_of_and_invert_f2])])
        new_flags[1] = self.or_used_in_zero_flag_0([and_used_in_zero_flag_0_, and_used_in_zero_flag_1_])
        
        # Sign Flag Logic (Determined by the MSB of the final bus result)
        new_flags[0] = final_alu_result[0]
        
        # Latch the results
        self.flags_latch(new_flags, clock)

class TriStateBuffer:
    """
    Simulates a Tri-State Buffer for an 8-bit bus using pure logic gates.
    Instead of outputting 'None' when disabled, it forces the output to all 0s.
    """
    def __init__(self, nbits=8):
        self.nbits = nbits
        self.and_gates = [AND(2) for _ in range(self.nbits)]

    def __call__(self, data_in, enable):
        output = []
        for i in range(self.nbits):
            output.append(self.and_gates[i]([data_in[i], enable]))
        return output
    
class DataBus:
    """ 
    Combines outputs from multiple Tri-State Buffers onto a single shared bus.
    Simulated using massive OR gates.
    """
    def __init__(self, num_buffers, nbits=8):
        self.nbits = nbits
        self.num_buffers = num_buffers
        # A giant OR gate for each wire on the bus. 
        # If num_buffers is 8, this builds an 8-input OR gate for each wire.
        self.or_gates = [OR(self.num_buffers) for _ in range(self.nbits)] 

    def __call__(self, list_of_buffer_outputs):
        assert len(list_of_buffer_outputs) == self.num_buffers, f"Bus expects {self.num_buffers} connections!"
        
        bus_result = []
        for i in range(self.nbits):
            bits_for_this_wire = [
                buf_out[i] if isinstance(buf_out, list) else buf_out 
                for buf_out in list_of_buffer_outputs
            ]
            bus_result.append(self.or_gates[i](bits_for_this_wire))
            
        return bus_result

# ------------------------- end ch21 ----------------------------------
# ------------------------- start ch22 ----------------------------------    
class RegisterArray:
    """
    Simulates the internal Register Array of the CPU.
    Based on Charles Petzold's 'Code' (Chapter 22, Page 344).
    
    Contains the 8-bit registers: A (Accumulator), B, C, D, E, H, and L.
    NOTE: Index 6 is intentionally missing (Select 110) because it is traditionally 
    used to trigger a read/write directly to Memory (M) instead of a register.
    """
    def __init__(self, nbits=8):
        self.nbits = nbits 
        self.decoder_clock = Decoder_3_8()
        self.decoder_enable = Decoder_3_8()

        self.latch_A = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_B = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_C = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_D = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_E = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_H = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_L = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        
        # 3-bit Selection Mapping
        self.latchs = { 0: self.latch_B, 
                        1: self.latch_C,
                        2: self.latch_D,
                        3: self.latch_E,
                        4: self.latch_H,
                        5: self.latch_L,
                        # WATCH OUT: 6 is Memory (M)
                        7: self.latch_A}
        
        self.tri_A = TriStateBuffer(self.nbits)
        self.tri_B = TriStateBuffer(self.nbits)
        self.tri_C = TriStateBuffer(self.nbits)
        self.tri_D = TriStateBuffer(self.nbits)
        self.tri_E = TriStateBuffer(self.nbits)
        self.tri_H = TriStateBuffer(self.nbits)
        self.tri_L = TriStateBuffer(self.nbits)
        
        self.tris = {   0: self.tri_B, 
                        1: self.tri_C,
                        2: self.tri_D,
                        3: self.tri_E,
                        4: self.tri_H,
                        5: self.tri_L,
                        # WATCH OUT: 6 is Memory (M)
                        7: self.tri_A}

        self.data_bus = DataBus(num_buffers=len(self.latchs), nbits=self.nbits)
        
        self.addr_nbits = 16
        self.tri_hl = TriStateBuffer(self.addr_nbits)

        self.clock_idx = [0] * (len(self.latchs) + 1) 
        self.enable_idx = [0] * (len(self.latchs) + 1) 
        self.or_gate_for_acc_clk = OR()
        self.or_gate_for_acc_read = OR()

        # Page 352: Gates to handle the 16-bit H-L register pair selection
        # self.invert_gate_hl_select = Inverter()
        self.or_gate_h_clk = OR()
        self.or_gate_l_clk = OR()
    def __call__(self, data, select, clock, addr, hl_select, hl_clock, acc_clk=0):
        """
        Writes data to a specific register based on a 3-bit select code.
        select is SI2, SI1, SI0 (Page 357).
        """
        assert len(data) == self.nbits, f"Inputs must be {self.nbits} bits long"
        assert len(select) == 3, "selects must be 3 bits long"
        assert clock in [0, 1], "clock signal must be 0 or 1"

        # The 3-to-8 decoder routes the single clock pulse to the correct register
        clock_idx = self.decoder_clock(select, enable=clock)
        assert (sum(clock_idx) == 1 and clock == 1) or ((sum(clock_idx) == 0 and clock == 0)), "FATAL: Check Decoder_3_8 input/output"

        duplicate_datas = self.duplicate_data_to_each_latch(data)
        
        # FIXME (Hardware Physics): 
        # In hardware, Tri-State buffers would block data from entering the wrong latches.
        # Software uses `if` statements here. To be 100% physically accurate, we should 
        # route the Data Bus through Tri-State Buffers before hitting the latches.
        if hl_select:
            duplicate_datas[4] = addr[:8] # Route to H latch
            duplicate_datas[5] = addr[8:] # Route to L latch
            
            # hl_clock is independent of the main register clock
            # clock_idx = len(self.clock_idx) * [0]
            clock_idx[4] = self.or_gate_h_clk([clock_idx[4], hl_clock])
            clock_idx[5] = self.or_gate_l_clk([clock_idx[5], hl_clock])
            assert (sum(clock_idx) == 2 and hl_clock == 1) or ((sum(clock_idx) == 0 and hl_clock == 0)), "FATAL: Check hl_select and hl_clock"
        # The physical OR gate for the Accumulator Clock!
        clock_idx[7] = self.or_gate_for_acc_clk([clock_idx[7], acc_clk])
            
        self.clock_idx = clock_idx
        self.write_helper(duplicate_datas, clock_idx)

    def duplicate_data_to_each_latch(self, data):
        """Hardware implicitly sends the bus data to all latches simultaneously."""
        datas = []
        for _ in range(len(self.latchs) + 1):
            datas.append(data)
        return datas
    
    def write_helper(self, datas, clock_idx):
        for idx, clk in enumerate(clock_idx):
            if idx == 6: # Watch out: index 6 is [1, 1, 0] (Memory), skip local latches
                continue
            self.latchs[idx](datas[idx], clk)

    def read_hl(self, enable_hl):
        """Outputs the 16-bit H-L pair combined onto the 16-bit address bus."""
        return self.tri_hl(self.latch_H.getQ() + self.latch_L.getQ(), enable_hl)

    def read_accumulator(self, enable=1):
        """
        enable is 'Acc Enable' (Page 357).
        Page 347 has the detailed circuit. Used to pipe Accumulator A directly to the ALU.
        """
        self.enable_idx = len(self.enable_idx) * [0]
        self.enable_idx[7] = self.or_gate_for_acc_read([enable, self.enable_idx[7]])
        assert (sum(self.enable_idx) == 1 and enable == 1) or ((sum(self.enable_idx) == 0 and enable == 0)), "FATAL: read_accumulator"
        return self.read_helper(self.enable_idx)

    def read_register(self, select, enable):
        """
        select is SO2, SO1, SO0 (Page 357).
        Uses a 3-to-8 decoder to open exactly ONE Tri-State buffer onto the data bus.
        """
        assert len(select) == 3, "selects must be 3 bits long"
        assert enable in [0, 1], "enable signal must be 0 or 1"
        
        enable_idx = self.decoder_enable(select, enable=enable)
        assert (sum(enable_idx) == 1 and enable == 1) or ((sum(enable_idx) == 0 and enable == 0)), "FATAL: Check Decoder_3_8 input/output"
        
        self.enable_idx = enable_idx
        return self.read_helper(enable_idx)
    
    def read_helper(self, enable_idx):
        list_of_buffer_outputs = []
        for idx, enab in enumerate(enable_idx):
            if idx == 6: # Watch out: index 6 is [1, 1, 0] (Memory)
                continue
            list_of_buffer_outputs.append(self.tris[idx](self.latchs[idx].getQ(), enab))

        return self.data_bus(list_of_buffer_outputs)

class InstLatch:
    """
    Holds the multi-byte instruction fetched from RAM.
    Circuit on Pages 347 and 353.
    """
    def __init__(self, nbits=8):
        self.nbits = nbits
        # Latch 1: Holds Opcode
        self.inst_latch1 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        # Latch 2: Holds Low Byte of Data/Address
        self.inst_latch2 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        # Latch 3: Holds High Byte of Data/Address
        self.inst_latch3 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        self.inst_latchs = {
            1: self.inst_latch1,
            2: self.inst_latch2,
            3: self.inst_latch3,
        }

        self.tri_2 = TriStateBuffer(self.nbits)
        self.tri_2_3 = TriStateBuffer(self.nbits * 2)
        
    def write_latch1(self, data, clock_idx):
        self.write_helper(data, 1, clock_idx)

    def write_latch2(self, data, clock_idx):
        self.write_helper(data, 2, clock_idx)

    def write_latch3(self, data, clock_idx):
        self.write_helper(data, 3, clock_idx)

    def write_helper(self, data, latch_idx, clock_idx):
        self.inst_latchs[latch_idx](data, clock_idx)

    def read_latch1(self):
        """Reads the Opcode."""
        return self.inst_latch1.getQ()

    def read_latch2(self, enable):
        """
        Sends Latch 2 to the Data Bus.
        Example: For an ADI (Add Immediate) instruction, Latch 2 holds the 
        immediate math value and must be enabled onto the data bus.
        """
        return self.tri_2(self.inst_latch2.getQ(), enable)

    def read_latch2_3(self, enable_2_3):
        """
        Sends Latches 2 and 3 to the 16-bit Address Bus.
        Example: For STA (Store Accumulator) or LDA (Load Accumulator), 
        Latches 2 and 3 form a 16-bit RAM address.
        
        NOTE (Hardware Physics): Little-Endian Byte Order! (Page 377)
        The Intel 8080 stores the least significant byte first. Therefore, 
        Latch 3 is the High Byte (MSB) and Latch 2 is the Low Byte (LSB).
        """
        return self.tri_2_3(self.inst_latch3.getQ() + self.inst_latch2.getQ(), enable_2_3)

class ProgramCounter:
    """
    16-Bit Program Counter. Circuit on Page 348.
    Holds the address of the currently executing instruction.
    """
    def __init__(self):
        self.addr_bits = 16
        self.latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.addr_bits)
        self.tri = TriStateBuffer(self.addr_bits)

    def SetMaxAddr(self):
        """Sets PC to 0xFFFF. Used right before booting so the first tick rolls over to 0x0000."""
        self.latch.SetMaxData()

    def Reset(self):
        """Sets the contents of the latch to 0x0000."""
        addrs = [0] * self.addr_bits
        self.latch.SetData(addrs)

    def SetAddr(self, addrs):
        self.latch.SetData(addrs)

    def readAddr(self, enable):
        return self.tri(self.latch.getQ(), enable)
        
    def __call__(self, addr, clk):
        self.latch(datas=addr, clk=clk)

class IncrementerDecrementer:
    """
    The 16-bit Incrementer/Decrementer (Pages 350 - 351).
    Used to quickly add 1 or subtract 1 from the Program Counter or Stack Pointer.
    """
    def __init__(self):
        self.addr_bits = 16
        self.xor_first_level = [XOR() for _ in range(self.addr_bits)]
        self.xor_second_level = [XOR() for _ in range(self.addr_bits)]
        self.and_gates = [AND() for _ in range(self.addr_bits)]
        
        self.latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.addr_bits)
        self.tri = TriStateBuffer(self.addr_bits)
        self.or_gate = OR()

    def readAddr(self, dec_enable, inc_enable):
        """
        NOTE (Hardware Physics): Ripple Carry Logic
        If inc_enable = 1, it adds 1.
        If dec_enable = 1, the XOR gates act as 1's complement inverters, 
        effectively subtracting 1 via two's complement math.
        """
        read_addrs = self.latch.getQ()
        
        v = 1 # Carry-in bit used to initiate the increment/decrement
        output_from_Inc_Dec = []
        
        # Ripple from LSB to MSB
        for idx, addr in enumerate(reversed(read_addrs)):
            output_from_Inc_Dec.append(self.xor_second_level[idx]([addr, v]))
            v = self.and_gates[idx]([self.xor_first_level[idx]([dec_enable, addr]), v])

        # Reverse the list so MSB is back at index 0
        output_from_Inc_Dec = list(reversed(output_from_Inc_Dec))

        return self.tri(output_from_Inc_Dec, self.or_gate([dec_enable, inc_enable]))

    def __call__(self, addrs, clock):
        self.latch(addrs, clock)

# ------------------------- end ch22 ----------------------------------
# ------------------------- start ch23 ----------------------------------    
class Counter4Bit:
    """
    A 4-Bit Ripple Counter.
    Used by the Control Unit to track the current Machine Cycle (1 to 6).
    """
    def __init__(self,):
        self.nbits = 4
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def SetMaxAddr(self):
        """
        Forces the counter to 1111 (15).
        NOTE: 'present' is used here as 'preset' to force the flip-flops to 1.
        """
        # 1. Assert the present wire (1) and let the hardware loop stabilize it!
        self.__call__(clk=0, clear_wire=0, present=1)
        
        # 2. De-assert the present wire (0) so the counter is ready to count again.
        self.__call__(clk=0, clear_wire=0, present=0)

    def Clear(self):
        """Asynchronously clears the counter to 0000."""
        # 1. Assert the Clear wire (1) and let the hardware loop stabilize it!
        self.__call__(clk=0, clear_wire=1, present=0)
        
        # 2. De-assert the Clear wire (0) so the counter is ready to count again.
        self.__call__(clk=0, clear_wire=0, present=0)

    def __call__(self, clk=0, clear_wire=0, present=0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset (mapped to 'present'), and clear_wire
                q, q_bar = ff([data, current_clk, present, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))
    

class ControlSignal:
    """
    The Master Control Unit of the CPU.
    Decodes the 8-bit Instruction Opcode and the 4-bit Cycle Counter to generate 
    dozens of precise enable and clock pulses across the entire motherboard.
    Follows the exact wiring schematics from Chapter 23 (Pages 366-376).
    """
    def __init__(self):
        self.nbits_of_latch = 8

        # TODO(PengChen:) V2 is ambiguous
        self.decoder_2_4_of_latch_1 = Decoder_2_4_V2()
        self.decoder_3_8_1_of_latch_1 = Decoder_3_8()
        self.decoder_3_8_2_of_latch_1 = Decoder_3_8()

        # TODO(PengChen:) for just for simple 
        self.and_gate_2_in = AND()
        self.and_gate_3_in = AND(3)

        self.invert_gate = Inverter()

        self.or_gate_3_in = OR(3)
        self.or_gate_2_in = OR()
        self.or_gate_7_in = OR(7)

        self.my_counter = Counter4Bit()
        self.decoder = Decoder_4_16()
        self.or_gate = OR()

        self.tri_buffer = TriStateBuffer(1)
        self.tri_buffer_2_in = TriStateBuffer(2)
        self.tri_buffer_1_in = TriStateBuffer(1)
        self.tri_buffer_3_in = TriStateBuffer(3)
        
        self.bus1_in_addr_bus_execute = DataBus(num_buffers=6, nbits=1)
        self.bus2_in_addr_bus_execute = DataBus(num_buffers=2, nbits=1)
        self.bus3_in_addr_bus_execute = DataBus(num_buffers=3, nbits=1)

        self.bus1_in_data_bus_execute = DataBus(num_buffers=3, nbits=1)

        self.tri_buffer_4_in = TriStateBuffer(4)

    def __call__(self, cycle_clk, pulse, reset, latch1, flags=[0]*3):
        self.my_counter(cycle_clk)
        output_of_decoder = self.decoder(self.my_counter.getQs())
        assert len(latch1) == self.nbits_of_latch

# page 366
# --------------------------------------------------------------------------------------------------
        output_of_c7_c6_p366 = self.decoder_2_4_of_latch_1(latch1[:2])
        output_of_c5_c4_c3_p366 = self.decoder_3_8_1_of_latch_1(latch1[2:5])
        output_of_c2_c1_c0_p366 = self.decoder_3_8_2_of_latch_1(latch1[5:])

        move_group_p366 = output_of_c7_c6_p366[1]
        arithmetic_logic_group_p366 = output_of_c7_c6_p366[2]
        memory_source_p366 = output_of_c2_c1_c0_p366[6]
        memory_destination_p366 = output_of_c5_c4_c3_p366[6]

        move_immediates_p366 = self.and_gate_2_in([output_of_c2_c1_c0_p366[6], output_of_c7_c6_p366[0]])
        adi_data_p366 = self.and_gate_2_in([output_of_c2_c1_c0_p366[6], output_of_c7_c6_p366[3]])

        inx_hl_p366 = self.and_gate_3_in([output_of_c2_c1_c0_p366[3], output_of_c5_c4_c3_p366[4], output_of_c7_c6_p366[0]])
        dcx_hl_p366 = self.and_gate_3_in([output_of_c2_c1_c0_p366[3], output_of_c5_c4_c3_p366[5], output_of_c7_c6_p366[0]])

        lda_p366 = self.and_gate_3_in([output_of_c2_c1_c0_p366[2], output_of_c5_c4_c3_p366[7], output_of_c7_c6_p366[0]])
        sta_p366 = self.and_gate_3_in([output_of_c2_c1_c0_p366[2], output_of_c5_c4_c3_p366[6], output_of_c7_c6_p366[0]])

# page 388: JUMP
        jmp_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[0], output_of_c2_c1_c0_p366[3]])
        jnz_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[0], output_of_c2_c1_c0_p366[2]])
        jz_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[1], output_of_c2_c1_c0_p366[2]])
        jnc_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[2], output_of_c2_c1_c0_p366[2]])
        jc_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[3], output_of_c2_c1_c0_p366[2]])
        jp_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[6], output_of_c2_c1_c0_p366[2]])
        jm_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[7], output_of_c2_c1_c0_p366[2]])
        pchl_p388 = self.and_gate_3_in([output_of_c7_c6_p366[3], output_of_c5_c4_c3_p366[5], output_of_c2_c1_c0_p366[1]])
        jump_group_p388 = self.or_gate_7_in([jmp_p388, jnz_p388, jz_p388, jnc_p388, jc_p388, jp_p388, jm_p388])
# page 367 first part
# --------------------------------------------------------------------------------------------------
        move_r_r_p367 = self.and_gate_3_in([move_group_p366, self.invert_gate([memory_source_p366]), self.invert_gate([memory_destination_p366])])
        move_r_M_p367 = self.and_gate_3_in([move_group_p366, memory_source_p366, self.invert_gate([memory_destination_p366])])
        move_M_r_p367 = self.and_gate_3_in([move_group_p366, self.invert_gate([memory_source_p366]), memory_destination_p366])

        hlt_p367 = self.and_gate_3_in([move_group_p366, memory_source_p366, memory_destination_p366])

        mvi_r_data_p367 = self.and_gate_2_in([move_immediates_p366, self.invert_gate([memory_destination_p366])])
        mvi_M_data_p367 = self.and_gate_2_in([move_immediates_p366, memory_destination_p366])

        add_r_p367 = self.and_gate_2_in([arithmetic_logic_group_p366, self.invert_gate([memory_source_p366])])
        add_M_p367 = self.and_gate_2_in([arithmetic_logic_group_p366, memory_source_p366])
# page 367 second part
# --------------------------------------------------------------------------------------------------
        fetch_2_byte_p367 = self.or_gate_3_in([mvi_r_data_p367, mvi_M_data_p367, adi_data_p366])
        fetch_3_byte_p367 = self.or_gate_3_in([lda_p366, sta_p366, jump_group_p388])
        fetch_1_byte_invert_p367 = self.or_gate_2_in([fetch_2_byte_p367, fetch_3_byte_p367])
        fetch_1_byte_p367 = self.invert_gate([fetch_1_byte_invert_p367])
        
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # +++++ UPDATE START: FIXING 2-CYCLE EXECUTE FOR INX/DCX HL           +++++
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # We must chain OR gates to include INX HL and DCX HL in the 2-cycle group!
        tmp_math_exec_2 = self.or_gate_3_in([adi_data_p366, add_r_p367, add_M_p367])
        execute_2_cycle_p367 = self.or_gate_3_in([tmp_math_exec_2, inx_hl_p366, dcx_hl_p366])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # +++++ UPDATE END                                                    +++++
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        execute_1_cycle_p367 = self.invert_gate([execute_2_cycle_p367])
# page 370
# --------------------------------------------------------------------------------------------------
        fetch_cycle_1_out_p370 = output_of_decoder[0]
        fetch_cycle_2_out_p370 = self.and_gate_2_in([output_of_decoder[2], fetch_1_byte_invert_p367])
        fetch_cycle_3_out_p370 = self.and_gate_2_in([output_of_decoder[4], fetch_3_byte_p367])
        pc_increment_p370 = self.or_gate_3_in([self.and_gate_2_in([output_of_decoder[3], fetch_1_byte_invert_p367]), output_of_decoder[1], self.and_gate_2_in([output_of_decoder[5], fetch_3_byte_p367])])
        
        # EC1 on page 373
        exec_cycle_1_out_p370 = self.or_gate_3_in([self.and_gate_2_in([output_of_decoder[2], fetch_1_byte_p367]), self.and_gate_2_in([output_of_decoder[4], fetch_2_byte_p367]), self.and_gate_2_in([output_of_decoder[6], fetch_3_byte_p367])])

        tmp_exec_cycle_2_p370 = self.or_gate_3_in([self.and_gate_2_in([output_of_decoder[3], fetch_1_byte_p367]), self.and_gate_2_in([output_of_decoder[5], fetch_2_byte_p367]), self.and_gate_2_in([output_of_decoder[7], fetch_3_byte_p367])])
        
        # EC2 on page 373
        exec_cycle_2_out_p370 = self.and_gate_2_in([tmp_exec_cycle_2_p370, execute_2_cycle_p367])
        
        tmp1_reset_p370 = self.or_gate_3_in([self.and_gate_2_in([output_of_decoder[4], fetch_1_byte_p367]), self.and_gate_2_in([output_of_decoder[6], fetch_2_byte_p367]), self.and_gate_2_in([output_of_decoder[8], fetch_3_byte_p367])])
        tmp2_reset_p370 = self.or_gate_2_in([self.and_gate_2_in([tmp_exec_cycle_2_p370, execute_1_cycle_p367]), self.and_gate_2_in([execute_2_cycle_p367, tmp1_reset_p370])])
        clear_p370 = self.or_gate_2_in([reset, tmp2_reset_p370])

        if clear_p370:
            """
            NOTE (Hardware Physics Optimization):
            Instead of clearing the counter to 0000 on reset, 
            we must pre-set it to 1111 (the maximum value). 
            This way, when the very first rising edge of the clock hits, 
            the counter "rolls over" from 1111 to 0000. 
            This perfectly locks the CPU into Fetch 1 for the first cycle!
            """
            self.my_counter.SetMaxAddr() 
            
# page 372 first part
# --------------------------------------------------------------------------------------------------
        or_of_fetch_p372 = self.or_gate_3_in([fetch_cycle_1_out_p370, fetch_cycle_2_out_p370, fetch_cycle_3_out_p370])
        program_counter_enable_p372 = or_of_fetch_p372
        
        # ATTENTION: maybe merge with other component can enable this.
        # tri_buffer is unnecessary, because enable and data is same.
        ram_data_out_enable_fetch_phrase_p372 = or_of_fetch_p372

        input_of_inc_dec_clk_p372 = self.and_gate_2_in([or_of_fetch_p372, pulse])
        inc_dec_clk_fetch_phrase_p372 = input_of_inc_dec_clk_p372

        instru_latch_1_clk_p372 = self.and_gate_2_in([fetch_cycle_1_out_p370, pulse])
        instru_latch_2_clk_p372 = self.and_gate_2_in([fetch_cycle_2_out_p370, pulse])
        instru_latch_3_clk_p372 = self.and_gate_2_in([fetch_cycle_3_out_p370, pulse])
# page 372 second part
# --------------------------------------------------------------------------------------------------
        increment_enable_fetch_phrase_p372 = pc_increment_p370
        
        input_of_program_counter_clk_fetch_phrase_p372 = self.and_gate_2_in([pc_increment_p370, pulse])
        program_counter_clk_fetch_phrase_p372 = input_of_program_counter_clk_fetch_phrase_p372

# page 373 first part
# --------------------------------------------------------------------------------------------------
        execute_pulse_1_decode_phrase_p373 = self.and_gate_2_in([exec_cycle_1_out_p370, pulse])
        execute_pulse_2_decode_phrase_p373 = self.and_gate_2_in([exec_cycle_2_out_p370, pulse])
# page 373 second part
# --------------------------------------------------------------------------------------------------
        # this halt output will go to the circuit with the oscillator
        halt_exec_phrase_p373 = self.and_gate_2_in([hlt_p367, execute_pulse_1_decode_phrase_p373])

# page 374
# --------------------------------------------------------------------------------------------------
# addr bus
        hl_enable_addr_bus_exec_phrase_1_p374, inst_latch2_3_enable_addr_bus_exec_phrase_1_p374 = self.tri_buffer_2_in([self.bus1_in_addr_bus_execute([move_r_M_p367, 
                                                                        move_M_r_p367,
                                                                        mvi_M_data_p367,
                                                                        add_M_p367,
                                                                        inx_hl_p366,
                                                                        dcx_hl_p366])[0], self.bus2_in_addr_bus_execute([lda_p366,
                                                                                                              sta_p366])[0]], exec_cycle_1_out_p370)
        inc_dec_clk_enable_addr_bus_exec_phrase_1_p374 = self.tri_buffer_1_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                           dcx_hl_p366])[0]], execute_pulse_1_decode_phrase_p373)[0]
                                                                           
        hl_select_enable_addr_bus_exec_phrase_2_p374, increment_enable_addr_bus_exec_phrase_2_p374, dec_enable_addr_bus_exec_phrase_2_p374 = self.tri_buffer_3_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                           dcx_hl_p366])[0], inx_hl_p366, dcx_hl_p366], exec_cycle_2_out_p370)
                                                                           
        hl_clk_addr_bus_exec_phrase_2_p374 = self.tri_buffer_1_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                      dcx_hl_p366])[0]], execute_pulse_2_decode_phrase_p373)[0]
        # flags[0]: Sign(S), flags[1]: Zero(Z), flags[2]: Carry(CY)
        conditional_jump_p389 = self.or_gate_7_in([self.and_gate_2_in([jnz_p388, self.invert_gate([flags[1]])]), 
                                              self.and_gate_2_in([jz_p388, flags[1]]), 
                                              self.and_gate_2_in([jnc_p388, self.invert_gate([flags[2]])]), 
                                              self.and_gate_2_in([jc_p388, flags[2]]), 
                                              self.and_gate_2_in([jp_p388, self.invert_gate([flags[0]])]), 
                                              self.and_gate_2_in([jm_p388, flags[0]]), 0])
        
        hl_enable_addr_bus_exec_phrase_1_p389, inst_latch2_3_enable_addr_bus_exec_phrase_1_p389 = self.tri_buffer_2_in([pchl_p388, self.bus2_in_addr_bus_execute([jmp_p388,
                                                                                                              conditional_jump_p389])[0]], exec_cycle_1_out_p370)

        pc_clock_addr_bus_exec_phrase_1_p389 = self.tri_buffer_1_in([self.bus3_in_addr_bus_execute([jmp_p388, 
                                                                                                    conditional_jump_p389, 
                                                                                                    pchl_p388])[0]], execute_pulse_1_decode_phrase_p373)[0]
        
        hl_enable_final = self.or_gate_2_in([hl_enable_addr_bus_exec_phrase_1_p374, hl_enable_addr_bus_exec_phrase_1_p389])
        inst_latch2_3_enable_final = self.or_gate_2_in([inst_latch2_3_enable_addr_bus_exec_phrase_1_p374, inst_latch2_3_enable_addr_bus_exec_phrase_1_p389])
        pc_clock_final = self.or_gate_2_in([program_counter_clk_fetch_phrase_p372, pc_clock_addr_bus_exec_phrase_1_p389])
        
# page 375
# --------------------------------------------------------------------------------------------------
        ra_enable_data_bus_exec_phrase_1_p375, ram_data_out_enable_data_bus_exec_phrase_1_p375, inst_latch2_enable_data_bus_exec_phrase_1_p375, acc_enable_data_bus_exec_phrase_1_p375 = self.tri_buffer_4_in([self.bus1_in_data_bus_execute([move_r_r_p367,
                                                                                                                              move_M_r_p367,
                                                                                                                              add_r_p367,
                                                                                                                              ])[0],
                                                                                                self.bus1_in_data_bus_execute([move_r_M_p367,
                                                                                                                              add_M_p367,
                                                                                                                              lda_p366,
                                                                                                                              ])[0],
                                                                                                self.bus1_in_data_bus_execute([mvi_r_data_p367,
                                                                                                                              mvi_M_data_p367,
                                                                                                                              adi_data_p366,
                                                                                                                              ])[0], sta_p366], exec_cycle_1_out_p370)
        
        ra_clk_data_bus_exec_phrase_1_p375, ram_write_enable_data_bus_exec_phrase_1_p375, alu_clk_data_bus_exec_phrase_1_p375, acc_clk_data_bus_exec_phrase_1_p375 = self.tri_buffer_4_in([self.bus1_in_data_bus_execute([move_r_r_p367,
                                                                                                move_r_M_p367,
                                                                                                mvi_r_data_p367,
                                                                                                ])[0],
                                                                self.bus1_in_data_bus_execute([move_M_r_p367,
                                                                                                mvi_M_data_p367,
                                                                                                sta_p366,
                                                                                                ])[0],
                                                                self.bus1_in_data_bus_execute([add_r_p367,
                                                                                                add_M_p367,
                                                                                                adi_data_p366,
                                                                                                ])[0], lda_p366], execute_pulse_1_decode_phrase_p373)
        
# page 376
# --------------------------------------------------------------------------------------------------
        alu_enable_data_bus_exec_phrase_2_p376 = self.tri_buffer_1_in([self.bus1_in_data_bus_execute([add_r_p367,
                                                                         add_M_p367,
                                                                         adi_data_p366,
                                                                         ])[0]], exec_cycle_2_out_p370)[0]
                                                                         
        acc_clk_data_bus_exec_phrase_2_p376 = self.tri_buffer_1_in([self.bus1_in_data_bus_execute([add_r_p367,
                                                                       add_M_p367,
                                                                       adi_data_p366,
                                                                       ])[0]], execute_pulse_2_decode_phrase_p373)[0]

        # =========================================================================================
        # NOTE (Hardware Bus Arbitration): 
        # Because we have multiple instruction phases (Fetch vs. Execute 1 vs. Execute 2) trying 
        # to drive the EXACT same physical wires (like the RAM Data Enable or ACC Clock), 
        # we MUST use OR gates to safely combine them so they don't short-circuit.
        # =========================================================================================
        
        # Happens on instruct fetch and data in phrase 1
        final_ram_data_out_enable = self.or_gate_2_in([ram_data_out_enable_fetch_phrase_p372, ram_data_out_enable_data_bus_exec_phrase_1_p375])
        
        # Happens on instruct fetch and addr bus exec phrase 1
        final_inc_dec_clk = self.or_gate_2_in([inc_dec_clk_fetch_phrase_p372, inc_dec_clk_enable_addr_bus_exec_phrase_1_p374])
        
        # Happens on instruct fetch and addr bus exec phrase 2
        final_increment_enable = self.or_gate_2_in([increment_enable_fetch_phrase_p372, increment_enable_addr_bus_exec_phrase_2_p374])
        
        # Happens on data bus phrase 1 for LDA and phrase 2 for ADD r, ADD M, and ADI Data
        final_acc_clk = self.or_gate_2_in([acc_clk_data_bus_exec_phrase_1_p375, acc_clk_data_bus_exec_phrase_2_p376])

        # Pack the Control Bus ribbon cable!
        control_bus = {
            "pc_enable": program_counter_enable_p372,
            "pc_clk": pc_clock_final, #program_counter_clk_fetch_phrase_p372,
            "inc_dec_clk": final_inc_dec_clk,
            "inc_enable": final_increment_enable,
            "dec_enable": dec_enable_addr_bus_exec_phrase_2_p374,

            "inst_latch_1_clk": instru_latch_1_clk_p372,
            "inst_latch_2_clk": instru_latch_2_clk_p372,
            "inst_latch_3_clk": instru_latch_3_clk_p372,
            "inst_latch_2_enable": inst_latch2_enable_data_bus_exec_phrase_1_p375,
            "inst_latch2_3_enable": inst_latch2_3_enable_final, #inst_latch2_3_enable_addr_bus_exec_phrase_1_p374,

            "ram_data_out_enable": final_ram_data_out_enable,
            "ram_write_enable": ram_write_enable_data_bus_exec_phrase_1_p375,

            "ra_enable": ra_enable_data_bus_exec_phrase_1_p375,
            "ra_clk": ra_clk_data_bus_exec_phrase_1_p375,
            "hl_enable": hl_enable_final, #hl_enable_addr_bus_exec_phrase_1_p374,
            "hl_select": hl_select_enable_addr_bus_exec_phrase_2_p374,
            "hl_clk": hl_clk_addr_bus_exec_phrase_2_p374,
            "acc_enable": acc_enable_data_bus_exec_phrase_1_p375,
            "acc_clk": final_acc_clk,

            "alu_enable": alu_enable_data_bus_exec_phrase_2_p376,
            "alu_clk": alu_clk_data_bus_exec_phrase_1_p375,

            "halt": halt_exec_phrase_p373,
            "clear": clear_p370
        }
        return control_bus   

class BasicTiming:
    """
    Generates the master clock and pulse signals for the CPU.
    Handles HALT and RESET interruption signals.
    """
    def __init__(self):
        self.edge_flipflop0 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.edge_flipflop1 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.edge_flipflop2 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.invert1 = Inverter()
        self.and_gate = AND()
        self.and_gate0 = AND()
        
        self.cycle_clock = 0
        self.pulse = 0
    
    def read_cycle_clk(self):
        return self.cycle_clock
    
    def read_pulse(self):
        return self.pulse
    
    def __call__(self, clock, reset=0, halt=0):
        # Hardware interrupt: Instantly clear timing flip-flops
        if reset == 1:
            self.edge_flipflop0.Reset() 
            self.edge_flipflop1.Reset()
            self.edge_flipflop2.Reset()
            return 
        
        # Halt flag flips FF0 to block the incoming oscillator clock
        self.edge_flipflop0([self.edge_flipflop0.getQ_bar(), halt])
        clock = self.and_gate0([self.edge_flipflop0.getQ_bar(), clock])

        not_clk = self.invert1([clock])

        # Frequency dividing and pulse generation logic
        self.edge_flipflop1([self.edge_flipflop1.getQ_bar(), clock])
        self.edge_flipflop2([self.edge_flipflop1.getQ(), not_clk])
        
        clk_input_to_counter = self.edge_flipflop1.getQ()
        pulse = self.and_gate([self.edge_flipflop1.getQ_bar(), self.edge_flipflop2.getQ()])
        
        self.cycle_clock = clk_input_to_counter
        self.pulse = pulse

class CPUSubSet_8080:
    """
    The Ultimate Intel 8080 CPU Subset (The Motherboard).
    Integrates all independent hardware components onto a shared Address Bus 
    and Data Bus. Driven by a central Oscillator and the Master Control Unit.
    """
    def __init__(self, data_nbits=8, addr_nbits=16):
        self.data_nbits = data_nbits
        self.addr_nbits = addr_nbits
        
        # 1. Instruction Latch (Holds Opcode and Immediates)
        self.inst_latch = InstLatch(self.data_nbits)
        # 2. Arithmetic Logic Unit (The Brain)
        self.alu = ALU(self.data_nbits)
        # 3. Register Array (A, B, C, D, E, H, L)
        self.ra = RegisterArray(self.data_nbits)
        # 4. 64-Kilobyte Random Access Memory
        self.ram = RAM_64KB(self.data_nbits)
        # 5. Program Counter (Tracks current execution address)
        self.pc = ProgramCounter()
        # 6. Incrementer / Decrementer (16-bit Math for Addresses)
        self.inc_dec = IncrementerDecrementer()

        # Timing and Control
        self.timing = BasicTiming()
        self.control = ControlSignal()

        # System Buses
        # Data Bus (Page 345 and 347): Connects RAM, ALU, RA(Standard Regs), RA(Accumulator), InstLatch2
        self.data_bus = DataBus(num_buffers=5, nbits=self.data_nbits) 
        
        # Address Bus (Page 353): Connects InstLatch 2&3, PC, Incr/Decr, RA(HL pointer)
        self.addr_bus = DataBus(num_buffers=4, nbits=self.addr_nbits) 

        self.current_halt_state = 0

    def reset(self):
        """
        Simulates pressing the physical 'RESET' button on the motherboard.
        Pulses the reset line high, then low, clearing all flip-flops in the Control Unit.
        """
        # Assert Reset High
        self.timing(clock=0, reset=1, halt=0)
        self.control(cycle_clk=0, pulse=0, reset=1, latch1=[0]*8)
        
        # Release Reset Low
        self.timing(clock=0, reset=0, halt=0)
        self.control(cycle_clk=0, pulse=0, reset=0, latch1=[0]*8)
        
    def load_program(self, program_data, start_address=0):
        """
        Hardware Programmer Helper.
        Flashes a list of binary byte instructions directly into RAM before boot.
        """
        current_addr = start_address
        for byte_val in program_data:
            addr_bits = int_to_16bit_list(current_addr)
            data_bits = int_to_8bit_list(byte_val)
            self.ram(addr_bits, data_bits, write=1)
            current_addr += 1

    def tick(self, oscillator_clk, external_reset=0):
        """
        Executes exactly ONE simulated clock tick (Rising or Falling edge).
        Evaluates the entire motherboard wiring simultaneously.
        """
        # 1. Update master timing 
        self.timing(oscillator_clk, reset=external_reset, halt=self.current_halt_state)
        cycle_clk = self.timing.read_cycle_clk()
        pulse = self.timing.read_pulse()

        # 2. Get current instruction opcode (Opcode is always stored in Latch 1)
        # NOTE (Hardware Physics): 
        # If the next cycle clock is Fetch 1, the current_opcode sitting in Latch 1 
        # is actually garbage from the previous instruction. But it's okay! The Control 
        # Unit knows this is Fetch 1 and will safely ignore the garbage opcode until 
        # it is overwritten at the end of the pulse.
        current_opcode = self.inst_latch.read_latch1()

        # 3. Control Unit calculates all bus routing signals
        signals = self.control(cycle_clk=cycle_clk, pulse=pulse, reset=external_reset, latch1=current_opcode, flags=self.alu.read_flags())

        # Helper to extract 1 or 0 from the signals dictionary securely
        def get_sig(name):
            val = signals[name]
            return val[0] if isinstance(val, list) else val
        
        # 4. ADDRESS BUS ROUTING
        # Open the specific Tri-State buffer allowed by the Control Unit
        current_address = self.addr_bus([
            self.pc.readAddr(enable=get_sig("pc_enable")),
            self.inc_dec.readAddr(dec_enable=get_sig("dec_enable"), inc_enable=get_sig("inc_enable")),
            self.ra.read_hl(enable_hl=get_sig("hl_enable")),
            self.inst_latch.read_latch2_3(enable_2_3=get_sig("inst_latch2_3_enable")),
        ])

        # 5. DATA BUS ROUTING
        # Pull data from whatever component currently owns the data bus
        current_data = self.data_bus([
            self.ram.read(current_address, enable=get_sig("ram_data_out_enable")),
            
            # NOTE: Read port uses Source Register SSS (Bits C2, C1, C0 -> [5:8])
            self.ra.read_register(select=current_opcode[5:8], enable=get_sig("ra_enable")),
            self.inst_latch.read_latch2(enable=get_sig("inst_latch_2_enable")),
            self.ra.read_accumulator(enable=get_sig("acc_enable")),                  
            self.alu.read_out(enable=get_sig("alu_enable")),                         
        ])

        # 6. EXECUTE WRITES (Clock Pulses)
        # Send the current Address Bus and Data Bus signals to all components.
        # Only the components receiving a clock pulse (1) will actually save the data.
        self.inc_dec(addrs=current_address, clock=get_sig("inc_dec_clk"))

        self.inst_latch.write_latch1(data=current_data, clock_idx=get_sig("inst_latch_1_clk"))
        self.inst_latch.write_latch2(data=current_data, clock_idx=get_sig("inst_latch_2_clk"))
        self.inst_latch.write_latch3(data=current_data, clock_idx=get_sig("inst_latch_3_clk"))

        self.pc(addr=current_address, clk=get_sig("pc_clk"))
        
        # NOTE: Write port uses Destination Register DDD (Bits C5, C4, C3 -> [2:5])        
        self.ra(data=current_data, 
                select=current_opcode[2:5], 
                clock=get_sig("ra_clk"), 
                hl_select=get_sig("hl_select"), 
                hl_clock=get_sig("hl_clk"), 
                addr=current_address,
                acc_clk=get_sig("acc_clk"))
        
        self.ram(address=current_address, data_in=current_data, write=get_sig("ram_write_enable"))         
        # =====================================================================
        # EDUCATIONAL NOTE (Hardware Physics - Page 345):
        # Notice that the B input and the Out output of the ALU are both connected 
        # to the Data Bus. However, the A input is connected directly to the Acc 
        # output of the register array! 
        # Therefore, input_A reading the accumulator is ALWAYS valid and does not 
        # need to wait for bus arbitration.
        # =====================================================================
        self.alu(input_A=self.ra.read_accumulator(enable=1), input_B=current_data, 
                 F2_0=current_opcode[2:5], clock=get_sig("alu_clk")) 

        # Handle hardware interrupts (Halt)
        self.current_halt_state = get_sig("halt")

        # --- Debug Print during the Pulse ---
        if pulse == 1 and self.current_halt_state == 0:
            pc_hex = f"{bit_list_to_int(self.pc.readAddr(enable=1), signed=False):04X}"
            op_hex = f"{bit_list_to_int(current_opcode, signed=False):02X}"
            addr_hex = f"{bit_list_to_int(current_address, signed=False):04X}"
            data_hex = f"{bit_list_to_int(current_data, signed=False):02X}"
            print(f"[PULSE] PC: {pc_hex} | AddrBus: {addr_hex} | DataBus: {data_hex} | Latch 1 (Opcode): {op_hex}")
        # self.print_value_is_1(signals)

    def print_value_is_1(self, raw_bus):
        print(f"-------------------------------------")
        for k, v in raw_bus.items():
            if v == 1:
                print(f"{k} is 1")
        print(f"-------------------------------------")
# ------------------------- end ch23 ----------------------------------