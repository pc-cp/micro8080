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

class NBitAdderWithCarryOut:
    def __init__(self, nbits):
        self.nbits = nbits # Carry_In, A, and B
        # Instantiate 'n' Full Adders
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
            
            # Run the Full Adder for this column
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            
            final_carrys = carry_out
            final_sums = [sum_out] + final_sums
        # The final carry out of the MSB is still sitting at index 0
        return final_carrys, final_sums

# include some basic data process function and NBitAdderWithOverflow
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
    adder = NBitAdderWithCarryOut(nbits)
    
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

class NBitAdderWithOverflow:
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
        
        return overflow, final_sums
    
    def get_carry_out(self):
        return self.carry_out

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

class ResetSetFlipFlop:
    """
    The key limitation of the basic SR latch is its potential illegal condition **when both set and reset inputs are asserted simultaneously**. This combination drives the latch into an unstable state, creating ambiguity and possible race conditions.
    (R, S) from (0, 1) -> (1, 0) or (1, 0) -> (0, 1)
    https://www.wevolver.com/article/understanding-the-sr-latch-theory-design-truth-tables-and-practical-implementations?utm_source=chatgpt.com
    """
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

        # ------------------------------------
        # The while True: loop perfectly mimics this physical bouncing:
        # 1. Calculate the new reality: it evaluates what both gates want to output right now, based on the 
        #    the current wires.
        # 2. Check for stability: It asks, "did either of the outputs change?" 
        # 3. If no: The circuit has stabilized! The electrons are done bouncing. 
        # 4. If yes: The outputs did change. That means those new outputs need to flow back into the inputs
        #    of the opposite gates. We update our internal memory (self.q = new_q) and loop again.
        # ------------------------------------

        while True:
            old_q = self.q
            old_q_bar = self.q_bar
        
            self.q = self.nor_gate1([r, self.q_bar])
            self.q_bar = self.nor_gate2([s, self.q])
        
            if self.q == old_q and self.q_bar == old_q_bar:
                break
        return self.q, self.q_bar

class ResetSetFlipFlop4Input:
    def __init__(self):
        # Edge-Triggered D-Type Flip-Flop with Clear and Preset (page 238)
        self.nin = 4 # r0, r1, s0, s1
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

class LevelTriggeredDTypeFlipFlop:
    def __init__(self):
        self.nin = 2
        self.invert = Inverter()
        
        # Solder TWO physical AND gates to our board!
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

        # Wire 1: Invert the Data
        not_data = self.invert([data])

        # Wire 2: The Reset pin (R) gets AND(NOT Data, Clock)
        r_wire = self.and_gate1([not_data, clock])

        # Wire 3: The Set pin (S) gets AND(Data, Clock)
        s_wire = self.and_gate2([data, clock])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar

class LevelTriggeredDTypeFlipFlopWithClear:
    def __init__(self):
        self.nin = 3 # data, clk, clr
        self.invert_data = Inverter()
         # added to protect the set pin(this different between book in page 238)
        self.invert_clr = Inverter()
        
        # Solder TWO physical AND gates to our board!
        self.and_gate_r = AND(2)
        self.and_gate_s = AND(3) # upgraded to 3 inputs
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
            
        # Wire 1: The Reset pin (R) gets OR(Clr, AND(NOT Data, Clock))
        and_r = self.and_gate_r([not_data, clock])
        r_wire = self.or_gate([clr, and_r])

        # Wire 2: The Set pin (S) gets AND(Data, Clock, NOT Clr)
        s_wire = self.and_gate_s([data, clock, not_clr])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar

class NBitLevelTriggeredDTypeFlipFlopWithClear:
    def __init__(self, nbits):
        self.nbits = nbits
        # Solder 'n' D-Latches onto the board side-by-side
        self.level_d_latchs = [LevelTriggeredDTypeFlipFlopWithClear() for _ in range(self.nbits)]
    
    def getQ(self):
        return [latch.getQ() for latch in self.level_d_latchs]

    def getQ_bar(self):
        return [latch.getQ_bar() for latch in self.level_d_latchs]


    # We separate the data bus (a list) from the clock (a single bit)
    def __call__(self, datas, clk, clr=0):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! No rippling required.
        for idx in range(self.nbits):
            # Fetch the latch for this specific bit, and pass its data and the shared clock
            q, q_bar = self.level_d_latchs[idx]([datas[idx], clk, clr])
            qs.append(q)
            
        return qs

class EdgeTriggeredDTypeFlipFlop:
    def __init__(self):
        self.nin = 2

        self.level_d_latchs_stage1 = LevelTriggeredDTypeFlipFlop()
        self.level_d_latchs_stage2 = LevelTriggeredDTypeFlipFlop()
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

class EdgeTriggeredDTypeFlipFlopWithPresetAndClear:
    def __init__(self):
        self.nin = 4
        self.rs_flipflop1 = ResetSetFlipFlop4Input()
        self.rs_flipflop2 = ResetSetFlipFlop4Input()
        self.rs_flipflop3 = ResetSetFlipFlop4Input()
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

class NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear:
    def __init__(self, nbits):
        self.nbits = nbits
        
        # Solder 'n' Edge-Triggered D-Flip-Flops onto the board side-by-side
        self.flip_flops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]

    def SetMaxData(self):
        for ff in self.flip_flops:
            ff([0, 0, 1, 0]) # D = 0, CLK = 0, PRE = 1, CLR = 0
    
    def SetData(self, data):
        for idx, ff in enumerate(self.flip_flops):
            if data[idx] == 1:
                ff([0, 0, 1, 0]) # D = 0, CLK = 0, PRE = 1, CLR = 0
            else:
                ff([0, 0, 0, 1]) # D = 0, CLK = 0, PRE = 0, CLR = 1

    def getQ(self):
        return [ff.getQ() for ff in self.flip_flops]
    
    def getQ_bar(self):
        return [ff.getQ_bar() for ff in self.flip_flops]

    def __call__(self, datas, clk, preset=0, clr=0):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! All bits lock in at the exact same time.
        for idx in range(self.nbits):
            q, q_bar = self.flip_flops[idx]([datas[idx], clk, preset, clr])
            qs.append(q)
            
        return qs

class NBitsAccumulator:
    def __init__(self, nbits):
        self.nbits = nbits
        self.adder = NBitAdderWithOverflow(self.nbits)
        self.register = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nbits)
        # At boot-up, the memory holds all zeros
        self.current_memory = [0 for _ in range(self.nbits)]

    def get_register(self):
        return self.current_memory

    def __call__(self, inputs_sequence):
        # We process a list of binary numbers, simulating time passing
        for data_in in inputs_sequence:
            assert len(data_in) == self.nbits , f"Data bus must be {self.nbits} bits long"
            # 1. The adder adds the incoming number to the CURRENT memory
            overflow, sum_bits = self.adder(data_in, self.current_memory)

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
        overflow, sum_bits = self.adder(inverted_memory, self.current_memory, last_carry_in=1)

        # 2. Manually toggle the clock (Press the "Add" button)
        self.register(sum_bits, 0)
        # RISING EDGE: Button goes down (Clk=1). The register locks in the new sum
        self.current_memory = self.register(sum_bits, 1)
        # Button goes back up (Clk = 0)
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

    def __call__(self, input_A, input_B, F1_0, CY_In = 0):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F1_0) == self.nin_control, f"Input must be {self.nin_control} bits long"

        invert_of_f0 = self.invert_gate_of_f0([F1_0[1]])
        invert_flag = F1_0[0]
        CI_flag = self.or_gate_of_CI([self.and_gate_of_f0_CY_in([F1_0[1], CY_In]), self.and_gate_of_f0_f1([invert_of_f0, F1_0[0]])])
        
        outputs_from_complements_of_one = []
        for idx, xor_gate in enumerate(self.xor_gates_for_complements):
            outputs_from_complements_of_one.append(xor_gate([invert_flag, input_B[idx]]))
        operand_B = outputs_from_complements_of_one

        overflow, sum_bits = self.adder(input_A, operand_B, CI_flag)
        carry_out = self.adder.get_carry_out()

        return carry_out, sum_bits
        
            
    
class ALU:
    def __init__(self, nin_data = 8, nin_control_signal = 3):
        self.nin_data = nin_data
        self.nin_control = nin_control_signal

        self.add_and_subtract = Add_Subtract(self.nin_data, self.nin_control-1)
        self.logic = Logic(self.nin_data, self.nin_control)

        self.enable_add_or_sub = 0

        # just use 3 bits although use nin_data bits here
        self.flags_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)
        self.result_latch = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(self.nin_data)

        self.invert_of_f2 = Inverter()
        self.and_gate_of_f0_f1 = AND()
        self.or_gate_of_invert_of_f2_other = OR()
        self.and_gate_of_cy_out_other = AND()

        self.nor_gates_of_flags =  NOR(self.nin_data)

        self.tri_add_sub = TriStateBuffer(self.nin_data)
        self.data_bus = DataBus(num_buffers=2, nbits=self.nin_data)
        self.tri_result = TriStateBuffer(self.nin_data)

    def __call__(self, input_A, input_B, F2_0, clock, enable):
        assert len(input_A) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(input_B) == self.nin_data, f"Input must be {self.nin_data} bits long"
        assert len(F2_0) == self.nin_control, f"Input must be {self.nin_control} bits long"
        assert clock in [0, 1], f"clock signal must be 0 or 1"
        assert enable in [0, 1], f"enable signal must be 0 or 1"

        invert_of_f2 = self.invert_of_f2([F2_0[0]])
        self.enable_add_or_sub = invert_of_f2

        and_of_f1_f0 = self.and_gate_of_f0_f1([F2_0[1], F2_0[2]])
        or_of_and_invert_f2 = self.or_gate_of_invert_of_f2_other([invert_of_f2, and_of_f1_f0])

        # flags current have 3 bits is meaningful: 
        # flags[0]: sign flag, flags[1]: zero flag, flags[2]: carry flag
        flags = self.flags_latch.getQ()
        # Carry flag then circles back up to provide the CY In input of the Add/Sub module
        carry_out, sum_bits = self.add_and_subtract(input_A, input_B, F2_0[1:], flags[2])

        and_of_cy_out_or = self.and_gate_of_cy_out_other([carry_out, or_of_and_invert_f2])

        # new flags
        new_flags = [0] * self.nin_data
        new_flags[2] = and_of_cy_out_or

        result_of_logic = self.logic(input_A, input_B, F2_0)

        # this tick's output from add_and_subtract
        output_from_add_sub = self.tri_add_sub(sum_bits, self.enable_add_or_sub)
        new_flags[1] = self.nor_gates_of_flags(output_from_add_sub)
        new_flags[0] = output_from_add_sub[0] # MSB

        self.result_latch(self.data_bus([output_from_add_sub, result_of_logic]), clock)

        self.flags_latch(new_flags, clock)
        return self.tri_result(self.result_latch.getQ(), enable)
        # if self.enable_add_or_sub:
        #     new_flags[1] = self.nor_gates_of_flags(sum_bits)
        #     new_flags[0] = sum_bits[0] # MSB

        #     self.result_latch(sum_bits, clock)

        # else:
        #     new_flags[1] = self.nor_gates_of_flags(result_of_logic)
        #     # new_flags[0] = flags[0] # old sign flag
        #     new_flags[0] = result_of_logic # maybe we also check logic output?

        #     self.result_latch(result_of_logic, clock)

        # self.flags_latch(new_flags, clock)

        # output = [0] * self.nin_data
        # if enable:
        #     output = self.result_latch.getQ()

        # return output

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
            # This slices vertically! It grabs bit `i` from EVERY buffer in the list.
            # E.g., for wire 0, it grabs bit 0 from Reg A, bit 0 from Reg B, bit 0 from Reg C...
            bits_for_this_wire = [buf_out[i] for buf_out in list_of_buffer_outputs]
            
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
        self.or_gate_h_clk = OR()
        self.or_gate_l_clk = OR()
    
    def __call__(self, data, select, clock, hl_clock, hl_select, addr):
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
        
        duplicate_datas = self.duplicate_data_to_each_latch(data)
        # clock_idx[3] = self.or_gate_h_clk([clock_idx[3], HL_clock])
        # clock_idx[2] = self.or_gate_l_clk([clock_idx[2], HL_clock])
        
        if hl_select:
            duplicate_datas[4] = addr[:8]
            duplicate_datas[5] = addr[8:]
            clock_idx[4] = self.or_gate_h_clk([clock_idx[4], hl_clock])
            clock_idx[5] = self.or_gate_l_clk([clock_idx[5], hl_clock])
        self.clock_idx = clock_idx

        self.write_helper(duplicate_datas, clock_idx)

    def duplicate_data_to_each_latch(self, data):
        datas = []
        for _ in range(len(self.latchs) + 1):
            datas.append(data)
        return datas

    def write_accumulator(self, data, clk):
        # clk is Acc Clock in page 357
        self.clock_idx[7] = self.or_gate_for_acc_clk([clk, self.clock_idx[7]])
        assert sum(self.clock_idx) == 1
        self.write_helper(self.duplicate_data_to_each_latch(data), self.clock_idx)
        
    def write_helper(self, datas, clock_idx):
        for idx, clk in enumerate(clock_idx):
            if idx == 6: # select is [1, 1, 0]
                continue
            self.latchs[idx](datas[idx], clk)

    def read_hl(self, enable_hl):
        return self.tri_hl(self.latch_H.getQ() + self.latch_L.getQ(), enable_hl)

    def read_accumulator(self, enable):
        # enable is Acc Enable in page 357
        self.enable_idx[7] = self.or_gate_for_acc_read([enable, self.enable_idx[7]])
        assert sum(self.enable_idx) == 1
        return self.read_helper(self, self.enable_idx)

    def read_register(self, select, enable):
        # select is SO2, SO1, SO0 in page 357
        assert len(select) == 3, f"selects must be 3 bits long"
        assert enable in [0, 1], "enable signal must be 0 or 1"
        
        enable_idx = self.decoder_enable(select, enable=enable)
        assert (sum(enable_idx) == 1 and enable == 1) or ((sum(enable_idx) == 0 and enable == 0)), "FATAL: Check Decoder_3_8 input/output"
        self.enable_idx = enable_idx
        return self.read_helper(self, enable_idx)
    
    def read_helper(self, enable_idx):
        list_of_buffer_outputs = []
        for idx, enab in enumerate(enable_idx):
            if idx == 6: # select is [1, 1, 0]
                continue
            list_of_buffer_outputs.append(self.tris[idx](self.latchs[idx].getQ(), enab))

        return self.data_bus(list_of_buffer_outputs)

class InstLatch:
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

    def read_latch2(self, enable):
        return self.tri_2(self.inst_latch2.getQ(), enable)
    
    def read_latch2_3(self, enable_2_3):
        return self.tri_2(self.inst_latch2.getQ(), enable_2_3) + self.tri_3(self.inst_latch3.getQ(), enable_2_3)

class ProgramCounter:
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
        
    def __call__(self, data, clk):
        self.latch(datas=data, clk=clk)

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

    def __call__(self, addrs, dec_enable, inc_enable, clock):
        
        self.latch(addrs, clock)
        read_addrs = self.latch.getQ()
        
        v = self.v
        output_from_Inc_Dec = []
        for idx, addr in enumerate(reversed(read_addrs)):
            output_from_Inc_Dec.append(self.xor_second_level[idx]([addr, v]))
            v = self.and_gates[idx]([self.xor_first_level[idx]([dec_enable, addr]), v])

        # now LSB is idx 0, so we should reverse, let MSB is idx 0
        output_from_Inc_Dec = list(reversed(output_from_Inc_Dec))

        return self.tri(output_from_Inc_Dec, self.or_gate([dec_enable, inc_enable]))
    

# ------------------------- end ch22 ----------------------------------