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

class FrequencyDivider:
    def __init__(self):
        self.nin = 2
        self.flipflop = EdgeTriggeredDTypeFlipFlop()

    def getQ(self):
        return self.flipflop.getQ()
        
    def getQ_bar(self):
        return self.flipflop.getQ_bar()

    def __call__(self, clk):
        data = self.flipflop.getQ_bar()
        q, q_bar = self.flipflop([data, clk])
        return q, q_bar

class NBitsFrequencyDivider:
    def __init__(self, nbits):
        self.nbits = nbits
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
    
    def getQ(self):
        return list(reversed([ff.getQ() for ff in self.flipflops]))

    def getQ_bar(self):
        return list(reversed([ff.getQ_bar() for ff in self.flipflops]))

    def __call__(self, clk = 0):
        current_clk = clk
        qs = []
        for flipflop in self.flipflops:
            data = flipflop.getQ_bar()
            q, q_bar = flipflop([data, current_clk])
            qs.append(q)
            current_clk = q_bar
        # MSB is on the left
        return list(reversed(qs))

class Counter0_9:
    """A module-10 Ripple Counter that counts from 0 to 9 and resets. """
    def __init__(self,):
        self.nbits = 4
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def __call__(self, clk = 0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 2. Wire up the Async Clear
            # ff[0] is Q0 (LSB), ff[1] is Q1, ff[2] is Q2, ff[3] is Q3 (MSB)
            # We want to clear when we hit 10 (Binary: 1010). 
            # This happens when Q3 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            clear_wire = self.and_gate([q3, q1])

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and our dynamic C';lear wire!
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class Counter0_5:
    """A module-6 Ripple Counter that counts from 0 to 5 and resets. """
    def __init__(self,):
        self.nbits = 3
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()
        
    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
        
    def __call__(self, clk = 0):
        # when the while loop runs a second time, it means
        # the circuit hasn't settled yet, but we are still
        # inside the exact same moment in time.
        # By putting current_clk = clk inside the top of 
        # the while loop, you ensure that every time you
        # re-calculate the ripple chain, you are correctly
        # starting from the external physical pin,
        # rather than accidentally passing the baton in a circle.
        # current_clk = clk

        
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 2. Wire up the Async Clear
            # ff[0] is Q0 (LSB), ff[1] is Q1, ff[2] is Q2(MSB)
            # We want to clear when we hit 6 (Binary: 110). 
            # This happens when Q2 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q2 = self.flipflops[2].getQ()
            clear_wire = self.and_gate([q2, q1])

            # 3. Propagate the clock and data through the ripple chain
            # if previous clock is 0, the current clock is 1, the data will pass through the flip-flop and toggle the state of the flip-flop.
            # and next loop current clock also 1, so Q hold
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and our dynamic Clear wire!
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break
            # else:
            #     print(list(reversed(old_qs)))
            #     print(list(reversed(new_qs)))
            # 5 -> 0
            # [1, 0, 1] 5
            # [1, 1, 0] 6
            # [1, 1, 0] 6
            # [0, 0, 0] 0

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class SecondTimer:
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        bits_of_low = self.decade_counter_10.getQs()
        return bits_of_low

    def getBitsOfHigh(self):
        bits_of_high = self.decade_counter_6.getQs()
        return bits_of_high
    
    def __call__(self, clk = 0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class MinuteTimer:
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        bits_of_low = self.decade_counter_10.getQs()
        return bits_of_low

    def getBitsOfHigh(self):
        bits_of_high = self.decade_counter_6.getQs()
        return bits_of_high
    
    def __call__(self, clk = 0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class HourTimer:
    def __init__(self):
        self.nbits = 5        
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
                
        self.nand_gate = NAND()
        self.and_gate_10 = AND(2) # Detects the 10
        self.and_gate_12 = AND(2) # Detects the 12
        
        self.or_gate = OR(2)

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def __call__(self, clk=0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]
  
            # 2. Wire up the Async Clear
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            q4 = self.flipflops[4].getQ()
            
            # Clear 1: When low digit hits 10 (q3=1, q1=1)
            clear_10 = self.and_gate_10([q3, q1])

            # Clear 2: When total time hits 12 (q4=1, q1=1). NO INVERTER NEEDED!
            clear_12 = self.and_gate_12([q4, q1])
            
            # The low digit must clear if it hits 10 OR if the whole clock hits 12
            clear_low_digit = self.or_gate([clear_12, clear_10])

            # The cascading clock for the High Digit (Triggers when low digit hits 10)
            q0 = self.flipflops[0].getQ()
            clk_of_hour_high_digit = self.nand_gate([q0, q3])
            
            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            
            # Tick the low digit (bits 0 to 3)
            for ff in self.flipflops[:-1]:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_low_digit])
                current_clk = q_bar

            # Tick the high digit (bit 4)
            data_high = self.flipflops[-1].getQ_bar()
            self.flipflops[-1]([data_high, clk_of_hour_high_digit, 0, clear_12])
            
            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break
                
        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class HourMinuteSecondTimer:
    # adding switches to set the time manually(hour and minute and second)
    def __init__(self):
        self.hour_timer = HourTimer()
        self.minute_timer = MinuteTimer()
        self.second_timer = SecondTimer()
        self.nand_gate_min_sec = NAND()
        
        self.nand_gate_hour_min = NAND()
        self.nand_gate_pm_am = NAND()
        # A toggle flip-flop to store AM (0) or PM (1)
        self.am_pm_memory = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()

        self.switch_sec = XOR()
        self.switch_min = XOR()
        self.switch_hour = XOR()

    def update_hour(self, hour_stride):
        for _ in range(hour_stride):
            bits_tens_min = self.minute_timer.getBitsOfHigh()
            clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
            for switch in [1, 1]:
                clk_of_hour = self.switch_hour([switch, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit        
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])

    def update_minute(self, minute_stride):
        for _ in range(minute_stride):
            bits_tens_sec = self.second_timer.getBitsOfHigh()
            clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
            for switch in [1, 1]:
                clk_of_min = self.switch_min([switch, clk_of_min])
                bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
                
                clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
                clk_of_hour = self.switch_hour([0, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])

    def update_second(self, second_stride, clk = 0):
        for _ in range(second_stride):
            for switch in [1, 1]:
                clk = self.switch_sec([switch, clk])
                # print(clk)
                bits_tens_sec, bits_ones_sec = self.second_timer(clk)
                clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
                clk_of_min = self.switch_min([0, clk_of_min])
                bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
                
                clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
                clk_of_hour = self.switch_hour([0, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])
            
    def __call__(self, clk = 0):
        # bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec = self.min_sec_timer(clk)
        clk = self.switch_sec([0, clk])
        bits_tens_sec, bits_ones_sec = self.second_timer(clk)
        clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
        clk_of_min = self.switch_min([0, clk_of_min])
        bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
        
        clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
        clk_of_hour = self.switch_hour([0, clk_of_hour])
        bits_hour = self.hour_timer(clk_of_hour)
        bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
        
        clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
        current_am_pm_state = self.am_pm_memory.getQ_bar()
        am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])
        
        return am_pm_q, bits_tens_hour, bits_ones_hour, bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec


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
    
class Decoder_3_8_bk:
    """
    3 to 8 decoder, takes 3 input bits and decodes them into 8 output lines.
    Only one output line will be high (1) at a time
    for example, if the input is 101, then the output will be 00100000
    """
    def __init__(self, nin = 3, nout = 8):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]

    def write(self, inputs, write):
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        # This function will take the write signal and the inputs, and return the output of the AND gate
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs
    
    def __call__(self, address, write=1):
        assert len(address) == self.nin, "Input must be 3 bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
        # TODO(PengChen:) this have potential bug, logcial error, address = [0,0,1] -> output[3] is 1
        # but should out[6] is 1.
        # output = [0] * self.nout
        # output[7] = self.and_gates[0]([write, self.inverters[2](address[2]), self.inverters[1](address[1]), self.inverters[0](address[0])]) # 1000
        # output[6] = self.and_gates[1]([write, self.inverters[2](address[2]), self.inverters[1](address[1]), address[0][0]]) # 1001
        # output[5] = self.and_gates[2]([write, self.inverters[2](address[2]), address[1][0], self.inverters[0](address[0])]) # 1010
        # output[4] = self.and_gates[3]([write, self.inverters[2](address[2]), address[1][0], address[0][0]]) # 1011
        # output[3] = self.and_gates[4]([write, address[2][0], self.inverters[1](address[1]), self.inverters[0](address[0])]) # 1100
        # output[2] = self.and_gates[5]([write, address[2][0], self.inverters[1](address[1]), address[0][0]]) # 1101
        # output[1] = self.and_gates[6]([write, address[2][0], address[1][0], self.inverters[0](address[0])]) # 1110
        # output[0] = self.and_gates[7]([write, address[2][0], address[1][0], address[0][0]]) # 1111
        # FIX above TODO bug
        output = [0] * self.nout
        output[7] = self.and_gates[0]([write, self.inverters[0](address[0]), self.inverters[1](address[1]), self.inverters[2](address[2])]) # 1000
        output[6] = self.and_gates[1]([write, self.inverters[0](address[0]), self.inverters[1](address[1]), address[2][0]]) # 1001
        output[5] = self.and_gates[2]([write, self.inverters[0](address[0]), address[1][0],                 self.inverters[2](address[2])]) # 1010
        output[4] = self.and_gates[3]([write, self.inverters[0](address[0]), address[1][0],                 address[2][0]]) # 1011
        output[3] = self.and_gates[4]([write, address[0][0],                 self.inverters[1](address[1]), self.inverters[2](address[2])]) # 1100
        output[2] = self.and_gates[5]([write, address[0][0],                 self.inverters[1](address[1]), address[2][0]]) # 1101
        output[1] = self.and_gates[6]([write, address[0][0],                 address[1][0],                 self.inverters[2](address[2])]) # 1110
        output[0] = self.and_gates[7]([write, address[0][0],                 address[1][0],                 address[2][0]]) # 1111
        # output[0] is MSB
        return output

class Selector_8_1_bk:
    """
    8 to 1 selector, takes 8 input lines and selects one of them based on a 3-bit address.
    for example, if the address is 101, then the output will be the value of the 00100000 -> output[2] out_from_memory line
    """
    def __init__(self, nin = 3, nout = 8):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)]
        self.or_gate = OR(self.nout)

    def __call__(self, address, out_from_memory):
        assert len(address) == self.nin, f"Input must be {self.nin} bits long"
        assert len(out_from_memory) == self.nout, f"Out_from_memory must be {self.out} bits long"
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input

        # output = [0] * self.nout
        # output[7] = self.and_gates[0]([out_from_memory[7], self.inverters[2](address[2]), self.inverters[1](address[1]), self.inverters[0](address[0])]) # 1000
        # output[6] = self.and_gates[1]([out_from_memory[6], self.inverters[2](address[2]), self.inverters[1](address[1]), address[0][0]]) # 1001
        # output[5] = self.and_gates[2]([out_from_memory[5], self.inverters[2](address[2]), address[1][0], self.inverters[0](address[0])]) # 1010
        # output[4] = self.and_gates[3]([out_from_memory[4], self.inverters[2](address[2]), address[1][0], address[0][0]]) # 1011
        # output[3] = self.and_gates[4]([out_from_memory[3], address[2][0], self.inverters[1](address[1]), self.inverters[0](address[0])]) # 1100
        # output[2] = self.and_gates[5]([out_from_memory[2], address[2][0], self.inverters[1](address[1]), address[0][0]]) # 1101
        # output[1] = self.and_gates[6]([out_from_memory[1], address[2][0], address[1][0], self.inverters[0](address[0])]) # 1110
        # output[0] = self.and_gates[7]([out_from_memory[0], address[2][0], address[1][0], address[0][0]]) # 1111
        # FIX above TODO bug
        output = [0] * self.nout
        output[7] = self.and_gates[0]([out_from_memory[7], self.inverters[0](address[0]), self.inverters[1](address[1]), self.inverters[2](address[2])]) # 1000
        output[6] = self.and_gates[1]([out_from_memory[6], self.inverters[0](address[0]), self.inverters[1](address[1]), address[2][0]]) # 1001
        output[5] = self.and_gates[2]([out_from_memory[5], self.inverters[0](address[0]), address[1][0],                 self.inverters[2](address[2])]) # 1010
        output[4] = self.and_gates[3]([out_from_memory[4], self.inverters[0](address[0]), address[1][0],                 address[2][0]]) # 1011
        output[3] = self.and_gates[4]([out_from_memory[3], address[0][0],                 self.inverters[1](address[1]), self.inverters[2](address[2])]) # 1100
        output[2] = self.and_gates[5]([out_from_memory[2], address[0][0],                 self.inverters[1](address[1]), address[2][0]]) # 1101
        output[1] = self.and_gates[6]([out_from_memory[1], address[0][0],                 address[1][0],                 self.inverters[2](address[2])]) # 1110
        output[0] = self.and_gates[7]([out_from_memory[0], address[0][0],                 address[1][0],                 address[2][0]]) # 1111

        out = self.or_gate(output)
        return [out]
    
class Decoder_3_8:
    """
    3 to 8 decoder with an Enable pin.
    Input 000 -> output[0] is 1 (if enable=1)
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
    8 to 1 selector.
    Input 000 -> output[0] is 1
    Input 111 -> output[7] is 1
    """
    def __init__(self, nin=3, nout=8):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)] # 3 inputs for Address
        self.or_gate = OR(self.nout)
    
    def __call__(self, address, out_from_memory):
        assert len(address) == self.nin, "Input must be 3 bits long"

        # Dynamically generate all 8 possible binary states: 000 to 111
        idxs = [[(i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(self.nout)]
        
        address = [[address[i]] for i in range(len(address))] 
        output = [0] * self.nout
        
        for i, idx in enumerate(idxs):
            input_and = [out_from_memory[i]]
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            
            # Straight 1-to-1 mapping! index 0 = output[0]
            output[i] = self.and_gates[i](input_and)
        # output[0] is LSB
        out = self.or_gate(output)
        return [out]

class RAM_8_1:
    """
    A simple memory module that combines the decoder, memory cells, and selector to create a functional memory unit.
    For simplicity, we will implement a 8-word memory with 3-bit addresses and 1-bit data.
    """
    def __init__(self):
        self.capacity = 8  # 8 words
        self.word_size = 1  # 1 bit per word

        self.decoder = Decoder_3_8()
        self.memory_cells = [NBitsMemory(self.word_size) for _ in range(self.capacity)]  # 8 words of 1 bit each
        self.selector = Selector_8_1()

    def __call__(self, address, data_in, write):
        assert len(address) == 3, "Address must be 3 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        
        # Use the decoder to determine which memory cell to write to
        write_lines = self.decoder(address, write)
        for i in range(self.capacity):
            self.memory_cells[i](data_in, write_lines[i])  # Write data to the selected memory cell
        # return self.read(address)

    def read(self, address):
        # Read from all memory cells and use the selector to get the output from the selected cell
        out_from_memory = [cell.read()[0] for cell in self.memory_cells]  # Get the output from all memory cells
        return self.selector(address, out_from_memory)  # Select the output from the addressed cell

class RAM_8_8:
    """
    A simple memory module that combines the decoder, memory cells, and selector to create a functional memory unit.
    For simplicity, we will implement a 8-word memory with 3-bit addresses and 8-bit data.
    """
    def __init__(self, word_size=8):
        self.capacity = 8  # 8 words
        self.word_size = word_size
        self.ram_8_1_cells = [RAM_8_1() for _ in range(self.word_size)]  # 8 words of 8 bits each
        
    def __call__(self, address, data_in, write):
        assert len(address) == 3, "Address must be 3 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        for bit in range(self.word_size):
            self.ram_8_1_cells[bit](address, [data_in[bit]], write)  # Write each bit to the selected memory cell

    def read(self, address):
        bits = []
        for bit in range(self.word_size):
            bits = bits + self.ram_8_1_cells[bit].read(address)
        return bits

class Decoder_4_16:
    """
    4 to 16 decoder, takes 4 input bits and decodes them into 16 output lines.
    Only one output line will be high (1) at a time
    for example, if the input is 1010, then the output will be output[10] = 1
    """
    def __init__(self, nin = 4, nout = 16):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(4) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        # This function will take the write signal and the inputs, and return the output of the AND gate
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs

    def __call__(self, address):
        assert len(address) == self.nin, "Input must be 4 bits long"
        idxs = [
            [0, 0, 0, 0], 
            [0, 0, 0, 1], 
            [0, 0, 1, 0], 
            [0, 0, 1, 1], 
            [0, 1, 0, 0], 
            [0, 1, 0, 1], 
            [0, 1, 1, 0], 
            [0, 1, 1, 1], 
            [1, 0, 0, 0], 
            [1, 0, 0, 1], 
            [1, 0, 1, 0], 
            [1, 0, 1, 1], 
            [1, 1, 0, 0], 
            [1, 1, 0, 1], 
            [1, 1, 1, 0], 
            [1, 1, 1, 1]
        ]
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
        output = [0] * self.nout
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            # output[self.nout - 1 - i] = self.and_gates[i]([write] + input_and)  # write is the first input to the AND gate
            # output[self.nout - 1 - i] = self.and_gates[i](input_and)
            output[i] = self.and_gates[i](input_and)
        return output

class Selector_16_1:
    """
    16 to 1 selector, takes 16 input lines and selects one of them based on a 16-bit address.
    for example, if the address is 1010, then the output will be the value of the -> output[10] out_from_memory line
    """
    def __init__(self, nin = 4, nout = 16):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(5) for _ in range(self.nout)]
        self.or_gate = OR(self.nout)

    def __call__(self, address, out_from_memory):
        assert len(address) == self.nin, f"Input must be {self.nin} bits long"
        assert len(out_from_memory) == self.nout, f"Out_from_memory must be {self.nout} bits long"
        idxs = [
            [0, 0, 0, 0], 
            [0, 0, 0, 1], 
            [0, 0, 1, 0], 
            [0, 0, 1, 1], 
            [0, 1, 0, 0], 
            [0, 1, 0, 1], 
            [0, 1, 1, 0], 
            [0, 1, 1, 1], 
            [1, 0, 0, 0], 
            [1, 0, 0, 1], 
            [1, 0, 1, 0], 
            [1, 0, 1, 1], 
            [1, 1, 0, 0], 
            [1, 1, 0, 1], 
            [1, 1, 1, 0], 
            [1, 1, 1, 1]
        ]
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
        output = [0] * self.nout
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            # output[self.nout - 1 - i] = self.and_gates[i]([out_from_memory[self.nout - 1 - i]] + input_and)  # write is the first input to the AND gate
            output[i] = self.and_gates[i]([out_from_memory[i]] + input_and)  # outdata is the first input to the AND gate
        out = self.or_gate(output)
        return [out]
    

class RAM_16_1:
    """
    A simple memory module that combines the decoder, memory cells, and selector to create a functional memory unit.
    For simplicity, we will implement a 16-word memory with 4-bit addresses and 1-bit data.
    """
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
        # return self.read(address)

    def read(self, address):
        # Read from all memory cells and use the selector to get the output from the selected cell
        out_from_memory = [cell.read()[0] for cell in self.memory_cells]  # Get the output from all memory cells
        return self.selector(address, out_from_memory)  # Select the output from the addressed cell

class RAM_16_8:
    """
    A simple memory module that combines the decoder, memory cells, and selector to create a functional memory unit.
    For simplicity, we will implement a 16-word memory with 4-bit addresses and 8-bit data.
    """
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
        # return self.read(address)

    def read(self, address):
        bits = []
        for bit in range(self.word_size):
            bits = bits + self.ram_16_1_cells[bit].read(address)
        return bits


class RAM_64KB_bk:
    """
    64KB Memory using 16-bit address bus.
    Address are split:
        - Top 12 bits route to one of 4,096 RAM_16_8 chips.
        - Bottom 4 bits select the exact byte within that chip.
    """
    def __init__(self, word_size=8):
        self.capacity = 65536  # 64KB = 65536 bytes
        self.word_size = word_size
        self.ram_16_8_cells = [RAM_16_8() for _ in range(self.capacity // 16)]  # Each RAM_16_8 can handle 16 addresses
        self.decoder0 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[0:4]
        self.decoder1 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[4:8]
        self.decoder2 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[8:12]
        self.tri = TriStateBuffer(self.word_size)

    def __call__(self, address, data_in, write):
        assert len(address) == 16, "Address must be 16 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        # 1. Decode the top 12 bits to find the active RAM_16_8 chip
        out0 = self.decoder0(address[:4])
        out1 = self.decoder1(address[4:8])
        out2 = self.decoder2(address[8:12])
        idx0 = [i for i, val in enumerate(reversed(out0)) if val == 1]
        idx1 = [i for i, val in enumerate(reversed(out1)) if val == 1]
        idx2 = [i for i, val in enumerate(reversed(out2)) if val == 1]
        assert len(idx0) == 1 and len(idx1) == 1 and len(idx2) == 1, "Decoder error: Multiple lines active!"
        idx = (idx0[0] << 8) | (idx1[0] << 4) | idx2[0]
        self.ram_16_8_cells[idx](address[12:], data_in, write)

        # below in loop, very slow
        # for i, val0 in enumerate(reversed(out0)):
        #     if val0 == 0: continue # software magic: skip dead wires to save time.
        #     for j, val1 in enumerate(reversed(out1)):
        #         if val1 == 0: continue
        #         for k, val2 in enumerate(reversed(out2)):
        #             if val2 == 0: continue
        #             # if val0, val1, and val2 are all 1, we found the active chip
        #             idx = (i << 8) | (j << 4) | k
        #             # the write signal is passed directly into the smaller chip1
        #             self.ram_16_8_cells[idx](address[12:], data_in, write)
        
        # return self.read(address)

    def read(self, address, enable=1):
        out0 = self.decoder0(address[:4])
        out1 = self.decoder1(address[4:8])
        out2 = self.decoder2(address[8:12])
        idx0 = [i for i, val in enumerate(reversed(out0)) if val == 1]
        idx1 = [i for i, val in enumerate(reversed(out1)) if val == 1]
        idx2 = [i for i, val in enumerate(reversed(out2)) if val == 1]
        assert len(idx0) == 1 and len(idx1) == 1 and len(idx2) == 1, "Decoder error: Multiple lines active!"
        idx = (idx0[0] << 8) | (idx1[0] << 4) | idx2[0]
        outputs = self.ram_16_8_cells[idx].read(address[12:])

        # for i, val0 in enumerate(reversed(out0)):
        #     if val0 == 0: continue # software magic: skip dead wires to save time.
        #     for j, val1 in enumerate(reversed(out1)):
        #         if val1 == 0: continue
        #         for k, val2 in enumerate(reversed(out2)):
        #             if val2 == 0: continue
        #             """
        #             page 281 of the book, read need [enable] pin, but 
        #             here we needn't, because we use if condition to check
        #             idx is our active chip.
        #             """
        #             # if val0, val1, and val2 are all 1, we found the active chip
        #             idx = (i << 8) | (j << 4) | k
        #             # the write signal is passed directly into the smaller chip1
        #             outputs = self.ram_16_8_cells[idx].read(address[12:])
        outputs = self.tri(outputs, enable)
        return outputs

class RAM_64KB:
    """
    64KB Memory using 16-bit address bus.
    Address are split:
        - Top 12 bits route to one of 4,096 RAM_16_8 chips.
        - Bottom 4 bits select the exact byte within that chip.
    """
    def __init__(self, word_size=8):
        self.capacity = 65536  # 64KB = 65536 bytes
        self.word_size = word_size
        self.ram_16_8_cells = [RAM_16_8() for _ in range(self.capacity // 16)]  # Each RAM_16_8 can handle 16 addresses
        self.decoder0 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[0:4]
        self.decoder1 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[4:8]
        self.decoder2 = Decoder_4_16()  # To select which RAM_16_8 to use based on the address[8:12]
        self.tri = TriStateBuffer(self.word_size)

    def __call__(self, address, data_in, write):
        assert len(address) == 16, "Address must be 16 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"

        # 1. Decode the top 12 bits to find the active RAM_16_8 chip
        out0 = self.decoder0(address[:4])
        out1 = self.decoder1(address[4:8])
        out2 = self.decoder2(address[8:12])
        idx0 = [i for i, val in enumerate(out0) if val == 1]
        idx1 = [i for i, val in enumerate(out1) if val == 1]
        idx2 = [i for i, val in enumerate(out2) if val == 1]
        assert len(idx0) == 1 and len(idx1) == 1 and len(idx2) == 1, "Decoder error: Multiple lines active!"
        # print(f'idx0: {idx0}, idx1: {idx1}, idx2: {idx2}')
        idx = (idx0[0] << 8) | (idx1[0] << 4) | idx2[0]
        self.ram_16_8_cells[idx](address[12:], data_in, write)

    def read(self, address, enable=1):
        out0 = self.decoder0(address[:4])
        out1 = self.decoder1(address[4:8])
        out2 = self.decoder2(address[8:12])
        idx0 = [i for i, val in enumerate(out0) if val == 1]
        idx1 = [i for i, val in enumerate(out1) if val == 1]
        idx2 = [i for i, val in enumerate(out2) if val == 1]
        assert len(idx0) == 1 and len(idx1) == 1 and len(idx2) == 1, "Decoder error: Multiple lines active!"
        idx = (idx0[0] << 8) | (idx1[0] << 4) | idx2[0]
        outputs = self.ram_16_8_cells[idx].read(address[12:])

        outputs = self.tri(outputs, enable)
        return outputs

    
class ControlSignals:
    def __init__(self):
        self.edge_flipflop1 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.edge_flipflop2 = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
        self.invert1 = Inverter()
        self.and_gate = AND()
    def __call__(self, clock):
        not_clk = self.invert1([clock])

        # while True:
        #     old_q1, old_q_bar1 = self.edge_flipflop1.getQ(), self.edge_flipflop1.getQ_bar()
        #     old_q2, old_q_bar2 = self.edge_flipflop2.getQ(), self.edge_flipflop2.getQ_bar()

        self.edge_flipflop1([self.edge_flipflop1.getQ_bar(), clock])
        self.edge_flipflop2([self.edge_flipflop1.getQ(), not_clk])
        clk_input_to_counter = self.edge_flipflop1.getQ()
        pulse = self.and_gate([self.edge_flipflop1.getQ_bar(), self.edge_flipflop2.getQ()])
        return [clk_input_to_counter, pulse]
    


class Counter16Bit:
    """A Ripple Counter that counts"""
    def __init__(self,):
        self.nbits = 16
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def SetMaxAddr(self):
        for ff in self.flipflops:
            ff([0, 0, 1, 0]) # D = 0, CLK = 0, PRE = 1, CLR = 0

    def __call__(self, clk = 0, clear_wire = 0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 2. Wire up the Async Clear
            # ff[0] is Q0 (LSB), ff[1] is Q1, ff[2] is Q2, ff[3] is Q3 (MSB)
            # We want to clear when we hit 10 (Binary: 1010). 
            # This happens when Q3 == 1 and Q1 == 1.
            # q1 = self.flipflops[1].getQ()
            # q3 = self.flipflops[3].getQ()
            # clear_wire = self.and_gate([q3, q1])

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and clear wire (0)
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))
    
class AutomatedAccumulatingAdder:
    """
    A class representing an automated accumulating adder.
    """
    def __init__(self, nbits = 8):
        self.nbits = nbits
        self.counter = Counter16Bit()  # Using the 16-bit counter as an accumulator
        # self.control_signals = ControlSignals()
        self.ram64KB = RAM_64KB()

        # NBitsAccumulator
        self.adder = NBitAdderWithOverflow(self.nbits)
        self.register = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        self.nor_gate = NOR(self.nbits) # for RAM Write signal
        self.and_gate = AND(2)

    def SetMaxAddr(self):
        self.counter.SetMaxAddr()

    def __call__(self, clk_input_to_counter, pulse):
        # clk_input_to_counter, pulse = self.control_signals(clock)
        self.counter(clk_input_to_counter)
        addr = self.counter.getQs()
        data_out_from_memory = self.ram64KB.read(addr)
        overflow, sum_bits = self.adder(data_out_from_memory, self.register.getQ())
        self.register(sum_bits, pulse)  # Data, Clock, Preset(0), Clear(0)

        # from page 297 in book, author
        # wants to write the accumulated sum to the first memory
        # location that has a value of 00h.
        ram_write = self.and_gate([self.nor_gate(data_out_from_memory), pulse])
        if ram_write:
            self.write_to_memory(addr, self.register.getQ())

    def write_to_memory(self, address, data):
        self.ram64KB(address, data, write=1)

    def read_register(self):
        return self.register.getQ()        
    


class Decoder_2_4:
    """
    2 to 4 decoder, takes 2 input bits and decodes them into 4 output lines.
    Only one output line will be high (1) at a time
    for example, if the input is 01, then the output will be 0010
    """
    def __init__(self, nin = 2, nout = 4):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(2) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        # This function will take the write signal and the inputs, and return the output of the AND gate
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs

    def __call__(self, address):
        assert len(address) == self.nin, "Input must be 2 bits long"
        idxs = [
            [0, 0], 
            [0, 1], 
            [1, 0], 
            [1, 1], 
        ]
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
        output = [0] * self.nout
        for i, idx in enumerate(idxs):
            input_and = []
            for j, val in enumerate(idx):
                if val == 0:
                    input_and.append(self.inverters[j](address[j]))
                else:
                    input_and.append(address[j][0])
            output[self.nout - 1 - i] = self.and_gates[i](input_and)
        # output[0] is MSB
        return output
    
class Decoder_2_4_V2:
    """
    2 to 4 decoder, takes 2 input bits and decodes them into 4 output lines.
    Only one output line will be high (1) at a time
    for example, if the input is 01, then the output[1] = 1
    """
    def __init__(self, nin = 2, nout = 4):
        self.nin = nin
        self.nout = nout
        self.inverters = [Inverter() for _ in range(self.nin)]
        self.and_gates = [AND(2) for _ in range(self.nout)]
        self.and_gates_with_write = [AND(2) for _ in range(self.nout)]
    
    def write(self, inputs, write):
        assert len(inputs) == self.nout, f"Inputs must be {self.nout} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        # This function will take the write signal and the inputs, and return the output of the AND gate
        outputs = []
        for i in range(self.nout):
            outputs.append(self.and_gates_with_write[i]([write, inputs[i]]))
        return outputs

    def __call__(self, address):
        assert len(address) == self.nin, "Input must be 2 bits long"
        idxs = [
            [0, 0], 
            [0, 1], 
            [1, 0], 
            [1, 1], 
        ]
        address = [[address[i]] for i in range(len(address))] # convert to list of lists for inverters gate input
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
    
class AutomatedAccumulatingAdderV2:
    """
    A class representing an automated accumulating adder.
    """
    def __init__(self, nbits = 8):
        self.nbits = nbits
        self.counter = Counter16Bit()  # Using the 16-bit counter as an accumulator
        # self.control_signals = ControlSignals()
        self.ram64KB = RAM_64KB()

        # NBitsAccumulator
        self.adder = NBitAdderWithOverflow(self.nbits)

        self.inst_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        self.low_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits+1)    # overflow of low
        self.middle_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits+1) # overflow of middle
        self.high_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)   

        self.decoder_2_4_for_clock = Decoder_2_4()
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
        # self.invert_gate_for_halt = Inverter()


    def SetMaxAddr(self):
        self.counter.SetMaxAddr()

    def getEnableLow(self):
        return self.enable_low_byte
    
    def getEnableMiddle(self):
        return self.enable_mid_byte
    
    def getEnableHigh(self):
        return self.enable_hig_byte
    
    def getHaltInst(self):
        return self.halt_instruct
    
    def getCarryInAdder(self):
        return self.carry_in_adder

    def getInputA(self):
        return self.input_a
    
    def getInputA(self):
        return self.input_a

    def getEnableInstruc(self):
        return self.enable_instruct

    def __call__(self, clk_input_to_counter, pulse):
        # clk_input_to_counter, pulse = self.control_signals(clock)
        self.counter(clk_input_to_counter)
        addr = self.counter.getQs()
        # instruct code or data
        data_out_from_memory = self.ram64KB.read(addr)

        # page 305: The three enable signals for the tri-state buffers can be 
        # generated by a 2-to-4 decoder using least significant bits of the memory address.
        enable_high_byte, enable_middle_byte, enable_low_byte, enable_insruct = self.decoder_2_4_for_clock([addr[-2], addr[-1]])

        self.enable_instruct = enable_insruct
        self.enable_low_byte = enable_low_byte
        self.enable_mid_byte = enable_middle_byte
        self.enable_hig_byte = enable_high_byte

        instruction_latch_clk = self.and_gate_use_for_instruct_clk([enable_insruct, pulse])
        self.inst_latch(data_out_from_memory, instruction_latch_clk)  # Code, Clock, Preset(0), Clear(0)
        Q_from_inst_latch = self.inst_latch.getQ()

        if pulse:
            print(f"Q_from_inst_latch: {Q_from_inst_latch}")

        # to halt
        Q3_from_inst_latch = Q_from_inst_latch[-4]
        self.halt_instruct = Q3_from_inst_latch
        # page 311 use invert Q3 to config flip-flip, we not use here for simple.
        # self.halt_instruct = self.invert_gate_for_halt([Q3_from_inst_latch])

        Q1_from_inst_latch = Q_from_inst_latch[-2]

        low_byte_latch_clk = self.and_gate_use_for_low_byte_clk([Q1_from_inst_latch, pulse, enable_low_byte])
        mid_byte_latch_clk = self.and_gate_use_for_middle_byte_clk([Q1_from_inst_latch, pulse, enable_middle_byte])
        high_byte_latch_clk = self.and_gate_use_for_high_byte_clk([Q1_from_inst_latch, pulse, enable_high_byte])

        Q0_from_inst_latch = Q_from_inst_latch[-1]
        outputs_from_complements_of_one = []
        for idx, xor_gate in enumerate(self.xor_gates_for_complements):
            outputs_from_complements_of_one.append(xor_gate([Q0_from_inst_latch, data_out_from_memory[idx]]))
        input_a = outputs_from_complements_of_one
        self.input_a = input_a

        if enable_low_byte:
            carry_signal_from_tri_state_buffers = 0 # low byte, no carry in    
            input_b = self.low_latch.getQ()[1:]
        elif enable_middle_byte:
            carry_signal_from_tri_state_buffers = self.low_latch.getQ()[0]  # carry out from low byte
            input_b = self.middle_latch.getQ()[1:]
        elif enable_high_byte:
            carry_signal_from_tri_state_buffers = self.middle_latch.getQ()[0]  # carry out from middle byte
            input_b = self.high_latch.getQ()
        else:
            # Default states to prevent floating wires during Instruction Fetch
            input_b = [0] * self.nbits
            carry_signal_from_tri_state_buffers = 0


        carry_in_adder = self.or_gate_for_carry_in_adder([self.and_gate_for_carry_in_adder([enable_low_byte, Q0_from_inst_latch]), carry_signal_from_tri_state_buffers])
        self.carry_in_adder = carry_in_adder
        overflow, sum_bits = self.adder(input_a, input_b, carry_in_adder)
        carry_out = self.adder.get_carry_out()

        if enable_low_byte:
            self.low_latch([carry_out]+sum_bits, low_byte_latch_clk)  # Data, Clock, Preset(0), Clear(0)
        elif enable_middle_byte:
            self.middle_latch([carry_out]+sum_bits, mid_byte_latch_clk)  # Data, Clock, Preset(0), Clear(0)
        elif enable_high_byte:
            self.high_latch(sum_bits, high_byte_latch_clk)  # Data, Clock, Preset(0), Clear(0)

        # RAM write
        Q2_from_inst_latch = Q_from_inst_latch[-3]
        ram_write = self.and_gate_for_write_ram([Q2_from_inst_latch, pulse, self.invert_for_write_ram([enable_insruct])])

        if ram_write:
            if enable_low_byte:
                self.write_to_memory(addr, self.low_latch.getQ()[1:]) # [0] is carry_out
            elif enable_middle_byte:
                self.write_to_memory(addr, self.middle_latch.getQ()[1:]) # [0] is carry_out
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

# ------------------------- start ch22 ----------------------------------
class Logic:
    def __init__(self, nin_data = 8, nin_control = 3):
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
        assert len(input_A) == self.nin_data, "Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, "Input must be {self.nin_data} bits long"
        assert len(F2_0) == self.nin_control, "Input must be {self.nin_control} bits long"

        invert_of_f0 = self.invert_gate_of_f0([F2_0[-1]])
        invert_of_f1 = self.invert_gate_of_f1([F2_0[-2]])

        self.enable_and_output = self.and_gate_of_enable_and([invert_of_f0, invert_of_f1, F2_0[0]])
        self.enable_xor_output = self.and_gate_of_enable_xor([F2_0[-1], invert_of_f1, F2_0[0]])
        self.enable_or_output = self.and_gate_of_enable_or([invert_of_f0, F2_0[1], F2_0[0]])

        output = []
        # should use tri-buffer to replace if condition
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
    def __init__(self, nin_data = 8, nin_control = 2):
        self.nin_data = nin_data
        self.nin_control = nin_control

        # ones' complement
        self.xor_gates_for_complements = [XOR() for _ in range(self.nin_data)]

        # NBitsAccumulator
        self.adder = NBitAdderWithOverflow(self.nin_data)

        self.invert_gate_of_f0 = Inverter()
        self.and_gate_of_f0_CY_in = AND(2)
        self.and_gate_of_f0_f1 = AND(2)

        self.or_gate_of_CI = OR(2)

        # This is a little different from the circuits shown in the book 
        # in that the values of both CY In and CY Out are inverted for subtraction. (The entry in the lower-right corner of the table on page 322 should be CY_bar)
        self.xor_for_cy = XOR()

    def __call__(self, input_A, input_B, F1_0, CY_In = 0):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F1_0) == self.nin_control, f"Input must be {self.nin_control} bits long"

        invert_of_f0 = self.invert_gate_of_f0([F1_0[1]])
        invert_flag = F1_0[0]
        CI_flag = self.or_gate_of_CI([self.and_gate_of_f0_CY_in([F1_0[1], self.xor_for_cy([CY_In, F1_0[0]])]), self.and_gate_of_f0_f1([invert_of_f0, F1_0[0]])])
        
        outputs_from_complements_of_one = []
        for idx, xor_gate in enumerate(self.xor_gates_for_complements):
            outputs_from_complements_of_one.append(xor_gate([invert_flag, input_B[idx]]))
        operand_B = outputs_from_complements_of_one

        overflow, sum_bits = self.adder(input_A, operand_B, CI_flag)
        # print(f"CI: {CI_flag}, CO: {self.adder.get_carry_out()}")
        carry_out = self.xor_for_cy([self.adder.get_carry_out(), F1_0[0]])

        return carry_out, sum_bits
        
            
    
class ALU:
    def __init__(self, nin_data = 8, nin_control_signal = 3):
        self.nin_data = nin_data
        self.nin_control = nin_control_signal

        self.add_and_subtract = Add_Subtract(self.nin_data, self.nin_control-1)
        self.logic = Logic(self.nin_data, self.nin_control)

        self.enable_add_or_sub = 0

        # just use 3 bits although use nin_data bits here
        # flag[0]: Sign flag(S), flag[1]: Zero flag(Z), flag[2]: Carry flag(CY)
        self.flags_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)
        self.result_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)

        self.invert_of_f2 = Inverter()
        self.and_gate_of_f0_f1 = AND()
        self.or_gate_of_invert_of_f2_other = OR()
        self.and_gate_of_cy_out_other = AND()

        self.nor_gates_of_flags =  NOR(self.nin_data)

        self.tri_add_sub = TriStateBuffer(self.nin_data)
        self.data_bus = DataBus(num_buffers=3, nbits=self.nin_data) # input_A, add/sub output and logic output
        self.tri_result = TriStateBuffer(self.nin_data)

        self.and_gate_of_f0_f1_f2 = AND()
        self.and_gate_cy_in = AND()
        self.tri_acc = TriStateBuffer(self.nin_data)

        self.and_used_in_zero_flag_0 = AND()
        self.and_used_in_zero_flag_1 = AND()
        self.invert_used_in_zero_flag_0 = Inverter()
        self.or_used_in_zero_flag_0 = OR()

    def read_flags(self,):
        return self.flags_latch.getQ()[:3]
    
    def read_out(self, enable):
        assert enable in [0, 1], f"enable signal must be 0 or 1"
        return self.tri_result(self.result_latch.getQ(), enable)

    # A comes from Acc of RA, B comes from out of data bus, output is send to data bus and acc (acc?) too. (page 345)
    # below function according page 332
    def __call__(self, input_A, input_B, F2_0, clock):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F2_0) == self.nin_control, f"Input must be {self.nin_control} bits long"
        assert clock in [0, 1], f"clock signal must be 0 or 1"

        # finish enable of add/sub
        invert_of_f2 = self.invert_of_f2([F2_0[0]])
        self.enable_add_or_sub = invert_of_f2

        and_of_f1_f0 = self.and_gate_of_f0_f1([F2_0[1], F2_0[2]])

        # finish enable acc
        self.enable_acc = self.and_gate_of_f0_f1_f2([and_of_f1_f0, F2_0[0]])

        # finish add/sub and CY OUT flag
        or_of_and_invert_f2 = self.or_gate_of_invert_of_f2_other([invert_of_f2, and_of_f1_f0])
        # flags current have 3 bits is meaningful: 
        # flags[0]: sign flag, flags[1]: zero flag, flags[2]: carry flag
        """
        The Carry flag should be set if the F2 signal is 0
        (indicating an addition or subtraction operation) or F1 and F0 are 1, which
        indicates a Compare operation. (How do you do this? Basically, it’s a subtraction.)

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
        flags = self.flags_latch.getQ()
        # CY in <- CY out and consider invert of F2(For the Compare operation, 
        # Add/Sub module is performing a Subtract with Borrow because F1 and F0 are both 1. 
        # For this reason, the CY In is set to 0 when a Compare operation is performed.)
        CY_IN = self.and_gate_cy_in([flags[2], invert_of_f2]) 
        # Carry flag then circles back up to provide the CY In input of the Add/Sub module
        carry_out, sum_bits = self.add_and_subtract(input_A, input_B, F2_0[1:], CY_IN) 
        and_of_cy_out_or = self.and_gate_of_cy_out_other([carry_out, or_of_and_invert_f2])
        # new flags, if this clock operation on logic, flags should keep same instead of update.
        # update: zero bit and sign flag both influenced by add/sub, compare/acc and logic
        # carry flag only influenced add/sub and compare
        new_flags = [0] * len(flags)
        new_flags[2] = and_of_cy_out_or

        # finish output from all component
        output_of_logic = self.logic(input_A, input_B, F2_0)
        output_from_add_sub = self.tri_add_sub(sum_bits, self.enable_add_or_sub)
        output_from_acc = self.tri_acc(input_A, self.enable_acc)
        
        # 1. Combine them on the bus. The Tri-State buffers ensure only the correct one has data!
        final_alu_result = self.data_bus([output_from_acc, output_from_add_sub, output_of_logic])
        self.result_latch(final_alu_result, clock)

        # 2. Calculate flags based on the FINAL combined bus data
        # for compare op: 
        #   1. if equal: zero flag is 1 and carry out flag is 0
        #   2. if A < B: carry out is 1
        #   3. if A > B: carry out is 0
        #   for sign bit, now influenced by acc, i.e., input_A
        # finish zero flag
        nor_from_add_sub = self.nor_gates_of_flags(sum_bits)
        and_used_in_zero_flag_0_ = self.and_used_in_zero_flag_0([nor_from_add_sub, or_of_and_invert_f2])
        nor_from_logic = self.nor_gates_of_flags(output_of_logic)
        and_used_in_zero_flag_1_ = self.and_used_in_zero_flag_1([nor_from_logic, self.invert_used_in_zero_flag_0([or_of_and_invert_f2])])
        new_flags[1] = self.or_used_in_zero_flag_0([and_used_in_zero_flag_0_, and_used_in_zero_flag_1_])
        # finish sign flag
        # sign bit influenced by input_A and add/sub
        """
        from gemini
        Why this fails: In the Intel 8080, a Compare instruction performs a hidden subtraction ($A - B$) 
        to calculate the flags. All flags (Zero, Carry, AND Sign) must reflect the result of that hidden subtraction.

        but author say However, the Compare operation doesn't result in a new value saved in the Accumulator. 
        For this reason, if a Compare operation is occurring, the A input is enabled with the tri-state 
        buffer at the far left to be saved in the Latch at the bottom right.
        and say:

        The Compare operation is the same as the Subtract operation with the
        important distinction that the result isn’t saved anywhere. Instead, the
        Carry flag is saved.
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
        new_flags[0] = final_alu_result[0]
        # 3. Latch the results
        self.flags_latch(new_flags, clock)

# ------------------------- end ch21 ----------------------------------
# ------------------------- start ch22 ----------------------------------
class TriStateBuffer:
    """
    Simulates a Tri-State Buffer for an 8-bit bus using pure logic gates.
    Instead of outputting 'None' when disabled, it forces the output to all 0s.
    (PengChen:) use if condition and bool variable to simulate this buffer
    so ugly, so gemini give me this implement.
    """
    def __init__(self, nbits=8):
        self.nbits = nbits
        self.and_gates = [AND(2) for _ in range(self.nbits)]

    def __call__(self, data_in, enable):
        # If enable=1, 1 AND Data = Data. (Passes through)
        # If enable=0, 0 AND Data = 0. (Blocks data, masking it to 0s)
        
        output = []
        for i in range(self.nbits):
            output.append(self.and_gates[i]([data_in[i], enable]))
            
        return output
    
class DataBus:
    """ 
    (PengChen:) be compatible class TriStateBuffer
    written by gemini
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
            # If it is a list, slice it with [i]. If it is an int, just use the int directly!
            bits_for_this_wire = [
                buf_out[i] if isinstance(buf_out, list) else buf_out 
                for buf_out in list_of_buffer_outputs
            ]
            # Shove all those bits into the giant OR gate
            bus_result.append(self.or_gates[i](bits_for_this_wire))
            
        return bus_result
    
class RegisterArray:
    """
    implement like: https://codehiddenlanguage.com/Chapter22/
    and page on book: 344
    """
    def __init__(self, nbits = 8):
        self.nbits = nbits # bits of latch
        self.decoder_clock = Decoder_3_8()
        self.decoder_enable = Decoder_3_8()

        self.latch_A = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_B = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_C = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_D = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_E = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_H = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.latch_L = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        
        self.latchs = { 0: self.latch_B, 
                        1: self.latch_C,
                        2: self.latch_D,
                        3: self.latch_E,
                        4: self.latch_H,
                        5: self.latch_L,
                        # watch out, 6: Memory
                        7: self.latch_A,}
        
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
                        # watch out, 6: Memory
                        7: self.tri_A,}

        self.data_bus = DataBus(num_buffers=len(self.latchs), nbits=self.nbits)
        self.addr_nbits = 16
        # num_buffers need change after
        self.addr_bus = DataBus(num_buffers=7, nbits=self.addr_nbits)
        self.tri_hl = TriStateBuffer(self.addr_nbits)

        self.clock_idx = [0] * (len(self.latchs) + 1) 
        self.enable_idx = [0] * (len(self.latchs) + 1) 
        self.or_gate_for_acc_clk = OR()
        self.or_gate_for_acc_read = OR()

        # self.inst_latch1 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        # self.inst_latch2 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        # self.enable_inst_latch2 = 0
        # self.inst_latch3 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        # page 352: 
        self.invert_gate_hl_select = Inverter()
        self.or_gate_h_clk = OR()
        self.or_gate_l_clk = OR()
    
    def __call__(self, data, select, clock, addr, hl_select, hl_clock):
        # select is SI2, SI1, SI0 in page 357
        assert len(data) == self.nbits, f"Inputs must be {self.nbits} bits long"
        assert len(select) == 3, f"selects must be 3 bits long"
        assert clock in [0, 1], "clock signal must be 0 or 1"

        # select is [i0, i1, i2]
        # latch_idx will let latch_idx[i0*4+i1*2+i2] = 1, other is 0
        # example [1, 1, 1]
        # latch_idx is [0, 0, 0, 0, 0, 0, 0, 1]
        # that suppose clock/enable is 1, otherwise latch_idx is all zeros
        
        clock_idx = self.decoder_clock(select, enable=clock)
        assert (sum(clock_idx) == 1 and clock == 1) or ((sum(clock_idx) == 0 and clock == 0)), "FATAL: Check Decoder_3_8 input/output"
        print(f"clock_idx: {clock_idx}, select: {select}, data: {data}")

        duplicate_datas = self.duplicate_data_to_each_latch(data)
        # clock_idx[3] = self.or_gate_h_clk([clock_idx[3], HL_clock])
        # clock_idx[2] = self.or_gate_l_clk([clock_idx[2], HL_clock])
        
        # TODO(PengChen:) we need add tri-buff before latch instead of use if condition
        if hl_select:
            duplicate_datas[4] = addr[:8] # to H latch
            duplicate_datas[5] = addr[8:] # to L latch
            # need this clear 0? we want hl_clock control instead of clock, they are independent.
            clock_idx = len(self.clock_idx) * [0]
            clock_idx[4] = self.or_gate_h_clk([clock_idx[4], hl_clock])
            clock_idx[5] = self.or_gate_l_clk([clock_idx[5], hl_clock])
            assert (sum(clock_idx) == 2 and hl_clock == 1) or ((sum(clock_idx) == 0 and hl_clock == 0)), "FATAL: Check hl_select and hl_clock"
        self.clock_idx = clock_idx

        self.write_helper(duplicate_datas, clock_idx)

    def duplicate_data_to_each_latch(self, data):
        datas = []
        for _ in range(len(self.latchs) + 1):
            datas.append(data)
        return datas

    def write_accumulator(self, data, clk):
        # clk is Acc Clock in page 357
        # page 347 have detailed circuit.
        self.clock_idx = len(self.clock_idx) * [0]
        self.clock_idx[7] = self.or_gate_for_acc_clk([clk, self.clock_idx[7]])
        assert (sum(self.clock_idx) == 1 and clk == 1) or ((sum(self.clock_idx) == 0 and clk == 0)), "FATAL: write_accumulator"
        self.write_helper(self.duplicate_data_to_each_latch(data), self.clock_idx)
        
    def write_helper(self, datas, clock_idx):
        print(f"datas: {datas}")
        for idx, clk in enumerate(clock_idx):
            if idx == 6: # select is [1, 1, 0]
                continue
            print(f"idx:{idx}, clk: {clk}")
            self.latchs[idx](datas[idx], clk)

    def read_hl(self, enable_hl):
        return self.tri_hl(self.latch_H.getQ() + self.latch_L.getQ(), enable_hl)

    def read_accumulator(self, enable=1):
        # TODO(PengChen): enable default is 1, so input_A of ALU can directly read accumulator?
        # enable is Acc Enable in page 357
        # page 347 have detailed circuit.
        self.enable_idx = len(self.enable_idx) * [0]
        self.enable_idx[7] = self.or_gate_for_acc_read([enable, self.enable_idx[7]])
        assert (sum(self.enable_idx) == 1 and enable == 1) or ((sum(self.enable_idx) == 0 and enable == 0)), "FATAL: read_accumulator"
        return self.read_helper(self.enable_idx)

    def read_register(self, select, enable):
        # select is SO2, SO1, SO0 in page 357
        assert len(select) == 3, f"selects must be 3 bits long"
        assert enable in [0, 1], "enable signal must be 0 or 1"
        
        enable_idx = self.decoder_enable(select, enable=enable)
        assert (sum(enable_idx) == 1 and enable == 1) or ((sum(enable_idx) == 0 and enable == 0)), "FATAL: Check Decoder_3_8 input/output"
        self.enable_idx = enable_idx
        return self.read_helper(enable_idx)
    
    def read_helper(self, enable_idx):
        list_of_buffer_outputs = []
        for idx, enab in enumerate(enable_idx):
            if idx == 6: # select is [1, 1, 0]
                continue
            print(f"idx: {idx}, data: {self.tris[idx](self.latchs[idx].getQ(), enab)}")
            list_of_buffer_outputs.append(self.tris[idx](self.latchs[idx].getQ(), enab))

        return self.data_bus(list_of_buffer_outputs)

class InstLatch:
    # circuit on page 347 and 353()
    def __init__(self, nbits = 8):
        self.nbits = nbits
        self.inst_latch1 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.inst_latch2 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        self.inst_latch3 = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)

        self.inst_latchs = {
            1:self.inst_latch1,
            2:self.inst_latch2,
            3:self.inst_latch3,
        }

        self.tri_2 = TriStateBuffer(self.nbits)
        self.tri_2_3 = TriStateBuffer(self.nbits * 2)
        
    def __call__(self, *args, **kwds):
        pass
        
    def write_latch1(self, data, clock_idx):
        self.write_helper(data, 1, clock_idx)

    def write_latch2(self, data, clock_idx):
        self.write_helper(data, 2, clock_idx)

    def write_latch3(self, data, clock_idx):
        self.write_helper(data, 3, clock_idx)

    def write_helper(self, data, latch_idx, clock_idx):
        self.inst_latchs[latch_idx](data, clock_idx)

    def read_latch1(self,):
        return self.inst_latch1.getQ()

    # send output to data bus
    def read_latch2(self, enable):
        # like ADI, latch2 must therefore be enabled on the data bus.
        return self.tri_2(self.inst_latch2.getQ(), enable)

    # send output to addr bus
    def read_latch2_3(self, enable_2_3):
        # like STA or LDA, latch2 and 3 must also be connected to the address bus through a tri-buffer.
        # the Intel 8080 uses "Little-Endian" byte order. example in page 377
        # Latch 3 is the High Byte (MSB), Latch 2 is the Low Byte (LSB)!
        return self.tri_2_3(self.inst_latch3.getQ() + self.inst_latch2.getQ(), enable_2_3)

class ProgramCounter:
    # circuit on page 348
    def __init__(self):
        self.addr_bits = 16
        self.latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.addr_bits)
        self.tri = TriStateBuffer(self.addr_bits)

    def SetMaxAddr(self):
        self.latch.SetMaxData()

    def Reset(self):
        # set the contents of the latch to all 0
        addrs = [0] * self.addr_bits
        self.latch.SetData(addrs)

    def SetAddr(self, addrs):
        self.latch.SetData(addrs)

    def readAddr(self, enable):
        return self.tri(self.latch.getQ(), enable)
        
    def __call__(self, addr, clk):
        self.latch(datas=addr, clk=clk)

class IncrementerDecrementer:
    def __init__(self):
        """ 
        The Incrementer / Decrementer (pages 350 – 351)
        refer: https://codehiddenlanguage.com/Chapter22/
        """
        self.addr_bits = 16
        self.xor_first_level = [XOR() for _ in range(self.addr_bits)]
        self.xor_second_level = [XOR() for _ in range(self.addr_bits)]
        self.and_gates = [AND() for _ in range(self.addr_bits)]
        self.v = 1

        self.latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.addr_bits)
        self.tri = TriStateBuffer(self.addr_bits)
        self.or_gate = OR()

    def readAddr(self, dec_enable, inc_enable):
        read_addrs = self.latch.getQ()
        
        v = self.v
        output_from_Inc_Dec = []
        for idx, addr in enumerate(reversed(read_addrs)):
            output_from_Inc_Dec.append(self.xor_second_level[idx]([addr, v]))
            v = self.and_gates[idx]([self.xor_first_level[idx]([dec_enable, addr]), v])

        # now LSB is idx 0, so we should reverse, let MSB is idx 0
        output_from_Inc_Dec = list(reversed(output_from_Inc_Dec))

        return self.tri(output_from_Inc_Dec, self.or_gate([dec_enable, inc_enable]))

    def __call__(self, addrs, clock):
        self.latch(addrs, clock)
        
    

# ------------------------- end ch22 ----------------------------------

class Counter4Bit:
    """A Ripple Counter that counts"""
    def __init__(self,):
        self.nbits = 4
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def SetMaxAddr(self):
        # 1. Assert the present wire (1) and let the hardware loop stabilize it!
        self.__call__(clk=0, clear_wire=0, present=1)
        
        # 2. De-assert the present wire (0) so the counter is ready to count again.
        self.__call__(clk=0, clear_wire=0, present=0)
        # for ff in self.flipflops:
            # ff([0, 0, 1, 0]) # D = 0, CLK = 0, PRE = 1, CLR = 0

    def Clear(self):
        # 1. Assert the Clear wire (1) and let the hardware loop stabilize it!
        self.__call__(clk=0, clear_wire=1, present=0)
        
        # 2. De-assert the Clear wire (0) so the counter is ready to count again.
        self.__call__(clk=0, clear_wire=0, present=0)
        # for ff in self.flipflops:
            # ff([0, 0, 0, 1]) # D = 0, CLK = 0, PRE = 0, CLR = 1

    def __call__(self, clk = 0, clear_wire = 0, present = 0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and clear_p370 wire (0)
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

        self.my_counter = Counter4Bit()
        self.decoder = Decoder_4_16()
        self.or_gate = OR()

        self.tri_buffer = TriStateBuffer(1)
        self.tri_buffer_2_in = TriStateBuffer(2)
        self.tri_buffer_1_in = TriStateBuffer(1)
        self.tri_buffer_3_in = TriStateBuffer(3)
        
        self.bus1_in_addr_bus_execute = DataBus(num_buffers=6, nbits=1)
        self.bus2_in_addr_bus_execute = DataBus(num_buffers=2, nbits=1)

        self.bus1_in_data_bus_execute = DataBus(num_buffers=3, nbits=1)

        self.tri_buffer_4_in = TriStateBuffer(4)

    def __call__(self, cycle_clk, pulse, reset, latch1):
        self.my_counter(cycle_clk)
        # print(f"self.my_counter: {self.my_counter.getQs()}")
        output_of_decoder = self.decoder(self.my_counter.getQs())
        # print(f"cycle_clk: {cycle_clk}, output_of_decoder: {output_of_decoder}")
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
        fetch_3_byte_p367 = self.or_gate_2_in([lda_p366, sta_p366])
        fetch_1_byte_invert_p367 = self.or_gate_2_in([fetch_2_byte_p367, fetch_3_byte_p367])
        fetch_1_byte_p367 = self.invert_gate([fetch_1_byte_invert_p367])
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # +++++ UPDATE START: FIXING 2-CYCLE EXECUTE FOR INX/DCX HL           +++++
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Previously: execute_2_cycle_p367 = self.or_gate_3_in([adi_data_p366, add_r_p367, add_M_p367])
        
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
        # print(f"tmp_exec_cycle_2_p370: {tmp_exec_cycle_2_p370}, execute_2_cycle_p367: {execute_2_cycle_p367}")
        tmp1_reset_p370 = self.or_gate_3_in([self.and_gate_2_in([output_of_decoder[4], fetch_1_byte_p367]), self.and_gate_2_in([output_of_decoder[6], fetch_2_byte_p367]), self.and_gate_2_in([output_of_decoder[8], fetch_3_byte_p367])])
        tmp2_reset_p370 = self.or_gate_2_in([self.and_gate_2_in([tmp_exec_cycle_2_p370, execute_1_cycle_p367]), self.and_gate_2_in([execute_2_cycle_p367, tmp1_reset_p370])])
        clear_p370 = self.or_gate_2_in([reset, tmp2_reset_p370])

        if clear_p370:
            """
            Instead of clearing the counter to 0000 on reset, 
            we must pre-set it to 1111 (the maximum value). 
            This way, when the very first rising edge of the clock hits, 
            the counter "rolls over" from 1111 to 0000. 
            This perfectly locks the CPU into Fetch 1 for the first cycle!
            """
            self.my_counter.SetMaxAddr() # clear_p370 0 and output[0] = 1 -> fetch cycle 1 next cycle
            # print(f"self.my_counter: {self.my_counter.getQs()}")
# page 372 first part
# --------------------------------------------------------------------------------------------------
        or_of_fetch_p372 = self.or_gate_3_in([fetch_cycle_1_out_p370, fetch_cycle_2_out_p370, fetch_cycle_3_out_p370])
        program_counter_enable_p372 = or_of_fetch_p372
        # here input and enable signal is same for tri-buffer
        # ATTENTION: maybe merge with other component can enable this.
        # tri_buffer is unnecessary, because enable and data is same, if data is 0, enable is 0 -> 0, if data is 1, enable is 1 -> 1
        # ram_data_out_enable_fetch_phrase_p372 = self.tri_buffer(or_of_fetch_p372, or_of_fetch_p372)[0]
        ram_data_out_enable_fetch_phrase_p372 = or_of_fetch_p372

        input_of_inc_dec_clk_p372 = self.and_gate_2_in([or_of_fetch_p372, pulse])
        # ATTENTION: maybe merge with other component can enable this.
        # inc_dec_clk_fetch_phrase_p372 = self.tri_buffer(input_of_inc_dec_clk_p372, input_of_inc_dec_clk_p372)[0]
        inc_dec_clk_fetch_phrase_p372 = input_of_inc_dec_clk_p372

        instru_latch_1_clk_p372 = self.and_gate_2_in([fetch_cycle_1_out_p370, pulse])
        instru_latch_2_clk_p372 = self.and_gate_2_in([fetch_cycle_2_out_p370, pulse])
        instru_latch_3_clk_p372 = self.and_gate_2_in([fetch_cycle_3_out_p370, pulse])
# page 372 second part
# --------------------------------------------------------------------------------------------------
        # ATTENTION: maybe merge with other component can enable this.
        # increment_enable_fetch_phrase_p372 = self.tri_buffer(pc_increment_p370, pc_increment_p370)[0]
        increment_enable_fetch_phrase_p372 = pc_increment_p370
        
        input_of_program_counter_clk_fetch_phrase_p372 = self.and_gate_2_in([pc_increment_p370, pulse])
        # ATTENTION: maybe merge with other component can enable this.
        # program_counter_clk_fetch_phrase_p372 = self.tri_buffer([input_of_program_counter_clk_fetch_phrase_p372, input_of_program_counter_clk_fetch_phrase_p372])[0]
        program_counter_clk_fetch_phrase_p372 = input_of_program_counter_clk_fetch_phrase_p372

# page 373 first part
# --------------------------------------------------------------------------------------------------
        execute_pulse_1_decode_phrase_p373 = self.and_gate_2_in([exec_cycle_1_out_p370, pulse])
        execute_pulse_2_decode_phrase_p373 = self.and_gate_2_in([exec_cycle_2_out_p370, pulse])
# page 373 second part
# --------------------------------------------------------------------------------------------------
        # this halt output will goes to the circuit with the oscillator
        halt_exec_phrase_p373 = self.and_gate_2_in([hlt_p367, execute_pulse_1_decode_phrase_p373])

# page 374
# --------------------------------------------------------------------------------------------------
# addr bus
        # ATTENTION: maybe merge with other component can enable this.
        hl_enable_addr_bus_exec_phrase_1_p374, inst_latch2_3_enable_addr_bus_exec_phrase_1_p374 = self.tri_buffer_2_in([self.bus1_in_addr_bus_execute([move_r_M_p367, 
                                                                        move_M_r_p367,
                                                                        mvi_M_data_p367,
                                                                        add_M_p367,
                                                                        inx_hl_p366,
                                                                        dcx_hl_p366])[0], self.bus2_in_addr_bus_execute([lda_p366,
                                                                                                              sta_p366])[0]], exec_cycle_1_out_p370)
        # ATTENTION: maybe merge with other component can enable this.
        inc_dec_clk_enable_addr_bus_exec_phrase_1_p374 = self.tri_buffer_1_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                           dcx_hl_p366])[0]], execute_pulse_1_decode_phrase_p373)[0]
        # ATTENTION: maybe merge with other component can enable this.
        hl_select_enable_addr_bus_exec_phrase_2_p374, increment_enable_addr_bus_exec_phrase_2_p374, dec_enable_addr_bus_exec_phrase_2_p374 = self.tri_buffer_3_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                           dcx_hl_p366])[0], inx_hl_p366, dcx_hl_p366], exec_cycle_2_out_p370)
        # ATTENTION: maybe merge with other component can enable this.
        hl_clk_addr_bus_exec_phrase_2_p374 = self.tri_buffer_1_in([self.bus2_in_addr_bus_execute([inx_hl_p366, 
                                                                      dcx_hl_p366])[0]], execute_pulse_2_decode_phrase_p373)[0]
        # print(f"exec_cycle_1_out_p370: {exec_cycle_1_out_p370}, execute_pulse_1_decode_phrase_p373: {execute_pulse_1_decode_phrase_p373}")
        # print(f"exec_cycle_2_out_p370: {exec_cycle_2_out_p370}, execute_pulse_2_decode_phrase_p373: {execute_pulse_2_decode_phrase_p373}")
# page 375
# --------------------------------------------------------------------------------------------------
        # ATTENTION: maybe merge with other component can enable this.
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
        # ATTENTION: maybe merge with other component can enable this.
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
        # ATTENTION: maybe merge with other component can enable this.
        alu_enable_data_bus_exec_phrase_2_p376 = self.tri_buffer_1_in([self.bus1_in_data_bus_execute([add_r_p367,
                                                                         add_M_p367,
                                                                         adi_data_p366,
                                                                         ])[0]], exec_cycle_2_out_p370)[0]
        # ATTENTION: maybe merge with other component can enable this.
        acc_clk_data_bus_exec_phrase_2_p376 = self.tri_buffer_1_in([self.bus1_in_data_bus_execute([add_r_p367,
                                                                       add_M_p367,
                                                                       adi_data_p366,
                                                                       ])[0]], execute_pulse_2_decode_phrase_p373)[0]

        # FIX: Combine signals that are triggered in multiple places using an OR gate!
        # (Apply this OR logic to any other wires you calculated twice)
        # this happen on insruct fetch and data in phrase 1
        final_ram_data_out_enable = self.or_gate_2_in([ram_data_out_enable_fetch_phrase_p372, ram_data_out_enable_data_bus_exec_phrase_1_p375])
        # happen on instruct fetch and addr bus exec phrase 1
        final_inc_dec_clk = self.or_gate_2_in([inc_dec_clk_fetch_phrase_p372, inc_dec_clk_enable_addr_bus_exec_phrase_1_p374])
        # happen on instruct fetch and addr bus exec phrase 2
        final_increment_enable = self.or_gate_2_in([increment_enable_fetch_phrase_p372, increment_enable_addr_bus_exec_phrase_2_p374])
        # happen on data bus phrase 1 for LDA and phrase 2 for ADD r, ADD M, and ADI Data
        final_acc_clk = self.or_gate_2_in([acc_clk_data_bus_exec_phrase_1_p375, acc_clk_data_bus_exec_phrase_2_p376])
        # l think maybe l will loss some enable or clock to get final result use or gate because circuit is so messy.
        # l try my best to double check. hope AI can help me further check whether have duplicate enable/ clock to merge get
        # final result.


        # Pack the Control Bus ribbon cable!
        control_bus = {
            "pc_enable": program_counter_enable_p372,
            "pc_clk": program_counter_clk_fetch_phrase_p372,
            "inc_dec_clk": final_inc_dec_clk,
            "inc_enable": final_increment_enable,
            "dec_enable": dec_enable_addr_bus_exec_phrase_2_p374,

            "inst_latch_1_clk": instru_latch_1_clk_p372,
            "inst_latch_2_clk": instru_latch_2_clk_p372,
            "inst_latch_3_clk": instru_latch_3_clk_p372,
            "inst_latch_2_enable": inst_latch2_enable_data_bus_exec_phrase_1_p375,
            "inst_latch2_3_enable": inst_latch2_3_enable_addr_bus_exec_phrase_1_p374,

            "ram_data_out_enable": final_ram_data_out_enable,
            "ram_write_enable": ram_write_enable_data_bus_exec_phrase_1_p375,

            "ra_enable": ra_enable_data_bus_exec_phrase_1_p375,
            "ra_clk": ra_clk_data_bus_exec_phrase_1_p375,
            "hl_enable": hl_enable_addr_bus_exec_phrase_1_p374,
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
        if reset == 1:
            self.edge_flipflop0.Reset() # clear_p370 
            self.edge_flipflop1.Reset()
            self.edge_flipflop2.Reset()
            return ;
        
        self.edge_flipflop0([self.edge_flipflop0.getQ_bar(), halt])

        clock = self.and_gate0([self.edge_flipflop0.getQ_bar(), clock])

        not_clk = self.invert1([clock])

        # while True:
        #     old_q1, old_q_bar1 = self.edge_flipflop1.getQ(), self.edge_flipflop1.getQ_bar()
        #     old_q2, old_q_bar2 = self.edge_flipflop2.getQ(), self.edge_flipflop2.getQ_bar()

        self.edge_flipflop1([self.edge_flipflop1.getQ_bar(), clock])
        self.edge_flipflop2([self.edge_flipflop1.getQ(), not_clk])
        clk_input_to_counter = self.edge_flipflop1.getQ()
        pulse = self.and_gate([self.edge_flipflop1.getQ_bar(), self.edge_flipflop2.getQ()])
        self.cycle_clock = clk_input_to_counter
        self.pulse = pulse
        # return [clk_input_to_counter, pulse]

        