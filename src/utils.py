# utils.py

# The Basic Gates
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
    """The NOT gate, It strictly takes 1 input."""
    def __init__(self):
        self.nin = 1

    def __call__(self, x):
        assert len(x) == self.nin, "Inverter takes exactly 1 input"
        # If 1, return 0. If 0, return 1.
        return 1 - x[0]

# Composing Complex Gates
class NAND:
    def __init__(self, nin=2):
        self.nin = nin
        # NAND is just an AND gate followed by an Inverter
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
    def __init__(self):
        self.nin = 2
        # The two components we need
        self.xor_gate = XOR()
        self.and_gate = AND(self.nin)

    def __call__(self, x):
        assert len(x) == self.nin, "Half Adder takes exactly 2 inputs"
        # Calculate Sum and Carry
        final_sum = self.xor_gate(x)
        final_carry = self.and_gate(x)

        # Return them as a tuple
        return final_carry, final_sum


class FullAdder:
    def __init__(self):
        self.nin = 3 # # Carry-In, A, and B

        # A full adder is literally just two half adders and an OR gate
        self.ha1 = HalfAdder()
        self.ha2 = HalfAdder()
        self.or_gate = OR(2)

    def __call__(self, x):
        # Carry-In, A, and B
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

        # Return them as a tuple
        return final_carry, final_sum

class nBit_Adder:
    def __init__(self, nbits):
        self.nbits = nbits # Carry_In, A, and B
        # Instantiate 'n' Full Adders
        self.fulladders = [FullAdder() for _ in range(self.nbits)]

    def __call__(self, x, y, last_carry_in=0):
        assert len(x) == self.nbits and len(y) == self.nbits, f"Inputs must be {self.nbits} bits long"
        final_sums = []
        final_carrys = [last_carry_in]

        # Iterate backwards: start from the far right and move left
        for idx in reversed(range(self.nbits)):
            carry_in = final_carrys[0]
            a = x[idx]
            b = y[idx]
            
            # Run the Full Adder for this column
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            
            final_carrys = [carry_out] + final_carrys
            final_sums = [sum_out] + final_sums
        # The final carry out of the MSB is still sitting at index 0
        return final_carrys[0], final_sums

# (PengChen:) update use two-complement for simulate real representation of hardware.
# def int_to_8bit_list(num):
#     """Converts an integer to a 8-bit list with MSB at index 0."""
#     # format(num, '08b') automatically converts to binary and pads to 8 bits
#     bin_str = format(num, '08b')
#     return [int(bit) for bit in bin_str]

# def int_to_16bit_list(num):
#     """Converts an integer to a 16-bit list with MSB at index 0."""
#     # format(num, '016b') automatically converts to binary and pads to 16 bits
#     bin_str = format(num, '016b')
#     return [int(bit) for bit in bin_str]

# def bit_list_to_int(bit_list):
#     """Converts a bit list (MSB at index 0) back to a standard integer."""
#     bin_str = "".join(str(bit) for bit in bit_list)
#     return int(bin_str, 2)


# include some basic data process function and nBit_Adder_with_two_complement
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

    # --- THE HARDWARE WAY ---
    
    # Step A: Pass the bits through our simulated Inverters
    my_inverter = Inverter()
    inverted_bits = [my_inverter([bit]) for bit in bit_list]

    # Step B: Wire up an adder to add 1
    adder = nBit_Adder(nbits)
    
    # Step B: Add 0, but set the Carry-In pin to 1
    zero_bits = [0 for _ in range(nbits)]
    overflow_carry, final_bits = adder(inverted_bits, zero_bits, last_carry_in=1)
    
    return final_bits
    
# Now you can easily create your 8-bit and 16-bit specific helpers:
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
        # Check the Most Significant Bit (Index 0)
        msb = bit_list[0]
        if msb == 1:
            # If MSB is 1, it's negative. We calculate its true negative value.
            # E.g., for 8 bits: val - 2^8 (val - 256)
            val = val - (1 << len(bit_list)) 
            
    return val

class nBit_Adder_with_two_complement:
    def __init__(self, nbits):
        self.nbits = nbits # Carry_In, A, and B
        # Instantiate 'n' Full Adders
        self.fulladders = [FullAdder() for _ in range(self.nbits)]

        # below gate use for overflow
        self.inverter = Inverter()
        # AND gate detects an overflow condition for negative numbers.
        # the sign bit of x and y inputs are both 1 and the sign
        # of the sum is 0.
        self.and_gate = AND(nin=3)
        # NOR gate detects an overflow condition for positive numbers.
        # the sign bit of x and y inputs are both 0 and the sign
        # of the sum is 1.
        self.nor_gate = NOR(nin=3)
        
        self.or_gate = OR(nin=2)
        
    def __call__(self, x, y, last_carry_in=0):
        assert len(x) == self.nbits and len(y) == self.nbits, f"Inputs must be {self.nbits} bits long"
        final_sums = []
        final_carrys = [last_carry_in]

        # Iterate backwards: start from the far right and move left
        for idx in reversed(range(self.nbits)):
            carry_in = final_carrys[0]
            a = x[idx]
            b = y[idx]
            
            # Run the Full Adder for this column
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            
            final_carrys = [carry_out] + final_carrys
            final_sums = [sum_out] + final_sums
        # The final carry out of the MSB is still sitting at index 0

        # we return third result that reflect overflow use two-complement
        invert_msb_of_final_sum = self.inverter([final_sums[0]])
        msb_of_x = x[0]
        msb_of_y = y[0]

        out_of_and_gate = self.and_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        out_of_nor_gate = self.nor_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        overflow = self.or_gate([out_of_and_gate, out_of_nor_gate])
        
        return overflow, final_carrys[0], final_sums

# from ch17 flip-flop

class Oscillator:
    """ A simple system clock that alternates between 0 and 1. """
    def __init__(self):
        self.state = 0

    def level(self):
        return self.state
        
    def tick(self):
        # Time moves forward one step!
        self.state = 1 - self.state
        return self.state

class RS_FlipFlop_V1:
    def __init__(self):
        self.nin = 2
        self.nor_gate1 = NOR()
        self.nor_gate2 = NOR()
        self.q = 0
        self.q_bar = 1 - self.q

    def getQ(self):
        return self.q

    def getQ_bar(self):
        return self.q_bar
    
    def __call__(self, x):
        assert len(x) == self.nin, "RS_FlipFlop takes exactly 2 inputs"
        r, s = x
        # 1. Q -> Q_bar -> Q
        # correct
        # self.q_bar = self.nor_gate2([self.q, s])
        # self.q = self.nor_gate1([self.q_bar, r])

        # 2. Q_bar -> Q -> Q_bar (- -> Q)
        # error
        # (PengChen:) because you evaluated Q first,
        # it didn't know that Q-bar was about to change!
        # Q evaluated using the "old" reality.
        # self.q = self.nor_gate1([self.q_bar, r])
        # self.q_bar = self.nor_gate2([self.q, s])

        # 3. iterate until stable
        while True:
            new_q = self.nor_gate1([r, self.q_bar])
            new_q_bar = self.nor_gate2([s, self.q])
            
            if new_q == self.q and new_q_bar == self.q_bar:
                break

            self.q = new_q
            self.q_bar = new_q_bar
        
        return self.q, self.q_bar

class RS_FlipFlop_V2:
    def __init__(self):
        # Edge-Triggered D-Type Flip-Flop with Clear and Preset (page 238)
        self.nin = 4 # r0, r1, s0, s1
        self.rs_flipflop = RS_FlipFlop_V1()
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

class Level_Triggered_D_Latch_V1:
    def __init__(self):
        self.nin = 2
        self.invert = Inverter()
        
        # Solder TWO physical AND gates to our board!
        self.and_gate1 = AND()
        self.and_gate2 = AND()
        
        self.rs_flipflop = RS_FlipFlop_V1()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]

        # Wire 1: Invert the Data
        not_data = self.invert([data])

        # Wire 2: The Reset pin (R) gets AND(NOT Data, Clock)
        r_wire = self.and_gate1([not_data, clock])

        # Wire 3: The Set pin (S) gets AND(Data, Clock)
        s_wire = self.and_gate2([data, clock])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar

class Level_Triggered_D_Latch_V2:
    def __init__(self):
        self.nin = 3 # data, clk, clr
        self.invert_data = Inverter()
        self.invert_clr = Inverter() # added to protect the set pin
        
        # Solder TWO physical AND gates to our board!
        self.and_gate_r = AND(2)
        self.and_gate_s = AND(3) # upgraded to 3 inputs
        self.or_gate = OR()
        
        self.rs_flipflop = RS_FlipFlop_V1()

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
            
        # Wire 1: The Reset pin (R) gets OR(Clr, AND(NOT Data, Clock))
        and_r = self.and_gate_r([not_data, clock])
        r_wire = self.or_gate([clr, and_r])

        # Wire 2: The Set pin (S) gets AND(Data, Clock, NOT Clr)
        s_wire = self.and_gate_s([data, clock, not_clr])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar

class nBitLevelTriggeredDLatch:
    def __init__(self, nbits):
        self.nbits = nbits
        # Solder 'n' D-Latches onto the board side-by-side
        self.level_d_latchs = [Level_Triggered_D_Latch_V2() for _ in range(self.nbits)]

    # We separate the data bus (a list) from the clock (a single bit)
    def __call__(self, datas, clk):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! No rippling required.
        for idx in range(self.nbits):
            # Fetch the latch for this specific bit, and pass its data and the shared clock
            q, q_bar = self.level_d_latchs[idx]([datas[idx], clk])
            qs.append(q)
            
        return qs

# A circuit that open like a door (Level-Triggered) is 
# called a Latch.
# A circuit that only triggers on the clock's
# transition (Edge-Triggered) is called
# a Flip-Flop.
class Edge_Triggered_D_Flip_Flop_V1:
    def __init__(self):
        self.nin = 2

        self.level_d_latchs_stage1 = Level_Triggered_D_Latch_V1()
        self.level_d_latchs_stage2 = Level_Triggered_D_Latch_V1()
        self.invert1 = Inverter()
        # self.q, self.q_bar = 0, 1

    def getQ(self):
        return self.level_d_latchs_stage2.getQ()

    def getQ_bar(self):
        return self.level_d_latchs_stage2.getQ_bar()
        
    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]

        # Wire 1: Invert the Clk
        not_clk = self.invert1([clock])

        # Wire 2: get Q and Q_bar from stage1
        q1, q_bar1 = self.level_d_latchs_stage1([data, not_clk])

        # Wire 3: get Q and Q_bar from stage2
        q2, q_bar2 = self.level_d_latchs_stage2([q1, clock])
        return q2, q_bar2

class Edge_Triggered_D_Flip_Flop_V2:
    def __init__(self):
        self.nin = 4
        self.rs_flipflop1 = RS_FlipFlop_V2()
        self.rs_flipflop2 = RS_FlipFlop_V2()
        self.rs_flipflop3 = RS_FlipFlop_V2()
        self.invert1 = Inverter()
        
    def getQ(self):
        return self.rs_flipflop3.getQ()

    def getQ_bar(self):
        return self.rs_flipflop3.getQ_bar()
        
    def __call__(self, x):
        assert len(x) in (self.nin, self.nin-2), f"Expected {self.nin} inputs"
        if len(x) == self.nin:
            data, clock, preset, clear = x
        else:
            data, clock = x
            preset, clear = 0, 0

        not_clk = self.invert1([clock])
        while True:
            # 1. Take a snapshot of the current reality
            old_q1, old_q_bar1 = self.rs_flipflop1.getQ(), self.rs_flipflop1.getQ_bar()
            old_q2, old_q_bar2 = self.rs_flipflop2.getQ(), self.rs_flipflop2.getQ_bar()
            old_q3, old_q_bar3 = self.rs_flipflop3.getQ(), self.rs_flipflop3.getQ_bar()

            # 2. Let the electrons flow through all the wires
            self.rs_flipflop1([self.rs_flipflop2.getQ_bar(), not_clk, data, preset])
            self.rs_flipflop2([clear, self.rs_flipflop1.getQ_bar(), preset, not_clk])
            q3, q_bar3 = self.rs_flipflop3([clear, self.rs_flipflop2.getQ_bar(), self.rs_flipflop1.getQ(), preset])    

            # 3. Did the electrons change anything? If no, the circuit is stable!
            if (old_q1 == self.rs_flipflop1.getQ() and old_q_bar1 == self.rs_flipflop1.getQ_bar() and 
                old_q2 == self.rs_flipflop2.getQ() and old_q_bar2 == self.rs_flipflop2.getQ_bar() and 
                old_q3 == self.rs_flipflop3.getQ() and old_q_bar3 == self.rs_flipflop3.getQ_bar()):
                break;
        
        return q3, q_bar3

class nBit_Edge_Triggered_Register:
    def __init__(self, nbits):
        self.nbits = nbits
        
        # Solder 'n' Edge-Triggered D-Flip-Flops onto the board side-by-side
        self.flip_flops = [Edge_Triggered_D_Flip_Flop_V2() for _ in range(self.nbits)]

    def __call__(self, datas, clk):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! All bits lock in at the exact same time.
        for idx in range(self.nbits):
            q, q_bar = self.flip_flops[idx]([datas[idx], clk])
            qs.append(q)
            
        return qs

class nBitAccumulatorV1:
    def __init__(self, nbits):
        self.nbits = nbits
        self.adder = nBit_Adder_with_two_complement(self.nbits)
        self.register = nBit_Edge_Triggered_Register(self.nbits)
        # At boot-up, the memory holds all zeros
        self.current_memory = [0 for _ in range(self.nbits)]

    def __call__(self, inputs_sequence):
        # We process a list of binary numbers, simulating time passing
        for data_in in inputs_sequence:
            assert len(data_in) == self.nbits , f"Data bus must be {self.nbits} bits long"
            # 1. The adder adds the incoming number to the CURRENT memory
            overflow, carry, sum_bits = self.adder(data_in, self.current_memory)

            # 2. Manually toggle the clock (Press the "Add" button)
            self.register(sum_bits, 0)
            # RISING EDGE: Button goes down (Clk=1). The register locks in the new sum
            self.current_memory = self.register(sum_bits, 1)
            # Button goes back up (Clk = 0)
            self.register(sum_bits, 0)
        # Return whatever the register is holding at the very end
        return self.current_memory

    def clear(self):
        """
        Clears the accumulator using pure hardward math.
        Adds the Two's complement of the current memory to itself.
        X + NOT(X) + 1 = 0
        """
        my_inverter = Inverter()

        inverted_memory = [my_inverter([bit]) for bit in self.current_memory]
        overflow, carry, sum_bits = self.adder(inverted_memory, self.current_memory, last_carry_in=1)

        # 2. Manually toggle the clock (Press the "Add" button)
        self.register(sum_bits, 0)
        # RISING EDGE: Button goes down (Clk=1). The register locks in the new sum
        self.current_memory = self.register(sum_bits, 1)
        # Button goes back up (Clk = 0)
        self.register(sum_bits, 0)        

class Frequency_Divider:
    def __init__(self):
        self.nin = 2
        # init self.state = 0
        self.oscillator = Oscillator() 
        self.flipflop = Edge_Triggered_D_Flip_Flop_V1()

        
    def __call__(self):
        clk = self.oscillator.level()
        self.oscillator.tick()
        data = self.flipflop.getQ_bar()

        q, q_bar = self.flipflop([data, clk])
        return q, q_bar

class nBitsRippleCounter:
    def __init__(self, nbits):
        self.nbits = nbits
        self.flipflops = [Edge_Triggered_D_Flip_Flop_V2() for _ in range(self.nbits)]

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

